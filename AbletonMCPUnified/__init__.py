"""AbletonMCPUnified Remote Script.

One Remote Script exposing a unified Ableton Live MCP command set plus a generic
Live Object Model escape hatch, over the same
``{"type": ..., "params": {...}}`` JSON-over-TCP protocol (default port 9877) and a
fire-and-forget UDP path for parameter sweeps (default port 9878).

Runs inside Live's embedded Python 3 (stdlib only).
"""
import json
import os
import queue
import socket
import threading
import time
import traceback

try:
    from _Framework.ControlSurface import ControlSurface
except ImportError:  # pragma: no cover - only outside Live
    class ControlSurface(object):
        def __init__(self, c_instance):
            pass

        def log_message(self, msg):
            pass

        def show_message(self, msg):
            pass

        def disconnect(self):
            pass

from .registry import COMMANDS, canonical_commands, modifying_commands
from .handlers import ALL_MIXINS

RS_VERSION = "unified-0.1.0"

DEFAULT_PORT = int(os.environ.get("ABLETON_MCP_PORT", "9877"))
UDP_PORT = int(os.environ.get("ABLETON_MCP_UDP_PORT", "9878"))
HOST = os.environ.get("ABLETON_MCP_HOST", "localhost")
CLIENT_TIMEOUT = float(os.environ.get("ABLETON_MCP_CLIENT_TIMEOUT", "300.0"))
MAX_CLIENTS = int(os.environ.get("ABLETON_MCP_MAX_CLIENTS", "10"))
MAX_BUFFER_SIZE = int(os.environ.get("ABLETON_MCP_MAX_BUFFER", "1048576"))
MAIN_THREAD_TIMEOUT = 10.0
MAX_MAIN_THREAD_TIMEOUT = 60.0
UDP_ALLOWLIST = frozenset(["set_device_parameter", "batch_set_device_parameters"])


def create_instance(c_instance):
    """Create and return the AbletonMCP script instance"""
    return AbletonMCP(c_instance)


class AbletonMCP(ControlSurface, *ALL_MIXINS):
    """AbletonMCPUnified Remote Script for Ableton Live"""

    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        self.log_message("AbletonMCPUnified %s initializing (%d commands)..." % (RS_VERSION, len(canonical_commands())))

        self.server = None
        self.client_threads = []
        self._threads_lock = threading.Lock()
        self.server_thread = None
        self.udp_server = None
        self.udp_thread = None
        self.running = False

        self._song = self.song()

        self.start_server()
        self.start_udp_server()

        self.log_message("AbletonMCPUnified initialized")
        self.show_message("AbletonMCPUnified: TCP %d / UDP %d" % (DEFAULT_PORT, UDP_PORT))

    # ------------------------------------------------------------------ lifecycle

    def disconnect(self):
        self.log_message("AbletonMCPUnified disconnecting...")
        self.running = False
        for sock in (self.server, self.udp_server):
            if sock:
                try:
                    sock.close()
                except (socket.error, OSError) as e:
                    self.log_message("Error closing socket: " + str(e))
        for t in (self.server_thread, self.udp_thread):
            if t and t.is_alive():
                t.join(1.0)
        with self._threads_lock:
            self.client_threads = []
        ControlSurface.disconnect(self)
        self.log_message("AbletonMCPUnified disconnected")

    # ------------------------------------------------------------------ TCP server

    def start_server(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind((HOST, DEFAULT_PORT))
            self.server.listen(5)
            self.running = True
            self.server_thread = threading.Thread(target=self._server_thread)
            self.server_thread.daemon = True
            self.server_thread.start()
            self.log_message("Server started on port " + str(DEFAULT_PORT))
        except Exception as e:
            self.log_message("Error starting server: " + str(e))
            self.show_message("AbletonMCPUnified: Error starting server - " + str(e))

    def _server_thread(self):
        try:
            self.log_message("Server thread started")
            self.server.settimeout(1.0)
            while self.running:
                try:
                    with self._threads_lock:
                        active_count = len([t for t in self.client_threads if t.is_alive()])
                        if active_count >= MAX_CLIENTS:
                            self.log_message("Max clients reached ({0}), waiting...".format(MAX_CLIENTS))
                            time.sleep(1.0)
                            continue
                    client, address = self.server.accept()
                    self.log_message("Connection accepted from " + str(address))
                    client_thread = threading.Thread(target=self._handle_client, args=(client,))
                    client_thread.daemon = True
                    client_thread.start()
                    with self._threads_lock:
                        self.client_threads.append(client_thread)
                        self.client_threads = [t for t in self.client_threads if t.is_alive()]
                except socket.timeout:
                    continue
                except (socket.error, OSError) as e:
                    if self.running:
                        self.log_message("Server accept error: " + str(e))
                    time.sleep(0.5)
                except Exception as e:
                    if self.running:
                        self.log_message("Unexpected server error: " + str(e))
                    time.sleep(0.5)
            self.log_message("Server thread stopped")
        except Exception as e:
            self.log_message("Server thread fatal error: " + str(e))
            self.log_message(traceback.format_exc())

    def _send_json(self, client, payload):
        client.sendall(json.dumps(payload).encode("utf-8"))

    def _handle_client(self, client):
        self.log_message("Client handler started")
        client.settimeout(CLIENT_TIMEOUT)
        buffer = b""
        try:
            while self.running:
                try:
                    data = client.recv(8192)
                    if not data:
                        self.log_message("Client disconnected")
                        break
                    buffer += data
                    if len(buffer) > MAX_BUFFER_SIZE:
                        self.log_message("Buffer overflow - client sent too much data")
                        try:
                            self._send_json(client, {"status": "error", "message": "Request exceeds %d bytes" % MAX_BUFFER_SIZE})
                        except (socket.error, OSError):
                            pass
                        break
                    stripped = buffer.rstrip()
                    # Only attempt a parse when the buffer could plausibly be complete JSON.
                    if not (stripped.endswith(b"}") or stripped.endswith(b"]")):
                        continue
                    try:
                        command = json.loads(buffer.decode("utf-8"))
                    except (ValueError, UnicodeDecodeError):
                        continue  # incomplete; wait for more
                    buffer = b""
                    self.log_message("Received command: " + str(command.get("type", "unknown")))
                    response = self._process_command(command)
                    self._send_json(client, response)
                except socket.timeout:
                    raise
                except Exception as e:
                    self.log_message("Error handling client data: " + str(e))
                    self.log_message(traceback.format_exc())
                    try:
                        self._send_json(client, {"status": "error", "message": str(e)})
                    except (socket.error, OSError) as send_err:
                        self.log_message("Failed to send error response: " + str(send_err))
                        break
                    if not isinstance(e, ValueError):
                        break
        except socket.timeout:
            self.log_message("Client timed out after {0} seconds".format(CLIENT_TIMEOUT))
        except Exception as e:
            self.log_message("Error in client handler: " + str(e))
            self.log_message(traceback.format_exc())
        finally:
            try:
                client.close()
            except (socket.error, OSError) as e:
                self.log_message("Error closing client socket: " + str(e))
            self.log_message("Client handler stopped")

    # ------------------------------------------------------------------ UDP server

    def start_udp_server(self):
        """Bind the fire-and-forget UDP listener. Failure here must not affect TCP."""
        try:
            self.udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.udp_server.bind((HOST, UDP_PORT))
            self.udp_server.settimeout(1.0)
            self.udp_thread = threading.Thread(target=self._udp_server_loop)
            self.udp_thread.daemon = True
            self.udp_thread.start()
            self.log_message("UDP server started on port " + str(UDP_PORT))
        except Exception as e:
            self.udp_server = None
            self.log_message("UDP server unavailable: " + str(e))

    def _udp_server_loop(self):
        while self.running and self.udp_server is not None:
            try:
                data, _addr = self.udp_server.recvfrom(65535)
            except socket.timeout:
                continue
            except (socket.error, OSError) as e:
                if self.running:
                    self.log_message("UDP socket error: " + str(e))
                break
            try:
                command = json.loads(data.decode("utf-8"))
                self._process_udp_command(command)
            except Exception as e:
                self.log_message("UDP: error processing datagram: " + str(e))
        self.log_message("UDP server thread stopped")

    def _process_udp_command(self, command):
        command_type = command.get("type", "")
        params = command.get("params", {}) or {}
        spec = COMMANDS.get(command_type)
        if spec is None or spec.name not in UDP_ALLOWLIST:
            self.log_message("UDP: command not allowed: " + str(command_type))
            return
        handler = getattr(self, spec.method)

        def task():
            try:
                handler(params)
            except Exception as e:
                self.log_message("UDP: error in %s: %s" % (command_type, e))

        self._schedule(task)

    # ------------------------------------------------------------------ dispatch

    def _schedule(self, task):
        """Run ``task`` on Live's main thread (or inline when already there / unavailable)."""
        schedule = getattr(self, "schedule_message", None)
        if schedule is None:
            task()
            return
        try:
            schedule(0, task)
        except AssertionError:
            task()

    def _execute(self, handler, params, command_name=""):
        """Run a handler and echo indices + names. Names are captured after the handler (so renames
        show the new name) except for delete-style commands, where the pre-run names are kept."""
        before = self._capture_names(params, command_name)
        result = handler(params)
        if command_name.startswith(("delete_", "remove_", "ungroup_")):
            names = before
        else:
            names = dict(before)
            names.update(self._capture_names(params, command_name))
        return self._finalize_result(params, result, names)

    def _run_on_main_thread(self, handler, params, timeout=MAIN_THREAD_TIMEOUT, command_name=""):
        response_queue = queue.Queue(maxsize=1)

        def main_thread_task():
            try:
                response_queue.put({"status": "success", "result": self._execute(handler, params, command_name)})
            except Exception as e:
                self.log_message("Error in main thread task: " + str(e))
                self.log_message(traceback.format_exc())
                response_queue.put({"status": "error", "message": str(e)})

        self._schedule(main_thread_task)
        try:
            return response_queue.get(timeout=timeout)
        except queue.Empty:
            return {"status": "error", "message": "Timeout waiting for operation to complete"}

    def _process_command(self, command):
        """Look the command up in the registry and run it (main thread when modifying)."""
        command_type = command.get("type", "")
        params = command.get("params", {}) or {}
        spec = COMMANDS.get(command_type)
        if spec is None:
            return {"status": "error",
                    "message": "Unknown command: %s. Use list_commands to see the %d available commands."
                               % (command_type, len(canonical_commands()))}
        timeout = MAIN_THREAD_TIMEOUT
        if "_timeout" in params:
            try:
                timeout = max(1.0, min(MAX_MAIN_THREAD_TIMEOUT, float(params.pop("_timeout"))))
            except (TypeError, ValueError):
                params.pop("_timeout", None)
        try:
            handler = getattr(self, spec.method)
            if spec.modifying:
                return self._run_on_main_thread(handler, params, timeout, spec.name)
            return {"status": "success", "result": self._execute(handler, params, spec.name)}
        except Exception as e:
            self.log_message("Error processing command: " + str(e))
            self.log_message(traceback.format_exc())
            return {"status": "error", "message": str(e)}

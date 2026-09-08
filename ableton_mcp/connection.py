"""TCP connection to the Remote Script plus a UDP sender.

The set of state-modifying commands is derived from ``spec.MODIFYING_COMMANDS`` so the
server never maintains a second hand-written list.
"""
from __future__ import annotations

import json
import logging
import os
import socket
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger("AbletonMCPUnified")

MCP_RECV_TIMEOUT = float(os.environ.get("MCP_RECV_TIMEOUT", "15.0"))
MCP_MODIFYING_CMD_TIMEOUT = float(os.environ.get("MCP_MODIFYING_CMD_TIMEOUT", "15.0"))
MCP_READ_CMD_TIMEOUT = float(os.environ.get("MCP_READ_CMD_TIMEOUT", "10.0"))
MCP_HEALTH_CHECK_TIMEOUT = float(os.environ.get("MCP_HEALTH_CHECK_TIMEOUT", "2.0"))
MCP_COMMAND_DELAY = float(os.environ.get("MCP_COMMAND_DELAY", "0.05"))
MCP_RETRY_DELAY = float(os.environ.get("MCP_RETRY_DELAY", "1.0"))
MCP_MAX_CONNECT_ATTEMPTS = int(os.environ.get("MCP_MAX_CONNECT_ATTEMPTS", "3"))
ABLETON_HOST = os.environ.get("ABLETON_HOST", "localhost")
ABLETON_PORT = int(os.environ.get("ABLETON_PORT", "9877"))
ABLETON_UDP_PORT = int(os.environ.get("ABLETON_UDP_PORT", "9878"))


def _modifying_commands() -> frozenset:
    from .spec import MODIFYING_COMMANDS
    return MODIFYING_COMMANDS


@dataclass
class AbletonConnection:
    host: str
    port: int
    sock: Optional[socket.socket] = field(default=None)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def connect(self) -> bool:
        if self.sock:
            return True
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            logger.info(f"Connected to Ableton at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Ableton: {e}")
            self.sock = None
            return False

    def disconnect(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception as e:
                logger.error(f"Error disconnecting from Ableton: {e}")
            finally:
                self.sock = None

    def receive_full_response(self, sock, buffer_size=8192) -> bytes:
        """Receive until the accumulated bytes parse as JSON (only tried when plausible)."""
        chunks = []
        sock.settimeout(MCP_RECV_TIMEOUT)
        try:
            while True:
                try:
                    chunk = sock.recv(buffer_size)
                    if not chunk:
                        if not chunks:
                            self.disconnect()
                            raise Exception("Connection closed before receiving any data")
                        break
                    chunks.append(chunk)
                    if not chunk.rstrip().endswith((b"}", b"]")):
                        continue
                    data = b"".join(chunks)
                    try:
                        json.loads(data.decode("utf-8"))
                        return data
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        continue
                except socket.timeout:
                    logger.warning("Socket timeout during chunked receive")
                    if not chunks:
                        self.disconnect()
                    break
                except (ConnectionError, BrokenPipeError, ConnectionResetError):
                    self.disconnect()
                    raise
        except (ConnectionError, BrokenPipeError, ConnectionResetError):
            raise
        except Exception as e:
            logger.error(f"Error during receive: {e}")
            self.disconnect()
            raise
        if chunks:
            data = b"".join(chunks)
            try:
                json.loads(data.decode("utf-8"))
                return data
            except json.JSONDecodeError:
                self.disconnect()
                raise Exception("Incomplete JSON response received")
        self.disconnect()
        raise Exception("No data received")

    def send_command(self, command_type: str, params: Dict[str, Any] = None,
                     timeout: Optional[float] = None) -> Dict[str, Any]:
        """Send a command and return its ``result`` (raises on ``status: error``)."""
        with self.lock:
            if not self.sock and not self.connect():
                raise ConnectionError("Not connected to Ableton")
            command = {"type": command_type, "params": params or {}}
            is_modifying = command_type in _modifying_commands()
            try:
                logger.info(f"Sending command: {command_type} with params: {params}")
                self.sock.sendall(json.dumps(command).encode("utf-8"))
                if is_modifying:
                    time.sleep(MCP_COMMAND_DELAY)
                if timeout is None:
                    timeout = MCP_MODIFYING_CMD_TIMEOUT if is_modifying else MCP_READ_CMD_TIMEOUT
                self.sock.settimeout(timeout)
                response_data = self.receive_full_response(self.sock)
                response = json.loads(response_data.decode("utf-8"))
                if response.get("status") == "error":
                    raise Exception(response.get("message", "Unknown error from Ableton"))
                if is_modifying:
                    time.sleep(MCP_COMMAND_DELAY)
                return response.get("result", {})
            except socket.timeout:
                logger.error("Socket timeout while waiting for response from Ableton")
                self.disconnect()
                raise Exception("Timeout waiting for Ableton response")
            except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
                self.disconnect()
                raise Exception(f"Connection to Ableton lost: {e}")
            except json.JSONDecodeError as e:
                self.disconnect()
                raise Exception(f"Invalid response from Ableton: {e}")
            except Exception as e:
                logger.error(f"Error communicating with Ableton: {e}")
                self.disconnect()
                raise Exception(f"Communication error with Ableton: {e}")


class UdpSender:
    """Fire-and-forget datagrams to the Remote Script's UDP listener."""

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        self.host = host or ABLETON_HOST
        self.port = port or ABLETON_UDP_PORT
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, command_type: str, params: Dict[str, Any]) -> int:
        payload = json.dumps({"type": command_type, "params": params}).encode("utf-8")
        if len(payload) > 65000:
            raise ValueError("UDP payload too large ({0} bytes); use reliable=True".format(len(payload)))
        return self.sock.sendto(payload, (self.host, self.port))


_ableton_connection: Optional[AbletonConnection] = None
_connection_lock = threading.Lock()
_udp_sender: Optional[UdpSender] = None


def get_udp_sender() -> UdpSender:
    global _udp_sender
    if _udp_sender is None:
        _udp_sender = UdpSender()
    return _udp_sender


def _probe(conn: AbletonConnection) -> None:
    """Health-check the Remote Script; tolerate legacy scripts that lack a health_check command."""
    try:
        conn.send_command("health_check", timeout=MCP_HEALTH_CHECK_TIMEOUT)
    except Exception as e:
        if "Unknown command" not in str(e):
            raise
        logger.warning("Remote Script has no health_check (legacy AbletonMCP script active?); falling back to get_session_info")
        conn.send_command("get_session_info", timeout=MCP_HEALTH_CHECK_TIMEOUT)


def get_ableton_connection() -> AbletonConnection:
    """Get or create a persistent, health-checked connection (thread-safe)."""
    global _ableton_connection
    with _connection_lock:
        if _ableton_connection is not None:
            try:
                _probe(_ableton_connection)
                return _ableton_connection
            except Exception as e:
                logger.warning(f"Existing connection is no longer valid: {e}")
                try:
                    _ableton_connection.disconnect()
                except Exception:
                    pass
                _ableton_connection = None
        for attempt in range(1, MCP_MAX_CONNECT_ATTEMPTS + 1):
            try:
                logger.info(f"Connecting to Ableton (attempt {attempt}/{MCP_MAX_CONNECT_ATTEMPTS})...")
                conn = AbletonConnection(host=ABLETON_HOST, port=ABLETON_PORT)
                if conn.connect():
                    _probe(conn)
                    _ableton_connection = conn
                    return conn
            except Exception as e:
                logger.error(f"Connection attempt {attempt} failed: {e}")
            if attempt < MCP_MAX_CONNECT_ATTEMPTS:
                time.sleep(MCP_RETRY_DELAY)
        raise Exception("Could not connect to Ableton. Make sure the AbletonMCPUnified Remote Script is running.")


def reset_connection():
    global _ableton_connection
    with _connection_lock:
        if _ableton_connection:
            _ableton_connection.disconnect()
        _ableton_connection = None

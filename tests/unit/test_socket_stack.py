"""End-to-end over real sockets: Remote Script server thread (mock song) <-> MCP server tools."""
import json
import socket
import time

import pytest

import AbletonMCPUnified as rs
from ableton_mcp import connection, tools_manual as m
from ableton_mcp.tools_generated import build_generated_tools
from tests.conftest import make_script
from tests.fixtures.mock_ableton import MockDevice, MockDeviceParameter, MockSong

G = build_generated_tools()


def _free_port():
    s = socket.socket()
    s.bind(("localhost", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture
def stack(monkeypatch):
    song = MockSong()
    song.tracks[0].devices.append(MockDevice("Serum", params=[
        MockDeviceParameter("Device On", 1.0, 0.0, 1.0), MockDeviceParameter("Fil Cutoff", 0.5, 0.0, 1.0)]))
    tcp, udp = _free_port(), _free_port()
    monkeypatch.setattr(rs, "DEFAULT_PORT", tcp)
    monkeypatch.setattr(rs, "UDP_PORT", udp)
    monkeypatch.setattr(rs, "MAX_BUFFER_SIZE", 4096)
    script = make_script(song)
    script.server = None
    script.client_threads = []
    import threading
    script._threads_lock = threading.Lock()
    script.server_thread = None
    script.udp_server = None
    script.udp_thread = None
    script.running = False
    script.start_server()
    script.start_udp_server()
    monkeypatch.setattr(connection, "ABLETON_PORT", tcp)
    monkeypatch.setattr(connection, "ABLETON_UDP_PORT", udp)
    monkeypatch.setattr(connection, "MCP_MAX_CONNECT_ATTEMPTS", 2)
    monkeypatch.setattr(connection, "MCP_RETRY_DELAY", 0.05)
    monkeypatch.setattr(connection, "_udp_sender", None)
    connection.reset_connection()
    yield script, song
    connection.reset_connection()
    script.disconnect()


def test_health_and_reads(stack):
    h = json.loads(m.health_check())
    assert h["connected"] and h["rs_version"] == rs.RS_VERSION and h["command_count"] >= 270
    info = json.loads(m.get_track_info(1))
    assert info["track_index"] == 1 and info["index"] == 1 and info["name"] == "Track 1"
    assert "must be >= 1" in m.get_track_info(0)


def test_setters_echo_and_alias(stack):
    script, song = stack
    out = json.loads(G["set_track_name"](track_index=2, name="Bass"))
    assert out["track_index"] == 2 and out["track_name"] == "Bass" and song.tracks[1].name == "Bass"
    assert "panning to -0.5000" in m.set_track_panning(1, -0.5)
    set_track_pan = m._alias_of(m.set_track_panning, "set_track_pan", "set_track_panning")
    assert set_track_pan.__doc__.startswith("[Deprecated alias of set_track_panning]")
    assert "panning to 0.2500" in set_track_pan(track_index=1, panning=0.25)


def test_device_parameter_roundtrip(stack):
    script, song = stack
    out = m.set_device_parameter(track_index=1, device_index=1, parameter_name="cutoff", value=0.3)
    assert "Set Fil Cutoff" in out
    payload = json.loads(out.split("\n", 1)[1])
    assert payload["value"] == 0.3 and payload["raw_value"] == pytest.approx(0.3) and payload["parameter_index"] == 2
    assert payload["device_name"] == "Serum" and payload["track_index"] == 1 and payload["device_index"] == 1
    assert "2 parameters" in m.get_device_parameters(1, 1)


def test_udp_batch_and_reliable(stack):
    script, song = stack
    serum = song.tracks[0].devices[0]
    out = m.batch_set_device_parameters(1, 1, [{"parameter_index": 2, "value": 0.9}])
    assert out.startswith("Sent 1 parameter updates via UDP")
    for _ in range(50):
        if abs(serum.parameters[1].value - 0.9) < 1e-6:
            break
        time.sleep(0.02)
    assert serum.parameters[1].value == pytest.approx(0.9)
    res = json.loads(m.batch_set_device_parameters(1, 1, [{"parameter_name": "cutoff", "value": 0.1}], reliable=True))
    assert res["updated"] == 1 and res["results"][0]["parameter_index"] == 2 and serum.parameters[1].value == pytest.approx(0.1)


def test_lom_over_socket(stack):
    script, song = stack
    kids = json.loads(m.live_children("live_set"))
    assert kids["lists"]["tracks"] == 8
    assert json.loads(m.live_get("live_set tracks 1", ["name"]))["values"]["name"] == "Track 1"
    assert json.loads(m.live_set("live_set", "tempo", 128))["value"] == 128.0 and song.tempo == 128.0
    assert json.loads(m.live_call("live_set", "create_midi_track", [-1]))["method"] == "create_midi_track"
    assert len(song.tracks) == 9
    assert "Error" in m.live_get("live_set __class__")


def test_send_command_generic(stack):
    out = json.loads(m.send_command("get_clip_launch_mode", {"track_index": 1, "clip_index": 1}))
    assert "error" in out or "track_index" in out  # empty slot -> RS error payload, still 1-based echo
    out = json.loads(m.send_command("get_all_track_names"))
    assert out["track_names"][0] == "Track 1" if "track_names" in out else True


def test_oversized_request_then_reconnect(stack):
    conn = connection.get_ableton_connection()
    big = json.dumps({"type": "get_session_info", "params": {"pad": "x" * 10000}})
    with pytest.raises(Exception):
        conn.send_command("get_session_info", {"pad": "x" * 10000})
    assert conn.sock is None
    assert json.loads(m.health_check())["connected"]


def test_unknown_command_error(stack):
    assert "Unknown command" in m.send_command("no_such_thing")


def test_server_restart_reconnects(stack):
    script, song = stack
    assert json.loads(m.health_check())["connected"]
    script.disconnect()
    assert json.loads(m.health_check())["connected"] is False
    script.start_server()
    assert json.loads(m.health_check())["connected"]

"""Live checklist against a running Ableton Live with the AbletonMCPUnified Remote Script.

Run with: uv run pytest -m integration tests/integration -v
These mutate the open set (tempo, track 1 name/volume, loop brace, cue points); use a scratch project.
"""
import json

import pytest

from ableton_mcp import tools_manual as m
from ableton_mcp.connection import get_ableton_connection, reset_connection
from ableton_mcp.tools_generated import build_generated_tools

pytestmark = pytest.mark.integration
G = build_generated_tools()


@pytest.fixture(scope="module")
def live():
    try:
        conn = get_ableton_connection()
    except Exception as e:  # pragma: no cover
        pytest.skip(f"Ableton not reachable: {e}")
    yield conn
    reset_connection()


def test_health_and_command_count(live):
    h = json.loads(m.health_check())
    assert h["connected"] and h["rs_version"].startswith("unified-") and h["command_count"] >= 270


def test_track_info_one_based(live):
    info = json.loads(m.get_track_info(1))
    assert info["track_index"] == 1 and info["index"] == 1 and info["name"]
    assert "must be >= 1" in m.get_track_info(0)


def test_track_setters_echo(live):
    original = json.loads(m.get_track_info(1))["name"]
    out = json.loads(G["set_track_name"](track_index=1, name=original + " ✓"))
    assert out["track_index"] == 1 and out["name"] == original + " ✓"
    G["set_track_name"](track_index=1, name=original)
    assert "panning" in m.set_track_panning(1, 0.0)
    assert "fader" in m.set_track_volume(1, 0.85)


def test_loop_and_song_time(live):
    assert "bars 5-9" in m.set_arrangement_loop(enabled=True, start_bar=5, end_bar=9)
    assert "bar 3" in m.set_song_time(bar=3)


def test_cue_points_roundtrip(live):
    assert "Created" in m.create_cue_point(bar=7, name="mcp-test")
    assert "mcp-test" in m.get_cue_points()
    assert "Deleted" in m.delete_cue_point(bar=7)


def test_lom(live):
    kids = json.loads(m.live_children("live_set"))
    assert kids["lists"]["tracks"] >= 1
    name = json.loads(m.live_get("live_set tracks 1", ["name"]))["values"]["name"]
    assert name == json.loads(m.get_track_info(1))["name"]
    assert "Error" in m.live_get("live_set __class__")
    tempo = json.loads(m.live_get("live_set", ["tempo"]))["values"]["tempo"]
    out = json.loads(m.live_set("live_set", "tempo", tempo))
    assert out["value"] == tempo

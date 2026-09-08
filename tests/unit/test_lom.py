"""Generic Live Object Model tools: safe walker (Remote Script) and 1-based path rewriting (server)."""
import pytest

from AbletonMCPUnified import lom
from ableton_mcp.lom import path_to_one_based, path_to_zero_based, rewrite_paths


class TestServerPaths:
    def test_zero_based(self):
        assert path_to_zero_based("live_set tracks 1 devices 2 parameters 3") == "live_set tracks 0 devices 1 parameters 2"

    def test_rejects_zero(self):
        with pytest.raises(ValueError, match="1-based"):
            path_to_zero_based("live_set tracks 0")

    def test_rejects_unknown_root(self):
        with pytest.raises(ValueError):
            path_to_zero_based("song tracks 1")

    def test_one_based_roundtrip(self):
        assert path_to_one_based("live_set tracks 0 devices 1") == "live_set tracks 1 devices 2"

    def test_rewrite_paths_recursive(self):
        out = rewrite_paths({"path": "live_set tracks 0", "value": [{"path": "live_set tracks 0 devices 1"}]})
        assert out["path"] == "live_set tracks 1"
        assert out["value"][0]["path"] == "live_set tracks 1 devices 2"


class TestWalker:
    def test_resolve_and_get(self, song):
        obj = lom.resolve_path({"live_set": song}, "live_set tracks 1")
        assert obj is song.tracks[1]
        assert lom.get_props(obj, ["name"])["name"] == "Track 2"

    def test_rejects_dunder(self, song):
        with pytest.raises(ValueError):
            lom.resolve_path({"live_set": song}, "live_set __class__")
        with pytest.raises(ValueError):
            lom.get_props(song, ["__dict__"])

    def test_rejects_private(self, song):
        with pytest.raises(ValueError):
            lom.resolve_path({"live_set": song}, "live_set _tempo")

    def test_index_out_of_range(self, song):
        with pytest.raises(IndexError):
            lom.resolve_path({"live_set": song}, "live_set tracks 99")

    def test_serialize_caps_lists(self):
        out = lom.serialize(list(range(1000)), "p")
        assert len(out) == lom.MAX_LIST + 1 and out[-1]["truncated"]

    def test_serialize_object(self, song):
        out = lom.serialize(song.tracks[0], "live_set tracks 0")
        assert out["type"] == "MockTrack" and out["name"] == "Track 1" and out["path"] == "live_set tracks 0"

    def test_children(self, song):
        out = lom.children(song, "live_set")
        assert "tempo" in out["properties"] and "tracks" in out["lists"] and "start_playing" in out["methods"]
        assert "master_track" in out["objects"]

    def test_coerce(self):
        assert lom.coerce_like(120.0, 128) == 128.0
        assert lom.coerce_like(False, 1) is True
        assert lom.coerce_like(3, "4") == 4
        with pytest.raises(ValueError):
            lom.coerce_like(object(), 1)

    def test_call_args(self):
        assert lom.json_to_call_args([-1, "a", [1, [2, 3]]]) == [-1, "a", (1, (2, 3))]
        with pytest.raises(ValueError):
            lom.json_to_call_args([object()])

    def test_call_args_path_ref(self):
        marker = object()
        out = lom.json_to_call_args([1, {"$path": "live_set tracks 1"}], lambda p: marker if p == "live_set tracks 1" else None)
        assert out == [1, marker]
        with pytest.raises(ValueError):
            lom.json_to_call_args([{"$path": "live_set"}])  # no resolver
        with pytest.raises(ValueError):
            lom.json_to_call_args([{"$path": "live_set", "extra": 1}], lambda p: None)


class TestDispatch:
    def test_live_get(self, dispatch):
        r = dispatch("live_get", path="live_set tracks 0", props=["name", "mute"])
        assert r["status"] == "success" and r["result"]["values"] == {"name": "Track 1", "mute": False}

    def test_live_children(self, dispatch):
        r = dispatch("live_children", path="live_set")
        assert r["result"]["lists"]["tracks"] == 8

    def test_live_set(self, dispatch, song):
        r = dispatch("live_set", path="live_set", prop="tempo", value=128)
        assert r["status"] == "success" and song.tempo == 128.0 and r["result"]["old_value"] == 120.0

    def test_live_set_refuses_object(self, dispatch):
        r = dispatch("live_set", path="live_set", prop="master_track", value=1)
        assert r["status"] == "error"

    def test_live_call(self, dispatch, song):
        r = dispatch("live_call", path="live_set", method="create_midi_track", args=[-1])
        assert r["status"] == "success" and len(song.tracks) == 9

    def test_live_call_rejects_dunder(self, dispatch):
        r = dispatch("live_call", path="live_set", method="__init__", args=[])
        assert r["status"] == "error"

    def test_dunder_path_errors(self, dispatch):
        assert dispatch("live_get", path="live_set __class__")["status"] == "error"


def test_refs_to_zero_based():
    from ableton_mcp.lom import refs_to_zero_based
    assert refs_to_zero_based([1, {"$path": "live_set tracks 1 devices 2"}, [{"$path": "live_set"}]]) == \
        [1, {"$path": "live_set tracks 0 devices 1"}, [{"$path": "live_set"}]]
    assert refs_to_zero_based({"$path": "live_set", "x": 1}) == {"$path": "live_set", "x": 1}
    assert refs_to_zero_based(3.5) == 3.5

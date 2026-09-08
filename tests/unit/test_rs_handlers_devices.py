"""Device / chain / drum pad handlers through dispatch."""
import pytest

from tests.fixtures.mock_ableton import MockChain, MockDevice, MockDeviceParameter, MockDrumPad


@pytest.fixture
def rack_song(song):
    inner = MockDevice("Operator", params=[MockDeviceParameter("Device On", 1.0, 0.0, 1.0),
                                          MockDeviceParameter("Filter Freq", 1000.0, 20.0, 20000.0)])
    rack = MockDevice("Instrument Rack", chains=[MockChain("A", [inner]), MockChain("B", [MockDevice("Wavetable")])])
    serum = MockDevice("Serum", params=[MockDeviceParameter("Device On", 1.0, 0.0, 1.0),
                                       MockDeviceParameter("Fil Cutoff", 0.5, 0.0, 1.0),
                                       MockDeviceParameter("Osc A Level", 0.75, 0.0, 1.0)])
    song.tracks[0].devices = [serum, rack]
    return song


def test_get_device_parameters_normalized(dispatch, rack_song):
    r = dispatch("get_device_parameters", track_index=0, device_index=0)["result"]
    assert r["device_name"] == "Serum" and r["parameter_count"] == 3
    assert r["parameters"][1] == {"index": 1, "name": "Fil Cutoff", "value": 0.5, "min": 0.0, "max": 1.0,
                                  "display_value": "0.50", "is_enabled": True, "is_quantized": False, "value_items": []}


def test_set_device_parameter_by_name_partial(dispatch, rack_song):
    r = dispatch("set_device_parameter", track_index=0, device_index=0, parameter_name="cutoff", value=0.3)
    assert r["status"] == "success"
    res = r["result"]
    assert res["parameter_name"] == "Fil Cutoff" and res["match_type"] == "partial"
    assert res["value"] == 0.3 and res["new_value"] == 0.3 and res["old_value"] == 0.5
    assert res["raw_value"] == pytest.approx(0.3) and res["display_value"] == "0.30"
    assert res["min"] == 0.0 and res["max"] == 1.0 and res["parameter_index"] == 1
    assert res["device_name"] == "Serum" and res["track_name"] == "Track 1"
    assert res["track_index"] == 0 and res["device_index"] == 0


def test_set_device_parameter_by_index_denormalizes(dispatch, rack_song):
    inner = rack_song.tracks[0].devices[1].chains[0].devices[0]
    r = dispatch("set_device_parameter", track_index=0, device_index=1, chain_index=0, parameter_index=1, value=0.5)
    assert r["status"] == "success"
    assert inner.parameters[1].value == pytest.approx(20.0 + 0.5 * (20000.0 - 20.0))
    assert r["result"]["device_name"] == "Operator" and r["result"]["clamped"] is False


def test_set_device_parameter_clamps(dispatch, rack_song):
    r = dispatch("set_device_parameter", track_index=0, device_index=0, parameter_index=1, value=1.5)
    assert r["result"]["clamped"] is True and r["result"]["value"] == 1.0


def test_set_device_parameter_unknown_name(dispatch, rack_song):
    r = dispatch("set_device_parameter", track_index=0, device_index=0, parameter_name="nope", value=0.1)
    assert r["status"] == "error" and "not found" in r["message"]


def test_batch_set_device_parameters(dispatch, rack_song):
    r = dispatch("batch_set_device_parameters", track_index=0, device_index=0, parameters=[
        {"parameter_index": 1, "value": 0.1}, {"parameter_name": "osc a", "value": 0.9}, {"parameter_name": "zzz", "value": 0.5}])
    res = r["result"]
    assert res["updated"] == 2 and res["failed"] == 1
    serum = rack_song.tracks[0].devices[0]
    assert serum.parameters[1].value == pytest.approx(0.1) and serum.parameters[2].value == pytest.approx(0.9)
    assert res["results"][2]["ok"] is False


def test_set_device_enabled_and_toggle(dispatch, rack_song):
    serum = rack_song.tracks[0].devices[0]
    r = dispatch("set_device_enabled", track_index=0, device_index=0, enabled=False)
    assert r["result"]["is_active"] is False and serum.parameters[0].value == 0.0
    r = dispatch("toggle_device", track_index=0, device_index=0)
    assert r["result"]["is_active"] is True and r["result"]["was_active"] is False and serum.parameters[0].value == 1.0


def test_get_chain_info(dispatch, rack_song):
    r = dispatch("get_chain_info", track_index=0, device_index=1)["result"]
    assert r["chain_count"] == 2 and r["chains"][1]["devices"][0]["name"] == "Wavetable"
    r = dispatch("get_chain_info", track_index=0, device_index=1, chain_index=0)["result"]
    assert r["chain_name"] == "A" and r["devices"][0]["name"] == "Operator"


def test_get_chain_info_not_a_rack(dispatch, rack_song):
    assert dispatch("get_chain_info", track_index=0, device_index=0)["status"] == "error"


def test_delete_device(dispatch, rack_song):
    r = dispatch("delete_device", track_index=0, device_index=0)["result"]
    assert r["deleted_device"] == "Serum" and r["remaining_devices"] == 1 and r["device_name"] == "Serum"


def test_drum_pad_info_list_and_detail(dispatch, song):
    kick = MockDrumPad(36, "Kick", [MockChain("Kick", [MockDevice("Simpler")])])
    empty = MockDrumPad(37, "")
    song.tracks[0].devices = [MockDevice("Drum Rack", drum_pads=[empty, kick])]
    r = dispatch("get_drum_pad_info", track_index=0, device_index=0)["result"]
    assert r["pad_count"] == 2 and len(r["filled_pads"]) == 1 and r["filled_pads"][0]["pad_index"] == 1
    r = dispatch("get_drum_pad_info", track_index=0, device_index=0, pad_index=1)["result"]
    assert r["note"] == 36 and r["name"] == "Kick" and r["chain_count"] == 1


def test_navigate_preset(dispatch, rack_song):
    serum = rack_song.tracks[0].devices[0]
    serum.presets = ["Init", "Warm Pad"]
    r = dispatch("navigate_preset", track_index=0, device_index=0, direction="next")["result"]
    assert r["preset_index"] == 1 and r["preset_name"] == "Warm Pad"


def test_udp_dispatch_runs_allowlisted_command(script, rack_song):
    script._song = rack_song
    script._process_udp_command({"type": "set_device_parameter", "params": {
        "track_index": 0, "device_index": 0, "parameter_index": 1, "value": 0.2}})
    assert rack_song.tracks[0].devices[0].parameters[1].value == pytest.approx(0.2)


def test_udp_dispatch_ignores_other_commands(script, rack_song):
    script._song = rack_song
    script._process_udp_command({"type": "set_tempo", "params": {"tempo": 99}})
    assert rack_song.tempo == 120.0

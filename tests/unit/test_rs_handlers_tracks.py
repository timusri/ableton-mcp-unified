"""Track/session handlers through the registry dispatch (0-based wire protocol)."""
from tests.conftest import make_script
from tests.fixtures.mock_ableton import MockDevice, MockSong, MockTrack


def test_get_track_info_echoes_index_and_name(dispatch):
    r = dispatch("get_track_info", track_index=1)
    assert r["status"] == "success"
    assert r["result"]["index"] == 1 and r["result"]["name"] == "Track 2"
    assert r["result"]["track_index"] == 1 and r["result"]["track_name"] == "Track 2"
    assert r["result"]["is_group_track"] is False and r["result"]["arm"] is False


def test_get_track_info_group_track():
    song = MockSong()
    song.tracks.insert(0, MockTrack("Mix Bus", is_group=True))
    r = make_script(song)._process_command({"type": "get_track_info", "params": {"track_index": 0}})
    assert r["result"]["is_group_track"] is True and r["result"]["arm"] is None


def test_get_track_info_out_of_range(dispatch):
    assert dispatch("get_track_info", track_index=99)["status"] == "error"


def test_set_track_name(dispatch, song):
    r = dispatch("set_track_name", track_index=0, name="Drums")
    assert r["result"]["name"] == "Drums" and song.tracks[0].name == "Drums"
    assert r["result"]["track_index"] == 0


def test_set_track_volume_and_get(dispatch, song):
    r = dispatch("set_track_volume", track_index=0, volume=0.5)
    assert r["result"]["volume"] == 0.5 and r["result"]["track_name"] == "Track 1"
    assert dispatch("get_track_volume", track_index=0)["result"]["volume"] == 0.5


def test_set_track_panning_and_pan_alias(dispatch, song):
    r = dispatch("set_track_panning", track_index=0, panning=-0.5)
    assert r["result"]["panning"] == -0.5 and r["result"]["pan"] == -0.5
    r2 = dispatch("set_track_pan", track_index=0, pan=0.25)
    assert r2["status"] == "success" and song.tracks[0].mixer_device.panning.value == 0.25


def test_track_mute_solo(dispatch, song):
    assert dispatch("set_track_mute", track_index=1, mute=True)["status"] == "success"
    assert song.tracks[1].mute is True
    assert dispatch("set_track_solo", track_index=1, solo=True)["result"]["track_name"] == "Track 2"


def test_create_and_delete_track(dispatch, song):
    r = dispatch("create_midi_track", index=-1)
    assert r["result"]["index"] == 8 and len(song.tracks) == 9
    r = dispatch("delete_track", track_index=8)
    assert r["result"]["deleted_track"].startswith("MIDI Track") and len(song.tracks) == 8


def test_delete_last_track_refused():
    song = MockSong(n_tracks=1)
    r = make_script(song)._process_command({"type": "delete_track", "params": {"track_index": 0}})
    assert r["status"] == "error" and "last remaining" in r["message"]


def test_session_info(dispatch):
    r = dispatch("get_session_info")["result"]
    assert r["track_count"] == 8 and r["return_track_count"] == 2 and r["tempo"] == 120.0


def test_set_tempo_and_playback(dispatch, song):
    assert dispatch("set_tempo", tempo=140)["status"] == "success" and song.tempo == 140
    dispatch("start_playback")
    assert song.is_playing
    dispatch("stop_playback")
    assert not song.is_playing


def test_master_volume_is_modifying_and_works(dispatch, song):
    from AbletonMCPUnified.registry import COMMANDS
    assert COMMANDS["set_master_volume"].modifying
    r = dispatch("set_master_volume", volume=0.5)
    assert r["status"] == "success" and song.master_track.mixer_device.volume.value == 0.5


def test_return_tracks_and_sends(dispatch, song):
    r = dispatch("get_return_tracks")
    assert r["status"] == "success" and len(r["result"]["return_tracks"]) == 2
    r = dispatch("set_send_level", track_index=0, send_index=1, level=0.5)
    assert r["status"] == "success" and song.tracks[0].mixer_device.sends[1].value == 0.5


def test_scenes(dispatch, song):
    assert dispatch("get_all_scenes")["result"]["scenes"][0]["index"] == 0
    dispatch("create_scene", index=-1)
    assert len(song.scenes) == 9
    r = dispatch("set_scene_name", scene_index=0, name="Intro")
    assert r["result"]["scene_name"] == "Intro" or song.scenes[0].name == "Intro"


def test_enrichment_captures_device_name(dispatch, song):
    song.tracks[0].devices.append(MockDevice("Serum"))
    r = dispatch("get_device_parameters", track_index=0, device_index=0)
    assert r["result"]["device_name"] == "Serum" and r["result"]["track_name"] == "Track 1"


def test_timeout_param_is_stripped(dispatch):
    r = dispatch("get_session_info", _timeout=5)
    assert r["status"] == "success"

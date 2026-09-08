"""Arrangement, cue point and view handlers through dispatch."""
from tests.conftest import make_script
from tests.fixtures.mock_ableton import MockSong, MockTrack


def test_set_arrangement_loop_both_vocabularies(dispatch, song):
    r = dispatch("set_arrangement_loop", enabled=True, start=16.0, length=8.0)["result"]
    assert r == {"enabled": True, "start": 16.0, "length": 8.0, "end": 24.0,
                 "loop_enabled": True, "loop_start": 16.0, "loop_length": 8.0}
    r = dispatch("set_arrangement_loop", enabled=True, start=4.0, end=12.0)["result"]
    assert r["loop_length"] == 8.0 and song.loop_start == 4.0


def test_set_song_time_and_alias(dispatch, song):
    assert dispatch("set_song_time", time=8.0)["result"]["time"] == 8.0
    assert dispatch("jump_to_time", time=12.0)["result"]["current_time"] == 12.0 and song.current_song_time == 12.0


def test_get_arrangement_length(dispatch):
    assert dispatch("get_arrangement_length")["status"] == "success"


def test_cue_point_crud_and_aliases(dispatch, song):
    r = dispatch("create_cue_point", time=16.0, name="Drop")
    assert r["status"] == "success" and song.cue_points[0].name == "Drop"
    r = dispatch("create_locator", time=32.0, name="Outro")
    assert r["status"] == "success" and len(song.cue_points) == 2
    r = dispatch("get_locators")["result"]
    assert r["locator_count"] == 2 and r["cue_points"][0] == {"index": 0, "name": "Drop", "time": 16.0}
    assert dispatch("create_cue_point", time=16.0)["status"] == "error"  # duplicate
    r = dispatch("jump_to_cue", name="Outro")["result"]
    assert r["time"] == 32.0 and song.cue_points[1].jumped
    song.current_song_time = 0.0
    assert dispatch("jump_to_next_cue")["result"]["time"] == 16.0
    assert dispatch("jump_to_cue_point", index=1)["result"]["name"] == "Outro"
    assert dispatch("jump_to_prev_cue")["result"]["direction"] == "prev"
    r = dispatch("delete_locator", locator_index=0)["result"]
    assert r["deleted"] and r["name"] == "Drop" and len(song.cue_points) == 1
    assert dispatch("delete_cue_point", time=32.0)["result"]["deleted"] and song.cue_points == []


def test_arrangement_clip_lifecycle(dispatch, song):
    r = dispatch("create_arrangement_clip", track_index=0, position=8.0, length=4.0)["result"]
    assert r["start_time"] == 8.0 and r["overlapped_clips"] == []
    r = dispatch("create_arrangement_clip", track_index=0, position=10.0, length=4.0)["result"]
    assert r["overlapped_clips"] == ["(unnamed)"]
    r = dispatch("get_arrangement_info", track_index=0)["result"]
    assert r["tracks"][0]["clip_count"] == 2 and r["transport"]["tempo"] == 120.0
    r = dispatch("set_arrangement_clip_property", track_index=0, clip_index=0, property="name", value="Lead")
    assert r["result"]["value"] == "Lead"
    assert dispatch("set_arrangement_clip_property", track_index=0, clip_index=0, property="__class__", value=1)["status"] == "error"
    assert dispatch("delete_arrangement_clip", track_index=0, clip_name="Lead")["result"]["deleted"]
    assert dispatch("delete_arrangement_clip", track_index=0, clip_index=0)["result"]["deleted"]
    assert song.tracks[0].arrangement_clips == []


def test_arrangement_info_skips_group_tracks():
    song = MockSong()
    song.tracks.insert(0, MockTrack("Mix Bus", is_group=True))
    script = make_script(song)
    r = script._process_command({"type": "get_arrangement_info", "params": {"track_index": -1}})["result"]
    assert [t["name"] for t in r["tracks"]][0] == "Track 1"
    r = script._process_command({"type": "get_arrangement_info", "params": {"track_index": 0}})["result"]
    assert r["tracks"][0]["is_group_track"] is True and r["tracks"][0]["arrangement_clips"] == []


def test_duplicate_to_arrangement(dispatch, song):
    song.tracks[0].clip_slots[0].create_clip(4.0)
    r = dispatch("duplicate_to_arrangement", track_index=0, clip_index=0, destination_time=16.0)["result"]
    assert r["duplicated"] and r["start_time"] == 16.0


def test_set_view_and_focus_alias(dispatch, script):
    r = dispatch("set_view", view_name="Arranger")["result"]
    assert r["visible"] is True and r["view_name"] == "Arranger"
    assert dispatch("focus_view", view_name="Session")["status"] == "success"
    script.application().view.show_view.assert_called_with("Session")


def test_control_arrangement_view(dispatch, song):
    assert dispatch("control_arrangement_view", action="follow_on")["result"]["done"]
    assert song.view.follow_song is True
    assert dispatch("control_arrangement_view", action="bogus")["status"] == "error"


def test_arrangement_commands_echo_arrangement_clip_name(dispatch, song):
    """clip_index on *arrangement* commands refers to arrangement clips, and the echoed name must match."""
    track = song.tracks[0]
    from tests.fixtures.mock_ableton import MockClip
    arr = MockClip(name="Timeline clip", length=4.0, start_time=64.0)
    track.arrangement_clips.append(arr)
    idx = len(track.arrangement_clips) - 1
    r = dispatch("add_notes_to_arrangement_clip", track_index=0, clip_index=idx,
                 notes=[{"pitch": 60, "start_time": 0.0, "duration": 1.0, "velocity": 100}])
    assert r["status"] == "success", r
    assert r["result"].get("clip_name") in (None, "Timeline clip")
    assert r["result"].get("clip_name") != (track.clip_slots[idx].clip.name if idx < len(track.clip_slots) and track.clip_slots[idx].has_clip else None) or r["result"].get("clip_name") == "Timeline clip"

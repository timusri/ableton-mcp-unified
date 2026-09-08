"""Cue point tools sequence playhead move -> settle -> toggle -> verify (Live applies cues asynchronously)."""
from unittest.mock import patch

from ableton_mcp import tools_manual as m


def _conn(mock_conn, cue_states):
    """cue_states: list of get_cue_points results returned in order (last one repeats)."""
    state = {"i": 0}

    def side_effect(command, params=None, **kw):
        if command == "get_session_info":
            return {"signature_numerator": 4, "signature_denominator": 4}
        if command == "get_cue_points":
            r = cue_states[min(state["i"], len(cue_states) - 1)]
            state["i"] += 1
            return r
        return {}
    mock_conn.send_command.side_effect = side_effect
    return mock_conn


@patch("time.sleep")
def test_create_moves_playhead_then_creates_then_renames(_sleep, mock_conn):
    _conn(mock_conn, [{"cue_points": []}, {"cue_points": [{"index": 0, "name": "1", "time": 24.0}]},
                      {"cue_points": [{"index": 0, "name": "Drop", "time": 24.0}]}])
    out = m.create_cue_point(bar=7, name="Drop")
    cmds = [c[0][0] for c in mock_conn.send_command.call_args_list]
    assert cmds.index("set_song_time") < cmds.index("create_cue_point") < cmds.index("live_set")
    assert mock_conn.send_command.call_args_list[cmds.index("set_song_time")][0][1] == {"time": 24.0}
    assert mock_conn.send_command.call_args_list[cmds.index("live_set")][0][1] == {
        "path": "live_set cue_points 0", "prop": "name", "value": "Drop"}
    assert out == "Created cue point 1 'Drop' at bar 7 (beat 24.0)"


@patch("time.sleep")
def test_create_refuses_duplicate(_sleep, mock_conn):
    _conn(mock_conn, [{"cue_points": [{"index": 0, "name": "x", "time": 24.0}]}])
    assert m.create_cue_point(bar=7).startswith("Error: a cue point already exists")
    assert "create_cue_point" not in [c[0][0] for c in mock_conn.send_command.call_args_list]


@patch("time.sleep")
def test_delete_by_index_moves_playhead_first(_sleep, mock_conn):
    _conn(mock_conn, [{"cue_points": [{"index": 0, "name": "Drop", "time": 24.0}]},
                      {"cue_points": [{"index": 0, "name": "Drop", "time": 24.0}]}, {"cue_points": []}])
    out = m.delete_cue_point(cue_index=1)
    cmds = [c[0][0] for c in mock_conn.send_command.call_args_list]
    assert cmds.index("set_song_time") < cmds.index("delete_cue_point")
    assert out == "Deleted cue point 1 'Drop'"

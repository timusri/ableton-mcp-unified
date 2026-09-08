"""Registry invariants: verb prefixes imply modifying; aliases resolve; dispatch works."""
import pytest

from AbletonMCPUnified.registry import COMMANDS, command, describe_commands, modifying_commands

MODIFYING_VERBS = ("set_", "create_", "delete_", "fire_", "stop_", "start_", "add_", "remove_", "duplicate_", "move_",
                   "load_", "toggle_", "select_", "apply_", "commit_", "quantize_", "humanize_", "generate_",
                   "transpose_", "undo", "redo", "freeze_", "flatten_", "fold_", "unfold_", "ungroup_", "unsolo_",
                   "unmute_", "unarm_", "solo_", "capture_", "jump_", "scrub_", "tap_", "continue_", "trigger_",
                   "re_enable", "clear_", "deselect_", "navigate_", "live_set", "live_call", "batch_")
EXCEPTIONS = set()


def test_verb_prefix_implies_modifying():
    offenders = sorted(n for n, s in COMMANDS.items() if n == s.name and not s.modifying
                       and n.startswith(MODIFYING_VERBS) and n not in EXCEPTIONS)
    assert offenders == []


def test_aliases_resolve_to_canonical():
    assert COMMANDS["set_track_pan"].name == "set_track_panning"
    assert COMMANDS["jump_to_time"].name == "set_song_time"
    assert COMMANDS["get_locators"].name == "get_cue_points"
    assert COMMANDS["create_locator"].name == "create_cue_point"
    assert COMMANDS["delete_locator"].name == "delete_cue_point"
    assert COMMANDS["jump_to_cue_point"].name == "jump_to_cue"
    assert COMMANDS["focus_view"].name == "set_view"


def test_modifying_commands_are_canonical_only():
    assert "set_track_pan" not in modifying_commands()
    assert "set_track_panning" in modifying_commands()


def test_describe_commands_marks_aliases():
    rows = {r["name"]: r for r in describe_commands()}
    assert rows["set_track_pan"]["is_alias"] and rows["set_track_pan"]["canonical"] == "set_track_panning"


def test_duplicate_registration_raises():
    with pytest.raises(ValueError):
        @command("set_tempo")
        def other(self, params):
            return {}


def test_command_count():
    assert len({s.name for s in COMMANDS.values()}) >= 270


def test_unknown_command(dispatch):
    resp = dispatch("no_such_command")
    assert resp["status"] == "error" and "Unknown command" in resp["message"]


def test_list_commands(dispatch):
    resp = dispatch("list_commands")
    assert resp["status"] == "success"
    assert resp["result"]["command_count"] >= 270
    assert "set_tempo" in resp["result"]["modifying"]


def test_health_check_has_version(dispatch):
    result = dispatch("health_check")["result"]
    assert result["rs_version"].startswith("unified-")
    assert result["command_count"] >= 270

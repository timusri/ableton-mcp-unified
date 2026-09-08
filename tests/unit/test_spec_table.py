"""spec.py is the single source of truth; it must agree with the Remote Script registry."""
import re

import pytest

from AbletonMCPUnified.registry import COMMANDS, canonical_commands, modifying_commands
from ableton_mcp import spec
from ableton_mcp.spec import ALL_SPECS, HIDDEN_SPECS, MODIFYING_COMMANDS, TOOL_SPECS, REQUIRED

INDEX_NAMES = {"track_index", "clip_index", "scene_index", "device_index", "return_index", "send_index",
               "pad_index", "chain_index", "parameter_index", "slot_index", "locator_index", "marker_index",
               "groove_index", "macro_index", "new_index", "cue_index"}


def test_every_spec_command_exists_in_remote_script():
    missing = sorted({s.command for s in ALL_SPECS if s.command} - set(canonical_commands()))
    assert missing == []


def test_every_remote_script_command_has_a_spec_row():
    covered = {s.command for s in ALL_SPECS if s.command}
    assert sorted(set(canonical_commands()) - covered) == []


def test_modifying_sets_agree():
    assert set(MODIFYING_COMMANDS) == set(modifying_commands())


def test_rs_modifying_table_matches_registry():
    assert spec._RS_MODIFYING == {n: s.modifying for n, s in COMMANDS.items() if n == s.name}


def test_tool_names_unique_including_aliases():
    names = [s.name for s in TOOL_SPECS] + [a for s in TOOL_SPECS for a in s.deprecated_aliases]
    assert len(names) == len(set(names))


def test_tool_names_are_verb_noun_snake_case():
    for s in TOOL_SPECS:
        assert re.match(r"^[a-z][a-z0-9_]*$", s.name), s.name
        assert "_" in s.name or s.name in ("undo", "redo"), s.name


@pytest.mark.parametrize("s", ALL_SPECS, ids=lambda s: s.name)
def test_index_params_are_flagged(s):
    for p in s.params:
        if p.name in INDEX_NAMES:
            assert p.index or p.optional_index, f"{s.name}.{p.name} is an index param but not flagged"
            assert p.type == "int"
        if p.index:
            assert p.name in INDEX_NAMES or p.name.endswith("_index"), f"{s.name}.{p.name} flagged index"
        if p.optional_index:
            assert p.default == 0, f"{s.name}.{p.name} optional_index must default to 0"
        if p.name == "index":
            assert not p.index and not p.optional_index, f"{s.name}.index is the -1 append sentinel"


def test_manual_rows_have_implementations():
    from ableton_mcp.tools_manual import MANUAL_TOOLS
    manual = {s.name for s in TOOL_SPECS if s.manual}
    assert manual == set(MANUAL_TOOLS)


def test_hidden_rows_have_no_tool():
    from ableton_mcp import server
    registered = set(server.GENERATED_TOOLS) | set(server.MANUAL_TOOL_NAMES)
    assert not (registered & {s.name for s in HIDDEN_SPECS})


def test_docs_are_current():
    import os
    import subprocess
    import sys
    root = os.path.join(os.path.dirname(__file__), "..", "..")
    out = subprocess.run([sys.executable, os.path.join(root, "scripts", "gen_tools_md.py"), "--stdout"],
                         capture_output=True, text=True, check=True).stdout
    with open(os.path.join(root, "docs", "tools.md")) as fh:
        assert fh.read() == out, "docs/tools.md is stale: run scripts/gen_tools_md.py"

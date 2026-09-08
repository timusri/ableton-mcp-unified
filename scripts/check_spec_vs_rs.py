#!/usr/bin/env python3
"""Report skew between ableton_mcp/spec.py and the Remote Script registry (offline, no Live needed)."""
import os
import sys
import types

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)

if "_Framework" not in sys.modules:
    fw = types.ModuleType("_Framework")
    cs = types.ModuleType("_Framework.ControlSurface")

    class ControlSurface(object):
        def __init__(self, c_instance):
            pass
    cs.ControlSurface = ControlSurface
    sys.modules["_Framework"] = fw
    sys.modules["_Framework.ControlSurface"] = cs

from AbletonMCPUnified.registry import canonical_commands, modifying_commands  # noqa: E402
from ableton_mcp.spec import ALL_SPECS, MODIFYING_COMMANDS, TOOL_SPECS, HIDDEN_SPECS  # noqa: E402

spec_cmds = {s.command for s in ALL_SPECS if s.command}
rs_cmds = set(canonical_commands())
missing_in_rs = sorted(spec_cmds - rs_cmds)
missing_in_spec = sorted(rs_cmds - spec_cmds)
mod_mismatch = sorted(set(MODIFYING_COMMANDS) ^ set(modifying_commands()))
print("Remote Script commands: %d (modifying %d)" % (len(rs_cmds), len(modifying_commands())))
print("Tools: %d, hidden command rows: %d" % (len(TOOL_SPECS), len(HIDDEN_SPECS)))
print("spec commands missing in RS: %d %s" % (len(missing_in_rs), missing_in_rs))
print("RS commands missing in spec: %d %s" % (len(missing_in_spec), missing_in_spec))
print("modifying mismatches: %d %s" % (len(mod_mismatch), mod_mismatch))
sys.exit(1 if (missing_in_rs or missing_in_spec or mod_mismatch) else 0)

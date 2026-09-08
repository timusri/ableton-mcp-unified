#!/usr/bin/env python3
"""Point Claude Code's `mcpServers.AbletonMCP` entry at this checkout.

    scripts/switch_mcp_config.py             # write the entry (backs up ~/.claude.json first)
    scripts/switch_mcp_config.py --rollback  # restore the backup made by the previous run
"""
import json
import os
import shutil
import sys

CFG = os.path.expanduser("~/.claude.json")
BAK = CFG + ".bak-ableton-mcp"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENTRY = {"type": "stdio", "command": "uv", "args": ["--directory", ROOT, "run", "ableton-mcp-unified"], "env": {}}

if "--rollback" in sys.argv:
    if not os.path.exists(BAK):
        sys.exit("no backup found at %s" % BAK)
    shutil.copy(BAK, CFG)
    print("restored", CFG, "from", BAK)
else:
    with open(CFG) as fh:
        cfg = json.load(fh)
    shutil.copy(CFG, BAK)
    cfg.setdefault("mcpServers", {})["AbletonMCP"] = ENTRY
    with open(CFG, "w") as fh:
        json.dump(cfg, fh, indent=2)
    print("mcpServers.AbletonMCP ->", json.dumps(ENTRY))
print("Restart Claude Code (or /mcp reconnect) for the change to take effect.")

"""FastMCP application: registers generated + manual tools and checks command skew on startup."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # mcp 2.x renamed it
    from mcp.server.mcpserver import MCPServer as FastMCP

from . import tools_generated, tools_manual
from .connection import get_ableton_connection, reset_connection
from .spec import ALL_SPECS, MODIFYING_COMMANDS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("AbletonMCPUnified")


def check_command_skew(list_commands_result: Dict[str, Any]) -> Dict[str, Any]:
    """Compare the Remote Script's registry with the server spec; returns a skew report."""
    rs_commands = {c["name"]: c for c in list_commands_result.get("commands", []) if not c.get("is_alias")}
    rs_modifying = {name for name, c in rs_commands.items() if c.get("modifying")}
    spec_commands = {s.command for s in ALL_SPECS if s.command}
    return {
        "rs_version": list_commands_result.get("rs_version"),
        "missing_in_rs": sorted(spec_commands - set(rs_commands)),
        "missing_in_spec": sorted(set(rs_commands) - spec_commands),
        "modifying_mismatch": sorted((rs_modifying ^ set(MODIFYING_COMMANDS)) & spec_commands & set(rs_commands)),
    }


@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    try:
        logger.info("AbletonMCPUnified server starting up")
        try:
            ableton = get_ableton_connection()
            report = check_command_skew(ableton.send_command("list_commands"))
            logger.info(f"Connected to Remote Script {report['rs_version']}")
            for key in ("missing_in_rs", "missing_in_spec", "modifying_mismatch"):
                if report[key]:
                    logger.warning(f"Command skew ({key}): {report[key]}")
        except Exception as e:
            logger.warning(f"Could not connect to Ableton on startup: {e}")
            logger.warning("Make sure the AbletonMCPUnified Remote Script is selected in Live > Preferences > Link/Tempo/MIDI")
        yield {}
    finally:
        reset_connection()
        logger.info("AbletonMCPUnified server shut down")


mcp = FastMCP("AbletonMCPUnified", instructions=(
    "Ableton Live integration. All track/clip/scene/device/chain/parameter indices are 1-based (as in Live's UI); "
    "device parameter values are normalized 0.0-1.0. Use list_commands/send_command for Remote Script commands "
    "without a dedicated tool and live_get/live_children/live_set/live_call for anything else in the Live Object Model."
), lifespan=server_lifespan)

GENERATED_TOOLS = tools_generated.register(mcp)
MANUAL_TOOL_NAMES = tools_manual.register(mcp)


def main():
    mcp.run()


if __name__ == "__main__":
    main()

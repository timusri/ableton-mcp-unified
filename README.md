# ableton-mcp-unified

An MCP server and a matching Ableton Live Remote Script that let an AI assistant read and
control a Live set: tracks, clips, notes, devices, racks, chains, arrangement, cue points,
browser, routing, transport, plus a generic Live Object Model escape hatch.

| | |
|---|---|
| MCP tools | 154 (+7 deprecated aliases), see [docs/tools.md](docs/tools.md) |
| Remote Script commands | 274 canonical, 281 wire names, all reachable via `send_command` |
| Generic LOM | `live_get`, `live_children`, `live_set`, `live_call` (no `exec` / `eval`) |
| Transport | JSON over TCP `localhost:9877`, fire-and-forget UDP on `9878` for parameter sweeps |

## Conventions

- **1-based indices everywhere** (tracks, clips, scenes, devices, chains, parameters, returns, sends,
  pads, cue points), exactly as Live's UI numbers them. `0` means "unset" for optional indices;
  `index=-1` means "append" in `create_*`.
- **Device parameter values are normalized 0.0 to 1.0** on input. Responses return `value`, `raw_value`,
  `display_value`, `min`, `max` and `old_value`. Parameters are addressable by 1-based index, exact name,
  partial name or plugin alias (`plugin_aliases.py`).
- **Every response echoes index and name** of the objects touched (`track_index`, `track_name`,
  `device_index`, `device_name`, ...).
- **`verb_noun` tool names.** A few older names remain as deprecated alias tools: `set_track_pan`,
  `jump_to_time`, `get_locators`, `create_locator`, `delete_locator`, `focus_view`, `set_ableton_view`.
- LOM paths use the same 1-based indices: `live_set tracks 1 devices 2 parameters 3`.

## Layout

```
ableton_mcp/            MCP server (Python 3.10+, mcp 1.x)
  spec.py               the spec table: single source of truth for tools, params, modifying flags
  tools_generated.py    builds tools from spec rows; tools_manual.py holds tools with logic
  connection.py         TCP (health-checked, locked) + UdpSender; convert.py index / bar-beat helpers
  lom.py                1-based <-> 0-based LOM path rewriting
AbletonMCPUnified/      Remote Script (Live's embedded Python, stdlib only)
  __init__.py           sockets (TCP + UDP), registry dispatch, main-thread scheduling
  registry.py           @command decorator; handlers/*.py one mixin per domain; lom.py safe walker
tests/                  unit (mocked Live) + integration (needs a running Live)
scripts/                install_remote_script.sh, gen_tools_md.py, check_spec_vs_rs.py, switch_mcp_config.py
```

## Install

Requirements: Ableton Live 11 or 12, Python 3.10+, [uv](https://docs.astral.sh/uv/).

```bash
git clone <this repo> && cd ableton-mcp-unified
uv sync --extra dev && uv run pytest          # unit tests, no Live needed
scripts/install_remote_script.sh              # symlink into ~/Music/Ableton/User Library/Remote Scripts
```

Then in Live: **Settings > Link, Tempo & MIDI > Control Surface: AbletonMCPUnified** (restart Live first).
Only one MCP Remote Script can be active at a time, since they all bind port 9877.

### MCP client configuration

Claude Code (`~/.claude.json`, under `mcpServers`), or run `scripts/switch_mcp_config.py` to write it:

```json
"AbletonMCP": {
  "type": "stdio",
  "command": "uv",
  "args": ["--directory", "/path/to/ableton-mcp-unified", "run", "ableton-mcp-unified"],
  "env": {}
}
```

Other MCP clients use the same command line: `uv --directory /path/to/ableton-mcp-unified run ableton-mcp-unified`.

### Environment variables

Server: `ABLETON_HOST`, `ABLETON_PORT` (9877), `ABLETON_UDP_PORT` (9878), `MCP_MAX_CONNECT_ATTEMPTS`,
`MCP_MODIFYING_CMD_TIMEOUT`, `MCP_READ_CMD_TIMEOUT`, `MCP_COMMAND_DELAY`.
Remote Script: `ABLETON_MCP_PORT`, `ABLETON_MCP_UDP_PORT`, `ABLETON_MCP_MAX_BUFFER`.

## Adding a command

1. Add a `@command("name", modifying=True)` handler to the right `AbletonMCPUnified/handlers/*.py` mixin.
2. Add a `T(...)` row to `ableton_mcp/spec.py` (`manual=True` if it needs logic in `tools_manual.py`,
   `hidden=True` if it should only be reachable through `send_command`).
3. `uv run python scripts/gen_tools_md.py && uv run pytest`. The spec/registry agreement tests catch the rest.

## Verifying against Live

`uv run pytest -m integration tests/integration -v` runs the live checklist (health check, 1-based read-back,
setter echo, loop brace, cue points, LOM). Use a scratch project.

## License

MIT. See `LICENSE`.

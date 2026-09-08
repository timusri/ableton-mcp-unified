#!/usr/bin/env python3
"""Generate docs/tools.md from ableton_mcp/spec.py (run after editing the spec)."""
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)

from ableton_mcp.spec import CATEGORIES, HIDDEN_SPECS, REQUIRED, TOOL_SPECS  # noqa: E402

TITLES = {"session": "Session & transport", "tracks": "Tracks, returns & master", "clips": "Session clips",
          "notes": "MIDI notes & generators", "scenes": "Scenes", "devices": "Devices & parameters",
          "chains": "Rack chains", "browser": "Browser & loading", "routing": "Input/output routing",
          "view": "Views & selection", "recording": "Recording & automation modes", "arrangement": "Arrangement",
          "cue_points": "Cue points (locators)", "lom": "Generic Live Object Model"}


def fmt_default(p):
    if p.default is REQUIRED:
        return "required"
    return "default `%r`" % (p.default,)


def param_line(p):
    flags = []
    if p.index:
        flags.append("1-based")
    if p.optional_index:
        flags.append("1-based, 0 = unset")
    if p.index_list:
        flags.append("list of 1-based")
    if p.rs_name:
        flags.append("wire name `%s`" % p.rs_name)
    extra = (" — " + p.doc) if p.doc else ""
    return "  - `%s` (%s, %s%s)%s" % (p.name, p.type, fmt_default(p), ("; " + ", ".join(flags)) if flags else "", extra)


def render():
    out = ["# Tools", "",
           "Generated from `ableton_mcp/spec.py` by `scripts/gen_tools_md.py`. Do not edit by hand.", "",
           "Conventions: all indices are 1-based (as shown in Live); device parameter values are normalized 0.0–1.0; "
           "responses echo the indices and names of the objects touched. Commands marked *modifying* run on Live's main thread.", "",
           "Tools: %d (+%d deprecated aliases). Remote Script commands without a dedicated tool: %d "
           "(use `send_command`)." % (len(TOOL_SPECS), sum(len(s.deprecated_aliases) for s in TOOL_SPECS), len(HIDDEN_SPECS)), ""]
    for cat in CATEGORIES:
        specs = [s for s in TOOL_SPECS if s.category == cat]
        if not specs:
            continue
        out.append("## %s" % TITLES.get(cat, cat))
        out.append("")
        for s in sorted(specs, key=lambda x: x.name):
            tag = " *(modifying)*" if s.modifying else ""
            manual = " *(manual)*" if s.manual else ""
            out.append("### `%s`%s%s" % (s.name, tag, manual))
            out.append("")
            out.append(s.doc.strip().split("\n")[0])
            if s.command and s.command != s.name:
                out.append("")
                out.append("Remote Script command: `%s`" % s.command)
            if s.deprecated_aliases:
                out.append("")
                out.append("Deprecated aliases: " + ", ".join("`%s`" % a for a in s.deprecated_aliases))
            if s.params:
                out.append("")
                out.append("Parameters:")
                out.extend(param_line(p) for p in s.params)
            out.append("")
    out.append("## Remote Script commands without a dedicated tool")
    out.append("")
    out.append("Call these with `send_command(command, params)`; `*_index` params are 1-based and converted automatically.")
    out.append("")
    for cat in CATEGORIES:
        specs = [s for s in HIDDEN_SPECS if s.category == cat]
        if not specs:
            continue
        out.append("### %s" % TITLES.get(cat, cat))
        out.append("")
        for s in sorted(specs, key=lambda x: x.name):
            params = ", ".join("%s%s" % (p.name, "" if p.default is REQUIRED else "=%r" % (p.default,)) for p in s.params)
            out.append("- `%s(%s)`%s — %s" % (s.name, params, " *(modifying)*" if s.modifying else "", s.doc.strip().split("\n")[0]))
        out.append("")
    return "\n".join(out).rstrip("\n") + "\n"


if __name__ == "__main__":
    text = render()
    if "--stdout" in sys.argv:
        sys.stdout.write(text)
    else:
        path = os.path.join(ROOT, "docs", "tools.md")
        with open(path, "w") as fh:
            fh.write(text)
        print("wrote", path)

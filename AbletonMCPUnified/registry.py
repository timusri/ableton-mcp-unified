"""Command registry for the unified Remote Script.

Every handler method is registered with ``@command(name, modifying=..., aliases=...)``.
``modifying=True`` means the handler mutates Live state and must run on Live's main
thread (see ``AbletonMCP._run_on_main_thread``). Aliases are alternative wire names
kept for backwards compatibility with older clients.
"""


class CommandSpec(object):
    __slots__ = ("name", "method", "modifying", "aliases")

    def __init__(self, name, method, modifying, aliases):
        self.name = name
        self.method = method
        self.modifying = modifying
        self.aliases = tuple(aliases)

    def __repr__(self):
        return "CommandSpec(%r, %r, modifying=%r, aliases=%r)" % (
            self.name, self.method, self.modifying, self.aliases)


COMMANDS = {}


def command(name, modifying=False, aliases=()):
    """Register ``fn`` as the handler for wire command ``name`` (and ``aliases``)."""
    def deco(fn):
        spec = CommandSpec(name, fn.__name__, modifying, aliases)
        for wire_name in (name,) + tuple(aliases):
            existing = COMMANDS.get(wire_name)
            if existing is not None and existing.method != fn.__name__:
                raise ValueError("Command %r already registered by %s" % (wire_name, existing.method))
            COMMANDS[wire_name] = spec
        return fn
    return deco


def canonical_commands():
    """Sorted canonical (non-alias) command names."""
    return sorted({spec.name for spec in COMMANDS.values()})


def modifying_commands():
    """Sorted canonical names of commands that must run on the main thread."""
    return sorted({spec.name for spec in COMMANDS.values() if spec.modifying})


def describe_commands():
    """Wire-level description used by the ``list_commands`` command."""
    out = []
    for wire_name in sorted(COMMANDS):
        spec = COMMANDS[wire_name]
        out.append({
            "name": wire_name,
            "canonical": spec.name,
            "modifying": spec.modifying,
            "is_alias": wire_name != spec.name,
        })
    return out

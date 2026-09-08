"""1-based <-> 0-based rewriting for Live Object Model paths used by the live_* tools."""
from __future__ import annotations

import re

ROOTS = ("live_set", "live_app")
_INT = re.compile(r"^-?\d+$")


def path_to_zero_based(path: str) -> str:
    """'live_set tracks 1 devices 2' -> 'live_set tracks 0 devices 1'. Integers must be >= 1."""
    if not isinstance(path, str) or not path.strip():
        raise ValueError("path must be a non-empty string such as 'live_set tracks 1'")
    tokens = path.split()
    if tokens[0] not in ROOTS:
        raise ValueError(f"path must start with one of {ROOTS}, got {tokens[0]!r}")
    out = [tokens[0]]
    for tok in tokens[1:]:
        if _INT.match(tok):
            n = int(tok)
            if n < 1:
                raise ValueError(f"index {n} in path {path!r} must be >= 1 (indices are 1-based)")
            out.append(str(n - 1))
        else:
            out.append(tok)
    return " ".join(out)


def path_to_one_based(path: str | None) -> str | None:
    """Inverse of path_to_zero_based for paths echoed back by the Remote Script."""
    if not path:
        return path
    tokens = path.split()
    out = [tokens[0]]
    for tok in tokens[1:]:
        out.append(str(int(tok) + 1) if _INT.match(tok) and int(tok) >= 0 else tok)
    return " ".join(out)


def rewrite_paths(obj):
    """Recursively rewrite every 'path' value in a serialized LOM response to 1-based."""
    if isinstance(obj, dict):
        return {k: (path_to_one_based(v) if k == "path" and isinstance(v, str) else rewrite_paths(v))
                for k, v in obj.items()}
    if isinstance(obj, list):
        return [rewrite_paths(x) for x in obj]
    return obj


PATH_KEY = "$path"


def refs_to_zero_based(obj):
    """Recursively rewrite {"$path": "<1-based path>"} object references inside args/values to 0-based."""
    if isinstance(obj, dict):
        if list(obj.keys()) == [PATH_KEY] and isinstance(obj[PATH_KEY], str):
            return {PATH_KEY: path_to_zero_based(obj[PATH_KEY])}
        return {k: refs_to_zero_based(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [refs_to_zero_based(x) for x in obj]
    return obj

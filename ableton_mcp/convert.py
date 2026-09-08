"""Index, parameter and bar/beat conversion helpers.

Convention: every user-facing index is 1-based (matches Live's UI); the Remote Script
speaks 0-based. ``0`` means "unset" for optional indices.
"""
from __future__ import annotations

from typing import Any, Optional


def _to_zero_based(index: int, field_name: str = "index") -> int:
    """Convert a required 1-based index to 0-based. Raises ValueError for < 1."""
    if index < 1:
        raise ValueError(f"{field_name} must be >= 1 (1-based), got {index}")
    return index - 1


def _optional_to_zero_based(index: int, field_name: str = "index") -> Optional[int]:
    """Convert an optional 1-based index to 0-based; 0 -> None (unset)."""
    if index < 0:
        raise ValueError(f"{field_name} must be >= 0 (0 = unset, 1+ = 1-based), got {index}")
    if index == 0:
        return None
    return index - 1


# public names
to_zero_based = _to_zero_based
optional_to_zero_based = _optional_to_zero_based


def normalize_param(value: float, min_val: float, max_val: float) -> float:
    """Normalize a raw parameter value to 0.0-1.0 (clamped)."""
    if max_val == min_val:
        return 0.0
    normalized = (value - min_val) / (max_val - min_val)
    return max(0.0, min(1.0, normalized))


def denormalize_param(normalized: float, min_val: float, max_val: float) -> float:
    """Convert a normalized 0.0-1.0 value (clamped) to the raw parameter range."""
    clamped = max(0.0, min(1.0, normalized))
    return min_val + clamped * (max_val - min_val)


def bar_to_beat(bar: int, numerator: int = 4, denominator: int = 4) -> float:
    """1-based bar number -> beat position (bar 1 = beat 0)."""
    return (bar - 1) * numerator * (4 / denominator)


def beat_to_bar(beat: float, numerator: int = 4, denominator: int = 4) -> int:
    """Beat position -> 1-based bar number."""
    beats_per_bar = numerator * (4 / denominator)
    return int(beat / beats_per_bar) + 1


INDEX_KEY_SUFFIX = "_index"
INDEX_KEYS_EXACT = ("index",)
# result keys that look like indices but are not (MIDI notes, sentinels, counts)
NON_INDEX_KEYS = frozenset({"playing_slot_index_raw"})


def is_index_key(key: str) -> bool:
    return key in INDEX_KEYS_EXACT or key.endswith(INDEX_KEY_SUFFIX)


def to_one_based(obj: Any) -> Any:
    """Recursively rewrite 0-based ``index``/``*_index`` integer values in a response to 1-based.

    Negative values (Live sentinels such as -1 = none, -2 = arrangement) are left alone.
    """
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if isinstance(k, str) and is_index_key(k) and k not in NON_INDEX_KEYS and type(v) is int and v >= 0:
                out[k] = v + 1
            elif isinstance(k, str) and (is_index_key(k) or k.endswith("_indices")) and isinstance(v, list) and all(type(x) is int for x in v):
                out[k] = [x + 1 if x >= 0 else x for x in v]
            else:
                out[k] = to_one_based(v)
        return out
    if isinstance(obj, list):
        return [to_one_based(x) for x in obj]
    return obj


def params_to_zero_based(params: dict) -> dict:
    """Generic 1-based -> 0-based conversion for raw ``send_command`` params.

    Keys ending in ``_index`` are required indices (must be >= 1); ``index`` (the
    ``create_*`` insert position) keeps its ``-1`` = append sentinel; lists of
    indices are converted element-wise.
    """
    out = {}
    for k, v in params.items():
        if k.endswith(INDEX_KEY_SUFFIX) and type(v) is int:
            out[k] = _to_zero_based(v, k)
        elif k.endswith("_indices") and isinstance(v, list):
            out[k] = [_to_zero_based(x, k) for x in v]
        else:
            out[k] = v
    return out

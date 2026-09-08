"""Hand-written tools with logic (formatting, name resolution, bar/beat math, LOM, UDP).

Every function here has a ``manual=True`` row in spec.py; ``register()`` binds them by name
so the docs, categories and modifying set still come from one place.
"""
from __future__ import annotations

import json
import logging
import math
from typing import Any, Dict, List, Optional

from .connection import get_ableton_connection, get_udp_sender
from .convert import (_optional_to_zero_based, _to_zero_based, bar_to_beat, beat_to_bar,
                      params_to_zero_based, to_one_based)
from .lom import path_to_zero_based, refs_to_zero_based, rewrite_paths
from .plugin_aliases import get_alias_for_param, get_categories, resolve_alias
from .plugin_cache import (_get_cached_external_plugins, _invalidate_external_plugin_cache,
                           _normalize_plugin_search_text, _plugin_match_score)
from .spec import HIDDEN_SPECS, SPECS_BY_NAME, TOOL_SPECS

logger = logging.getLogger("AbletonMCPUnified")

_ARRANGEMENT_TIP = "\nTip: use set_view(view='Arranger') to see changes in arrangement view."
MANUAL_TOOLS: Dict[str, Any] = {}


def manual(name: str):
    def deco(fn):
        fn.__name__ = name
        fn._spec = SPECS_BY_NAME[name]
        MANUAL_TOOLS[name] = fn
        return fn
    return deco


def _dumps(result: Any) -> str:
    return json.dumps(to_one_based(result), indent=2)


# ---------------------------------------------------------------- session

@manual("health_check")
def health_check() -> str:
    """Check if Ableton Live is connected and responsive; reports the Remote Script version and command count."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("health_check")
        return json.dumps({"connected": True, **result}, indent=2)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return json.dumps({"connected": False, "error": str(e)}, indent=2)


@manual("send_command")
def send_command(command: str, params: Dict[str, Any] = None) -> str:
    """Send any Remote Script command by name. Params ending in `_index` are 1-based and converted; `index` keeps -1 = append.
    See list_commands / docs/tools.md for the full command list (including commands without a dedicated tool)."""
    try:
        ableton = get_ableton_connection()
        wire = params_to_zero_based(params or {})
        result = ableton.send_command(command, wire)
        return _dumps(result)
    except Exception as e:
        logger.error(f"Error in send_command({command}): {e}")
        return f"Error in send_command({command}): {e}"


# ---------------------------------------------------------------- tracks

@manual("get_track_info")
def get_track_info(track_index: int) -> str:
    """Get detailed information about a track (1-based index): clip slots, devices, mute/solo/arm, volume, panning, is_group_track."""
    try:
        ableton = get_ableton_connection()
        ti = _to_zero_based(track_index, "track_index")
        result = ableton.send_command("get_track_info", {"track_index": ti})
        return _dumps(result)
    except Exception as e:
        logger.error(f"Error getting track info: {e}")
        return f"Error getting track info: {e}"


def _db_str(vol: float, unity: float = 0.85) -> str:
    return f"{20 * math.log10(vol / unity):+.1f} dB" if vol > 0 else "-inf dB"


def _pan_str(pan: float) -> str:
    return "center" if abs(pan) < 0.01 else f"{abs(pan):.2f} {'L' if pan < 0 else 'R'}"


@manual("get_track_volume")
def get_track_volume(track_index: int) -> str:
    """Get the current fader volume and panning of a track (1-based). Volume 0.85 = 0 dB unity. Return tracks come after session tracks."""
    try:
        ableton = get_ableton_connection()
        ti = _to_zero_based(track_index, "track_index")
        result = ableton.send_command("get_track_volume", {"track_index": ti})
        vol = result.get("volume", 0)
        pan = result.get("panning", 0)
        name = result.get("track_name", "?")
        return (f"Track {track_index} '{name}':\n"
                f"  Volume: {vol:.4f} (range {result.get('volume_min', 0):.2f}–{result.get('volume_max', 1):.2f}) ≈ {_db_str(vol)}\n"
                f"  Panning: {pan:.4f} ({_pan_str(pan)})\n"
                f"  Unity gain (0 dB) = 0.85")
    except Exception as e:
        logger.error(f"Error getting track volume: {e}")
        return f"Error getting track volume: {e}"


@manual("set_track_volume")
def set_track_volume(track_index: int, volume: float) -> str:
    """Set the mixer fader volume of a track (1-based). Normalized: 0.0 silence, 0.85 = 0 dB unity, 1.0 max (~+6 dB)."""
    try:
        ableton = get_ableton_connection()
        ti = _to_zero_based(track_index, "track_index")
        result = ableton.send_command("set_track_volume", {"track_index": ti, "volume": volume})
        vol = result.get("volume", volume)
        return f"Set track {track_index} '{result.get('track_name', '?')}' fader to {vol:.4f} (≈ {_db_str(vol)})"
    except Exception as e:
        logger.error(f"Error setting track volume: {e}")
        return f"Error setting track volume: {e}"


@manual("set_track_panning")
def set_track_panning(track_index: int, panning: float) -> str:
    """Set the mixer panning of a track (1-based): -1.0 full left, 0.0 center, +1.0 full right."""
    try:
        ableton = get_ableton_connection()
        ti = _to_zero_based(track_index, "track_index")
        result = ableton.send_command("set_track_panning", {"track_index": ti, "panning": panning})
        pan = result.get("panning", panning)
        return f"Set track {track_index} '{result.get('track_name', '?')}' panning to {pan:.4f} ({_pan_str(pan)})"
    except Exception as e:
        logger.error(f"Error setting track panning: {e}")
        return f"Error setting track panning: {e}"


@manual("get_track_deletion_status")
def get_track_deletion_status() -> str:
    """Check whether session tracks can be deleted right now (Live requires at least one session track)."""
    try:
        ableton = get_ableton_connection()
        info = ableton.send_command("get_session_info")
        track_count = info.get("track_count", 0)
        if track_count <= 1:
            return ("Track deletion blocked: 1 session track remaining. Ableton requires at least one session track. "
                    "Create a new track before deleting.")
        return (f"Track deletion available: {track_count} session tracks currently exist. You can delete up to "
                f"{max(0, track_count - 1)} more track(s) before hitting Ableton's minimum-track limit.")
    except Exception as e:
        logger.error(f"Error checking track deletion status: {e}")
        return f"Error checking track deletion status: {e}"


@manual("delete_track")
def delete_track(track_index: int = 0, track_name: str = "") -> str:
    """Delete a track by 1-based index (or by name when track_index is 0). Refuses to delete the last session track."""
    try:
        ableton = get_ableton_connection()
        info = ableton.send_command("get_session_info")
        track_count = info.get("track_count", 0)
        if track_count <= 1:
            return ("Error: Cannot delete the last remaining session track. Ableton must always have at least one track. "
                    "Create a new track before deleting.")
        if track_index <= 0:
            if not track_name:
                return "Error: provide either track_index (1-based) or track_name."
            matched_index = None
            for i in range(track_count):
                t = ableton.send_command("get_track_info", {"track_index": i})
                if t.get("name", "").lower() == track_name.lower():
                    matched_index = i
                    break
            if matched_index is None:
                return f"Error: No track named '{track_name}' found."
            ti = matched_index
        else:
            ti = _to_zero_based(track_index, "track_index")
        result = ableton.send_command("delete_track", {"track_index": ti})
        return "Deleted track '{0}'. {1} tracks remaining.".format(result.get("deleted_track", "unknown"),
                                                                  result.get("remaining_tracks", "?"))
    except Exception as e:
        logger.error(f"Error deleting track: {e}")
        return f"Error deleting track: {e}"


# ---------------------------------------------------------------- devices

@manual("get_device_parameters")
def get_device_parameters(track_index: int, device_index: int = 1, chain_index: int = 0,
                          category: str = "", show_all: bool = False) -> str:
    """List parameters of a device (1-based indices). Default is a category summary; pass category or show_all=True for details.
    Values are normalized 0.0-1.0 with display strings; known plugins get friendly aliases."""
    try:
        ableton = get_ableton_connection()
        ti = _to_zero_based(track_index, "track_index")
        di = _to_zero_based(device_index, "device_index")
        ci = _optional_to_zero_based(chain_index, "chain_index")
        result = ableton.send_command("get_device_parameters", {
            "track_index": ti, "device_index": di, "chain_index": ci, "show_all": True})
        device_name = result.get("device_name", "Unknown")
        params = result.get("parameters", [])
        param_count = result.get("parameter_count", len(params))
        for p in params:
            alias = get_alias_for_param(device_name, p["name"])
            if alias:
                p["alias"] = alias
        categories = get_categories(device_name)

        def categorize(p_name):
            if categories:
                for cat_name, prefixes in categories.items():
                    for prefix in prefixes:
                        if p_name.startswith(prefix):
                            return cat_name
            return "Other"

        if show_all or category:
            filtered = params
            if category:
                filtered = [p for p in params if categorize(p["name"]).lower() == category.lower()]
                if not filtered:
                    return "No parameters found in category '{0}'. Available categories: {1}".format(
                        category, ", ".join(sorted(set(categorize(p["name"]) for p in params))))
            lines = ["{0} (track {1}, device {2}) — {3} parameters".format(device_name, track_index, device_index, len(filtered)), ""]
            for p in filtered:
                alias_str = " ({0})".format(p["alias"]) if p.get("alias") else ""
                enabled_str = "" if p.get("is_enabled", True) else " [disabled]"
                lines.append("  {0}. {1}{2}: {3} (normalized {4}){5}".format(
                    p["index"] + 1, p["name"], alias_str, p.get("display_value", "?"), round(p["value"], 2), enabled_str))
            return "\n".join(lines)
        groups: Dict[str, list] = {}
        for p in params:
            groups.setdefault(categorize(p["name"]), []).append(p)
        lines = ["{0} (track {1}, device {2}) — {3} parameters total".format(device_name, track_index, device_index, param_count), ""]
        for cat_name, cat_params in groups.items():
            lines.append("  {0}: {1} parameters".format(cat_name, len(cat_params)))
        lines.append("")
        lines.append("Use category='<name>' or show_all=True for full details.")
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Error getting device parameters: {e}")
        return f"Error getting device parameters: {e}"


@manual("set_device_parameter")
def set_device_parameter(track_index: int, device_index: int = 1, chain_index: int = 0,
                         parameter_name: str = "", parameter_index: int = 0, value: float = 0.0) -> str:
    """Set a device parameter (1-based indices) by name (exact, partial or plugin alias) or by parameter_index. Value is normalized 0.0-1.0.
    Returns value, raw_value, display_value, min, max, old_value and the device/track names."""
    try:
        ableton = get_ableton_connection()
        ti = _to_zero_based(track_index, "track_index")
        di = _to_zero_based(device_index, "device_index")
        ci = _optional_to_zero_based(chain_index, "chain_index")
        pi = _optional_to_zero_based(parameter_index, "parameter_index")
        if not parameter_name and pi is None:
            return "Error: provide parameter_name or parameter_index (1-based)."
        resolved_name = parameter_name
        alias_used = None
        if parameter_name:
            info = ableton.send_command("get_device_parameters", {
                "track_index": ti, "device_index": di, "chain_index": ci, "show_all": False})
            real_name = resolve_alias(info.get("device_name", ""), parameter_name)
            if real_name:
                alias_used = parameter_name
                resolved_name = real_name
        result = ableton.send_command("set_device_parameter", {
            "track_index": ti, "device_index": di, "chain_index": ci,
            "parameter_name": resolved_name if resolved_name else None, "parameter_index": pi, "value": value})
        result = to_one_based(result)
        result.setdefault("track_index", track_index)
        result.setdefault("device_index", device_index)
        if chain_index:
            result.setdefault("chain_index", chain_index)
        if alias_used:
            result["alias_used"] = alias_used
        msg = "Set {0} to {1} (normalized {2})".format(result.get("parameter_name", "?"), result.get("display_value", "?"),
                                                     round(result.get("new_value", value), 2))
        if alias_used:
            msg += " [alias: {0}]".format(alias_used)
        if result.get("clamped"):
            msg += " (value was clamped to 0.0-1.0 range)"
        return msg + "\n" + json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error setting device parameter: {e}")
        return f"Error setting device parameter: {e}"


def _resolve_device_index(ableton, ti: int, track_index: int, device_index: int, device_name: str):
    """Return (0-based device index, error message)."""
    di = _optional_to_zero_based(device_index, "device_index")
    if device_name and di is None:
        info = ableton.send_command("get_track_info", {"track_index": ti})
        devices = info.get("devices", [])
        matches = [d for d in devices if d["name"].lower() == device_name.lower()]
        if len(matches) == 0:
            return None, "Error: Device '{0}' not found on track {1}".format(device_name, track_index)
        if len(matches) > 1:
            match_list = ", ".join("{0} (index {1})".format(d["name"], d["index"] + 1) for d in matches)
            return None, "Error: Multiple devices named '{0}' on track {1}: {2}".format(device_name, track_index, match_list)
        return matches[0]["index"], None
    return (0 if di is None else di), None


def _set_device_enabled_impl(track_index, device_index, device_name, chain_index, enabled) -> str:
    try:
        ableton = get_ableton_connection()
        ti = _to_zero_based(track_index, "track_index")
        ci = _optional_to_zero_based(chain_index, "chain_index")
        di, err = _resolve_device_index(ableton, ti, track_index, device_index, device_name)
        if err:
            return err
        result = ableton.send_command("set_device_enabled", {
            "track_index": ti, "device_index": di, "chain_index": ci, "enabled": enabled})
        state = "enabled" if result.get("is_active", enabled) else "disabled"
        return "{0} {1} (track {2}, device {3})".format(result.get("device_name", "?"), state, track_index, di + 1)
    except Exception as e:
        logger.error(f"Error toggling device: {e}")
        return f"Error toggling device: {e}"


@manual("set_device_enabled")
def set_device_enabled(track_index: int, device_index: int = 0, device_name: str = "", chain_index: int = 0,
                       enabled: bool = True) -> str:
    """Enable or bypass a device (1-based index or name; optional rack chain_index)."""
    return _set_device_enabled_impl(track_index, device_index, device_name, chain_index, enabled)


@manual("enable_device")
def enable_device(track_index: int, device_index: int = 0, device_name: str = "", chain_index: int = 0) -> str:
    """Enable (activate) a device on a track. device_index is 1-based; use 0 with device_name."""
    return _set_device_enabled_impl(track_index, device_index, device_name, chain_index, True)


@manual("disable_device")
def disable_device(track_index: int, device_index: int = 0, device_name: str = "", chain_index: int = 0) -> str:
    """Disable (bypass) a device on a track. device_index is 1-based; use 0 with device_name."""
    return _set_device_enabled_impl(track_index, device_index, device_name, chain_index, False)


@manual("get_chain_info")
def get_chain_info(track_index: int, device_index: int = 1, chain_index: int = 0) -> str:
    """List chains in a rack device (1-based indices), or devices within one chain when chain_index is given."""
    try:
        ableton = get_ableton_connection()
        ti = _to_zero_based(track_index, "track_index")
        di = _to_zero_based(device_index, "device_index")
        ci = _optional_to_zero_based(chain_index, "chain_index")
        result = ableton.send_command("get_chain_info", {"track_index": ti, "device_index": di, "chain_index": ci})
        if chain_index > 0:
            devices = result.get("devices", [])
            lines = ["Chain {0} '{1}' — {2} devices".format(chain_index, result.get("chain_name", "?"), len(devices)), ""]
            for d in devices:
                active = "" if d.get("is_active", True) else " [disabled]"
                lines.append("  {0}. {1} ({2}, {3} params){4}".format(
                    d["index"] + 1, d["name"], d["type"], d.get("parameter_count", "?"), active))
            return "\n".join(lines)
        chains = result.get("chains", [])
        lines = ["{0} — {1} chains".format(result.get("device_name", "?"), len(chains)), ""]
        for c in chains:
            mute_str = " [muted]" if c.get("mute") else ""
            solo_str = " [solo]" if c.get("solo") else ""
            dev_names = ", ".join(d["name"] for d in c.get("devices", []))
            lines.append("  {0}. {1}{2}{3}: {4} devices ({5})".format(
                c["index"] + 1, c["name"], mute_str, solo_str, c["device_count"], dev_names or "empty"))
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Error getting chain info: {e}")
        return f"Error getting chain info: {e}"


@manual("get_drum_pad_info")
def get_drum_pad_info(track_index: int, device_index: int = 1, pad_index: int = 0) -> str:
    """List filled pads of a Drum Rack (1-based indices), or detail one pad when pad_index is given."""
    try:
        ableton = get_ableton_connection()
        ti = _to_zero_based(track_index, "track_index")
        di = _to_zero_based(device_index, "device_index")
        pi = _optional_to_zero_based(pad_index, "pad_index")
        params = {"track_index": ti, "device_index": di}
        if pi is not None:
            params["pad_index"] = pi
        result = ableton.send_command("get_drum_pad_info", params)
        if pi is not None:
            return _dumps(result)
        pads = result.get("filled_pads", [])
        lines = ["{0} — {1} filled pads".format(result.get("device_name", "?"), len(pads)), ""]
        for pad in pads:
            mute_str = " [muted]" if pad.get("mute") else ""
            solo_str = " [solo]" if pad.get("solo") else ""
            dev_names = [d["name"] for chain in pad.get("chains", []) for d in chain.get("devices", [])]
            pad_no = " (pad {0})".format(pad["pad_index"] + 1) if "pad_index" in pad else ""
            lines.append("  Note {0}: {1}{2}{3}{4} → {5}".format(
                pad["note"], pad["name"], pad_no, mute_str, solo_str, ", ".join(dev_names) or "empty"))
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Error getting drum pad info: {e}")
        return f"Error getting drum pad info: {e}"


@manual("delete_device")
def delete_device(track_index: int, device_index: int = 0, device_name: str = "") -> str:
    """Delete a device from a track by 1-based index or by name."""
    try:
        ableton = get_ableton_connection()
        ti = _to_zero_based(track_index, "track_index")
        di, err = _resolve_device_index(ableton, ti, track_index, device_index, device_name)
        if err:
            return err
        result = ableton.send_command("delete_device", {"track_index": ti, "device_index": di})
        return "Deleted {0}. {1} devices remaining.".format(result.get("deleted_device", "device"),
                                                            result.get("remaining_devices", "?"))
    except Exception as e:
        logger.error(f"Error deleting device: {e}")
        return f"Error deleting device: {e}"


@manual("navigate_device_preset")
def navigate_device_preset(track_index: int, device_index: int = 1, chain_index: int = 0, direction: str = "next") -> str:
    """Navigate device presets: direction = next, previous or current (1-based indices)."""
    try:
        ableton = get_ableton_connection()
        ti = _to_zero_based(track_index, "track_index")
        di = _to_zero_based(device_index, "device_index")
        ci = _optional_to_zero_based(chain_index, "chain_index")
        result = ableton.send_command("navigate_preset", {
            "track_index": ti, "device_index": di, "chain_index": ci, "direction": direction})
        preset_name = result.get("preset_name", "?")
        preset_idx = result.get("preset_index", 0)
        preset_count = result.get("preset_count", 0)
        device_n = result.get("device_name", "?")
        if direction == "current":
            return "{0}: current preset is '{1}' ({2}/{3})".format(device_n, preset_name, preset_idx + 1, preset_count)
        return "{0}: loaded preset '{1}' ({2}/{3})".format(device_n, preset_name, preset_idx + 1, preset_count)
    except Exception as e:
        logger.error(f"Error navigating preset: {e}")
        return f"Error navigating preset: {e}"


@manual("batch_set_device_parameters")
def batch_set_device_parameters(track_index: int, device_index: int = 1, parameters: List[Dict[str, Any]] = None,
                                chain_index: int = 0, reliable: bool = False) -> str:
    """Set several parameters of one device at once (normalized 0.0-1.0, 1-based indices).
    Default is fire-and-forget UDP (no response); reliable=True uses TCP and returns per-parameter results."""
    try:
        ti = _to_zero_based(track_index, "track_index")
        di = _to_zero_based(device_index, "device_index")
        ci = _optional_to_zero_based(chain_index, "chain_index")
        wire_params = []
        for entry in parameters or []:
            item = {"value": entry.get("value", 0.0)}
            if entry.get("parameter_name"):
                item["parameter_name"] = entry["parameter_name"]
            if entry.get("parameter_index") is not None:
                item["parameter_index"] = _to_zero_based(int(entry["parameter_index"]), "parameter_index")
            wire_params.append(item)
        if not wire_params:
            return "Error: parameters must be a non-empty list of {parameter_index|parameter_name, value}."
        payload = {"track_index": ti, "device_index": di, "chain_index": ci, "parameters": wire_params}
        if reliable:
            result = get_ableton_connection().send_command("batch_set_device_parameters", payload)
            return _dumps(result)
        get_udp_sender().send("batch_set_device_parameters", payload)
        return "Sent {0} parameter updates via UDP to track {1}, device {2} (fire-and-forget; use reliable=True for results).".format(
            len(wire_params), track_index, device_index)
    except Exception as e:
        logger.error(f"Error in batch_set_device_parameters: {e}")
        return f"Error in batch_set_device_parameters: {e}"


# ---------------------------------------------------------------- browser

@manual("get_browser_tree")
def get_browser_tree(category_type: str = "all") -> str:
    """Get a hierarchical tree of browser categories ('all', 'instruments', 'sounds', 'drums', 'audio_effects', 'midi_effects', 'plugins')."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_browser_tree", {"category_type": category_type})
        if "available_categories" in result and len(result.get("categories", [])) == 0:
            return (f"No categories found for '{category_type}'. "
                    f"Available browser categories: {', '.join(result.get('available_categories', []))}")
        formatted_output = f"Browser tree for '{category_type}' (showing {result.get('total_folders', 0)} folders):\n\n"

        def format_tree(item, indent=0):
            output = ""
            if item:
                prefix = "  " * indent
                output += f"{prefix}• {item.get('name', 'Unknown')}"
                if item.get("path"):
                    output += f" (path: {item.get('path')})"
                if item.get("has_more", False):
                    output += " [...]"
                output += "\n"
                for child in item.get("children", []):
                    output += format_tree(child, indent + 1)
            return output

        for category in result.get("categories", []):
            formatted_output += format_tree(category) + "\n"
        return formatted_output
    except Exception as e:
        return _browser_error("Error getting browser tree", e)


def _browser_error(prefix: str, e: Exception) -> str:
    error_msg = str(e)
    logger.error(f"{prefix}: {error_msg}")
    if "Browser is not available" in error_msg:
        return "Error: The Ableton browser is not available. Make sure Ableton Live is fully loaded and try again."
    if "Could not access Live application" in error_msg:
        return "Error: Could not access the Ableton Live application. Make sure Ableton Live is running and the Remote Script is loaded."
    if "Unknown or unavailable category" in error_msg:
        return f"Error: {error_msg}. Please check the available categories using get_browser_tree."
    if "Path part" in error_msg and "not found" in error_msg:
        return f"Error: {error_msg}. Please check the path and try again."
    return f"{prefix}: {error_msg}"


@manual("get_browser_items_at_path")
def get_browser_items_at_path(path: str) -> str:
    """List browser items at 'category/folder/subfolder' (category aliases such as 'audio-effects' or 'vst3' are normalized)."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_browser_items_at_path", {"path": path})
        if "error" in result and "available_categories" in result:
            return (f"Error: {result.get('error', '')}\n"
                    f"Available browser categories: {', '.join(result.get('available_categories', []))}")
        return json.dumps(result, indent=2)
    except Exception as e:
        return _browser_error("Error getting browser items at path", e)


@manual("load_instrument_or_effect")
def load_instrument_or_effect(track_index: int, uri: str) -> str:
    """Load an instrument or effect onto a track (1-based) by browser URI."""
    try:
        ableton = get_ableton_connection()
        ti = _to_zero_based(track_index, "track_index")
        result = ableton.send_command("load_browser_item", {"track_index": ti, "item_uri": uri})
        if result.get("loaded", False):
            new_devices = result.get("new_devices", [])
            if new_devices:
                return f"Loaded instrument with URI '{uri}' on track {track_index}. New devices: {', '.join(new_devices)}"
            devices = result.get("devices_after", [])
            return f"Loaded instrument with URI '{uri}' on track {track_index}. Devices on track: {', '.join(devices)}"
        return f"Failed to load instrument with URI '{uri}'"
    except Exception as e:
        logger.error(f"Error loading instrument by URI: {e}")
        return f"Error loading instrument by URI: {e}"


@manual("load_drum_kit")
def load_drum_kit(track_index: int, rack_uri: str, kit_path: str) -> str:
    """Load a Drum Rack by URI onto a track (1-based), then the first loadable kit found at kit_path."""
    try:
        ableton = get_ableton_connection()
        ti = _to_zero_based(track_index, "track_index")
        result = ableton.send_command("load_browser_item", {"track_index": ti, "item_uri": rack_uri})
        if not result.get("loaded", False):
            return f"Failed to load drum rack with URI '{rack_uri}'"
        kit_result = ableton.send_command("get_browser_items_at_path", {"path": kit_path})
        if "error" in kit_result:
            return f"Loaded drum rack but failed to find drum kit: {kit_result.get('error')}"
        loadable_kits = [item for item in kit_result.get("items", []) if item.get("is_loadable", False)]
        if not loadable_kits:
            return f"Loaded drum rack but no loadable drum kits found at '{kit_path}'"
        ableton.send_command("load_browser_item", {"track_index": ti, "item_uri": loadable_kits[0].get("uri")})
        return f"Loaded drum rack and kit '{loadable_kits[0].get('name')}' on track {track_index}"
    except Exception as e:
        logger.error(f"Error loading drum kit: {e}")
        return f"Error loading drum kit: {e}"


@manual("list_external_plugins")
def list_external_plugins(query: str = "", max_results: int = 50, refresh_cache: bool = False) -> str:
    """List discovered external plugins (VST/AU), optionally filtered by a case-insensitive name query. Cached for 2 minutes."""
    try:
        ableton = get_ableton_connection()
        plugins = _get_cached_external_plugins(ableton, force_refresh=refresh_cache)
        if query:
            scored = [(s, p) for p in plugins for s in [_plugin_match_score(p.get("name", ""), query)] if s > 0]
            scored.sort(key=lambda x: (-x[0], _normalize_plugin_search_text(x[1].get("name", ""))))
            filtered = [item for _, item in scored]
        else:
            filtered = plugins
        if not filtered:
            return "No external plugins matched query '{0}'.".format(query) if query else "No external plugins were discovered."
        max_results = max(1, int(max_results))
        shown = filtered[:max_results]
        lines = ["External plugins discovered: {0} total, showing {1}".format(len(filtered), len(shown)), ""]
        for idx, plugin in enumerate(shown, start=1):
            lines.append("  {0}. {1} (path: {2})".format(idx, plugin.get("name", "Unknown"), plugin.get("path", "?")))
        if len(filtered) > len(shown):
            lines.append("")
            lines.append("Use max_results={0} (or a tighter query) to see more.".format(len(filtered)))
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Error listing external plugins: {e}")
        return f"Error listing external plugins: {e}"


@manual("load_external_plugin")
def load_external_plugin(track_index: int, plugin_name: str, exact_match: bool = False, refresh_cache: bool = False) -> str:
    """Load an external plugin onto a track (1-based) by name; exact_match=True requires an exact normalized name."""
    try:
        if not plugin_name or not plugin_name.strip():
            return "Error: plugin_name is required."
        ableton = get_ableton_connection()
        ti = _to_zero_based(track_index, "track_index")
        plugins = _get_cached_external_plugins(ableton, force_refresh=refresh_cache)
        scored = []
        for plugin in plugins:
            score = _plugin_match_score(plugin.get("name", ""), plugin_name)
            if exact_match and score < 1000:
                continue
            if score > 0:
                scored.append((score, plugin))
        scored.sort(key=lambda x: (-x[0], _normalize_plugin_search_text(x[1].get("name", ""))))
        if not scored:
            return ("No external plugin matched '{0}'. Try list_external_plugins(query='{0}') to inspect candidates.").format(plugin_name)
        top_score = scored[0][0]
        top_plugins = [plugin for score, plugin in scored if score == top_score]
        if len(top_plugins) > 1 and top_score < 1000:
            options = ", ".join(p.get("name", "?") for p in top_plugins[:5])
            return "Multiple plugins match '{0}': {1}. Please be more specific or set exact_match=True.".format(plugin_name, options)
        chosen = top_plugins[0]
        result = ableton.send_command("load_browser_item", {"track_index": ti, "item_uri": chosen.get("uri")})
        if result.get("loaded", False):
            return "Loaded external plugin '{0}' on track {1} (matched '{2}').".format(chosen.get("name", "?"), track_index, plugin_name)
        return "Failed to load external plugin '{0}'.".format(chosen.get("name", "?"))
    except Exception as e:
        logger.error(f"Error loading external plugin: {e}")
        return f"Error loading external plugin: {e}"


# ---------------------------------------------------------------- arrangement / cue points

def _get_time_signature():
    info = get_ableton_connection().send_command("get_session_info")
    return info.get("signature_numerator", 4), info.get("signature_denominator", 4)


def _convert_bar_to_beat(bar: int, beat: float = 0.0) -> float:
    if bar > 0:
        num, denom = _get_time_signature()
        return bar_to_beat(bar, num, denom)
    return beat


@manual("get_arrangement_info")
def get_arrangement_info(track_index: int = 0) -> str:
    """Get arrangement clips (bar positions) and transport state. track_index is 1-based; 0 = all tracks."""
    try:
        ableton = get_ableton_connection()
        idx = _optional_to_zero_based(track_index, "track_index")
        result = ableton.send_command("get_arrangement_info", {"track_index": idx if idx is not None else -1})
        transport = result.get("transport", {})
        num = transport.get("signature_numerator", 4)
        denom = transport.get("signature_denominator", 4)
        lines = ["=== Arrangement Info ==="]
        lines.append(f"Tempo: {transport.get('tempo')} BPM | Time Sig: {num}/{denom} | Playing: {transport.get('is_playing')} | "
                     f"Position: bar {beat_to_bar(transport.get('current_time', 0), num, denom)}")
        if transport.get("loop_enabled"):
            ls = transport.get("loop_start", 0)
            ll = transport.get("loop_length", 0)
            lines.append(f"Loop: bars {beat_to_bar(ls, num, denom)}-{beat_to_bar(ls + ll, num, denom)}")
        for t in result.get("tracks", []):
            clips = t.get("arrangement_clips", [])
            kind = "Group" if t.get("is_group_track") else ("MIDI" if t.get("is_midi") else "Audio")
            lines.append(f"\nTrack {t['index'] + 1}: {t['name']} ({kind}) — {len(clips)} clip(s)")
            for c in clips:
                muted = " [MUTED]" if c.get("muted") else ""
                lines.append(f"  {c.get('index', 0) + 1}. \"{c.get('name', '')}\" bars "
                             f"{beat_to_bar(c.get('start_time', 0), num, denom)}-{beat_to_bar(c.get('end_time', 0), num, denom)}{muted}")
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Error getting arrangement info: {e}")
        return f"Error getting arrangement info: {e}"


@manual("get_cue_points")
def get_cue_points() -> str:
    """List all cue points (locators) with 1-based cue index and bar position."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_cue_points")
        num, denom = _get_time_signature()
        cues = result.get("cue_points", [])
        if not cues:
            return "No cue points in this project."
        lines = ["=== Cue Points ==="]
        for i, cp in enumerate(cues):
            idx = cp.get("index", i) + 1
            lines.append(f"  {idx}. \"{cp.get('name', '')}\" — bar {beat_to_bar(cp.get('time', 0), num, denom)} (beat {cp.get('time', 0)})")
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Error getting cue points: {e}")
        return f"Error getting cue points: {e}"


@manual("set_song_time")
def set_song_time(bar: int = 0, beat: float = 0.0) -> str:
    """Jump playback to a bar (1-based; takes precedence) or to a raw beat position."""
    try:
        ableton = get_ableton_connection()
        time_val = _convert_bar_to_beat(bar, beat)
        ableton.send_command("set_song_time", {"time": time_val})
        num, denom = _get_time_signature()
        return f"Jumped to bar {beat_to_bar(time_val, num, denom)} (beat {time_val})"
    except Exception as e:
        logger.error(f"Error setting song time: {e}")
        return f"Error setting song time: {e}"


@manual("set_arrangement_loop")
def set_arrangement_loop(enabled: bool = True, start_bar: int = 0, end_bar: int = 0,
                         start_beat: float = 0.0, length_beats: float = 0.0) -> str:
    """Enable/disable the arrangement loop and set its region by 1-based bars (start_bar/end_bar) or by beats."""
    try:
        ableton = get_ableton_connection()
        num, denom = _get_time_signature()
        start = None
        length = None
        if start_bar > 0:
            start = bar_to_beat(start_bar, num, denom)
            if end_bar > start_bar:
                length = bar_to_beat(end_bar, num, denom) - start
        else:
            if start_beat > 0:
                start = start_beat
            if length_beats > 0:
                length = length_beats
        params: Dict[str, Any] = {"enabled": enabled}
        if start is not None:
            params["start"] = start
        if length is not None:
            params["length"] = length
        result = ableton.send_command("set_arrangement_loop", params)
        state = "enabled" if result.get("enabled") else "disabled"
        ls = result.get("start", 0)
        ll = result.get("length", 0)
        return f"Loop {state}: bars {beat_to_bar(ls, num, denom)}-{beat_to_bar(ls + ll, num, denom)} (beats {ls}-{ls + ll})"
    except Exception as e:
        logger.error(f"Error setting arrangement loop: {e}")
        return f"Error setting arrangement loop: {e}"


@manual("jump_to_cue_point")
def jump_to_cue_point(direction: str = "", name: str = "", cue_index: int = 0) -> str:
    """Jump to a cue point by direction ('next'/'prev'), by name, or by 1-based cue_index."""
    try:
        ableton = get_ableton_connection()
        params: Dict[str, Any] = {}
        if direction:
            params["direction"] = direction
        if name:
            params["name"] = name
        ci = _optional_to_zero_based(cue_index, "cue_index")
        if ci is not None:
            params["cue_index"] = ci
        result = ableton.send_command("jump_to_cue", params)
        return f"Jumped to cue point: {json.dumps(to_one_based(result))}"
    except Exception as e:
        logger.error(f"Error jumping to cue point: {e}")
        return f"Error jumping to cue point: {e}"


CUE_SETTLE_SECONDS = 0.6
CUE_POLL_SECONDS = 2.0


def _find_cue(ableton, time_val):
    for cp in ableton.send_command("get_cue_points").get("cue_points", []):
        if abs(cp.get("time", -1) - time_val) < 0.01:
            return cp
    return None


def _wait_for_cue(ableton, time_val, present: bool):
    """Live applies cue changes asynchronously; poll until the cue at time_val appears/disappears."""
    import time as _time
    deadline = _time.monotonic() + CUE_POLL_SECONDS
    while True:
        cue = _find_cue(ableton, time_val)
        if (cue is not None) == present:
            return cue
        if _time.monotonic() > deadline:
            return cue
        _time.sleep(0.1)


@manual("create_cue_point")
def create_cue_point(bar: int = 0, beat: float = 0.0, name: str = "") -> str:
    """Create a cue point at a bar (1-based) or beat position, optionally named.
    Moves the playhead first and waits for Live to settle (cue creation is asynchronous in Live)."""
    try:
        import time as _time
        ableton = get_ableton_connection()
        time_val = _convert_bar_to_beat(bar, beat)
        if _find_cue(ableton, time_val) is not None:
            return f"Error: a cue point already exists at beat {time_val}"
        ableton.send_command("set_song_time", {"time": time_val})
        _time.sleep(CUE_SETTLE_SECONDS)
        ableton.send_command("create_cue_point", {"time": time_val, "name": name})
        cue = _wait_for_cue(ableton, time_val, present=True)
        if cue is None:
            return f"Error: Live did not create a cue point at beat {time_val} (try again with playback stopped)"
        if name and cue.get("name") != name:
            ableton.send_command("live_set", {"path": "live_set cue_points %d" % cue["index"], "prop": "name", "value": name})
            cue = _find_cue(ableton, time_val) or cue
        return f"Created cue point {cue['index'] + 1} '{cue.get('name', name)}' at bar {bar if bar > 0 else '?'} (beat {time_val})"
    except Exception as e:
        logger.error(f"Error creating cue point: {e}")
        return f"Error creating cue point: {e}"


@manual("delete_cue_point")
def delete_cue_point(bar: int = 0, beat: float = 0.0, cue_index: int = 0) -> str:
    """Delete a cue point at a bar (1-based) / beat position, or by 1-based cue_index.
    Moves the playhead first and waits for Live to settle (cue deletion is asynchronous in Live)."""
    try:
        import time as _time
        ableton = get_ableton_connection()
        ci = _optional_to_zero_based(cue_index, "cue_index")
        if ci is not None:
            cues = ableton.send_command("get_cue_points").get("cue_points", [])
            if ci >= len(cues):
                return f"Error: cue_index {cue_index} out of range (1-{len(cues)})"
            time_val = cues[ci]["time"]
            label = f"cue point {cue_index} '{cues[ci].get('name', '')}'"
        else:
            time_val = _convert_bar_to_beat(bar, beat)
            label = f"cue point at bar {bar if bar > 0 else '?'} (beat {time_val})"
        cue = _find_cue(ableton, time_val)
        if cue is None:
            return f"Error: no cue point at beat {time_val}"
        ableton.send_command("set_song_time", {"time": time_val})
        _time.sleep(CUE_SETTLE_SECONDS)
        ableton.send_command("delete_cue_point", {"time": time_val})
        if _wait_for_cue(ableton, time_val, present=False) is not None:
            return f"Error: Live did not delete the {label}"
        return f"Deleted {label}"
    except Exception as e:
        logger.error(f"Error deleting cue point: {e}")
        return f"Error deleting cue point: {e}"


@manual("create_arrangement_midi_clip")
def create_arrangement_midi_clip(track_index: int, start_bar: int = 0, end_bar: int = 0, start_beat: float = 0.0,
                                 length_beats: float = 4.0, name: str = "") -> str:
    """Create an empty MIDI clip in the arrangement (track 1-based) at a bar or beat position."""
    try:
        ableton = get_ableton_connection()
        num, denom = _get_time_signature()
        if start_bar > 0:
            position = bar_to_beat(start_bar, num, denom)
            length = bar_to_beat(end_bar, num, denom) - position if end_bar > start_bar else length_beats
        else:
            position = start_beat
            length = length_beats
        ti = _to_zero_based(track_index, "track_index")
        result = ableton.send_command("create_arrangement_clip", {"track_index": ti, "position": position, "length": length})
        if name:
            try:
                clips = ableton.send_command("get_arrangement_info", {"track_index": ti}).get("tracks", [{}])[0].get("arrangement_clips", [])
                for c in clips:
                    if abs(c.get("start_time", -1) - position) < 0.01:
                        ableton.send_command("set_arrangement_clip_property", {
                            "track_index": ti, "clip_index": c["index"], "property": "name", "value": name})
                        break
            except Exception as e:  # naming is best-effort
                logger.warning(f"Could not name new arrangement clip: {e}")
        msg = f"Created MIDI clip on track {track_index} at bar {beat_to_bar(position, num, denom)}, length {length} beats"
        overlapped = result.get("overlapped_clips", [])
        if overlapped:
            msg += f"\nWarning: overlapped existing clips: {', '.join(overlapped)}"
        return msg + _ARRANGEMENT_TIP
    except Exception as e:
        logger.error(f"Error creating arrangement MIDI clip: {e}")
        return f"Error creating arrangement MIDI clip: {e}"


@manual("create_arrangement_audio_clip")
def create_arrangement_audio_clip(track_index: int, file_path: str, start_bar: int = 0, start_beat: float = 0.0) -> str:
    """Place an audio file as a clip in the arrangement (track 1-based)."""
    try:
        ableton = get_ableton_connection()
        position = _convert_bar_to_beat(start_bar, start_beat)
        ti = _to_zero_based(track_index, "track_index")
        ableton.send_command("create_arrangement_audio_clip", {"track_index": ti, "position": position, "file_path": file_path})
        return f"Created audio clip from '{file_path}' on track {track_index}" + _ARRANGEMENT_TIP
    except Exception as e:
        logger.error(f"Error creating arrangement audio clip: {e}")
        return f"Error creating arrangement audio clip: {e}"


@manual("duplicate_clip_to_arrangement")
def duplicate_clip_to_arrangement(track_index: int, clip_index: int, destination_bar: int = 0, destination_beat: float = 0.0) -> str:
    """Copy a session clip (1-based track/slot) to the arrangement at a bar or beat position."""
    try:
        ableton = get_ableton_connection()
        dest = _convert_bar_to_beat(destination_bar, destination_beat)
        ti = _to_zero_based(track_index, "track_index")
        ci = _to_zero_based(clip_index, "clip_index")
        ableton.send_command("duplicate_to_arrangement", {"track_index": ti, "clip_index": ci, "destination_time": dest})
        return f"Duplicated session clip to arrangement on track {track_index}" + _ARRANGEMENT_TIP
    except Exception as e:
        logger.error(f"Error duplicating clip to arrangement: {e}")
        return f"Error duplicating clip to arrangement: {e}"


@manual("delete_arrangement_clip")
def delete_arrangement_clip(track_index: int, clip_index: int = 0, clip_name: str = "") -> str:
    """Delete an arrangement clip by 1-based position or by name."""
    try:
        ableton = get_ableton_connection()
        ti = _to_zero_based(track_index, "track_index")
        params: Dict[str, Any] = {"track_index": ti}
        if clip_name:
            params["clip_name"] = clip_name
        elif clip_index > 0:
            params["clip_index"] = _to_zero_based(clip_index, "clip_index")
        else:
            return "Error: provide clip_index or clip_name"
        ableton.send_command("delete_arrangement_clip", params)
        ref = f"'{clip_name}'" if clip_name else f"#{clip_index}"
        return f"Deleted arrangement clip {ref} on track {track_index}" + _ARRANGEMENT_TIP
    except Exception as e:
        logger.error(f"Error deleting arrangement clip: {e}")
        return f"Error deleting arrangement clip: {e}"


@manual("set_arrangement_clip_property")
def set_arrangement_clip_property(track_index: int, clip_index: int = 1, clip_name: str = "", name: str = "",
                                  muted: Optional[bool] = None, color: Optional[int] = None, looping: Optional[bool] = None,
                                  loop_start: Optional[float] = None, loop_end: Optional[float] = None,
                                  gain: Optional[float] = None, pitch_coarse: Optional[int] = None,
                                  pitch_fine: Optional[float] = None, warping: Optional[bool] = None,
                                  warp_mode: Optional[int] = None) -> str:
    """Set properties on an arrangement clip (1-based track/clip). Only the given properties are changed."""
    try:
        ableton = get_ableton_connection()
        ti = _to_zero_based(track_index, "track_index")
        ci = _to_zero_based(clip_index, "clip_index") if clip_index > 0 else 0
        props = {"name": name, "muted": muted, "color": color, "looping": looping, "loop_start": loop_start,
                 "loop_end": loop_end, "gain": gain, "pitch_coarse": pitch_coarse, "pitch_fine": pitch_fine,
                 "warping": warping, "warp_mode": warp_mode}
        changes = []
        for prop_name, value in props.items():
            if value is not None and value != "":
                params: Dict[str, Any] = {"track_index": ti, "clip_index": ci, "property": prop_name, "value": value}
                if clip_name:
                    params["clip_name"] = clip_name
                ableton.send_command("set_arrangement_clip_property", params)
                changes.append(f"{prop_name}={value}")
        if not changes:
            return "No properties specified to change."
        ref = f"'{clip_name}'" if clip_name else f"clip {clip_index}"
        return f"Updated {ref} on track {track_index}: {', '.join(changes)}"
    except Exception as e:
        logger.error(f"Error setting arrangement clip property: {e}")
        return f"Error setting arrangement clip property: {e}"


@manual("manage_clip_automation")
def manage_clip_automation(track_index: int, clip_index: int = 1, clip_name: str = "", action: str = "create",
                           parameter_name: str = "volume") -> str:
    """Create or clear automation envelopes on an arrangement clip (action: create, clear, clear_all)."""
    try:
        ableton = get_ableton_connection()
        ti = _to_zero_based(track_index, "track_index")
        ci = _to_zero_based(clip_index, "clip_index") if clip_index > 0 else 0
        ableton.send_command("manage_clip_automation", {
            "track_index": ti, "clip_index": ci, "action": action, "parameter_name": parameter_name})
        if action == "clear_all":
            return f"Cleared all automation on clip {clip_index}, track {track_index}"
        return f"Automation {action}: {parameter_name} on clip {clip_index}, track {track_index}"
    except Exception as e:
        logger.error(f"Error managing clip automation: {e}")
        return f"Error managing clip automation: {e}"


# ---------------------------------------------------------------- generic Live Object Model

@manual("live_get")
def live_get(path: str = "live_set", props: Optional[List[str]] = None) -> str:
    """Read a Live object by path with 1-based indices, e.g. 'live_set tracks 1 devices 2 parameters 3'.
    Without props returns a summary of the object; with props returns those attribute values."""
    try:
        ableton = get_ableton_connection()
        params: Dict[str, Any] = {"path": path_to_zero_based(path)}
        if props:
            params["props"] = list(props)
        result = ableton.send_command("live_get", params)
        return json.dumps(rewrite_paths(result), indent=2)
    except Exception as e:
        logger.error(f"Error in live_get: {e}")
        return f"Error in live_get: {e}"


@manual("live_children")
def live_children(path: str = "live_set") -> str:
    """Enumerate the properties, lists (with lengths), child objects and methods of the Live object at path (1-based indices)."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("live_children", {"path": path_to_zero_based(path)})
        return json.dumps(rewrite_paths(result), indent=2)
    except Exception as e:
        logger.error(f"Error in live_children: {e}")
        return f"Error in live_children: {e}"


@manual("live_set")
def live_set(path: str, prop: str, value: Any) -> str:
    """Set a property on the Live object at path (1-based indices), e.g. live_set('live_set', 'tempo', 128).
    Object-valued properties take a reference: value={"$path": "live_set tracks 1 devices 1 drum_pads 47"}."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("live_set", {"path": path_to_zero_based(path), "prop": prop,
                                                   "value": refs_to_zero_based(value)})
        return json.dumps(rewrite_paths(result), indent=2)
    except Exception as e:
        logger.error(f"Error in live_set: {e}")
        return f"Error in live_set: {e}"


@manual("live_call")
def live_call(path: str, method: str, args: Optional[List[Any]] = None, timeout: float = 10.0) -> str:
    """Call a method on the Live object at path (1-based indices) with JSON-primitive args,
    e.g. live_call('live_set', 'create_midi_track', [-1]). An arg of {"$path": "live_set tracks 1 devices 2"}
    (1-based) is resolved to that Live object, e.g. live_call('live_set view', 'select_device', [{"$path": ...}]).
    timeout in seconds (max 60)."""
    try:
        ableton = get_ableton_connection()
        t = max(1.0, min(60.0, float(timeout)))
        result = ableton.send_command("live_call", {
            "path": path_to_zero_based(path), "method": method, "args": refs_to_zero_based(list(args or [])),
            "_timeout": t}, timeout=t + 5.0)
        return json.dumps(rewrite_paths(result), indent=2)
    except Exception as e:
        logger.error(f"Error in live_call: {e}")
        return f"Error in live_call: {e}"


# ---------------------------------------------------------------- registration

def register(mcp) -> List[str]:
    names = []
    for spec in TOOL_SPECS:
        if not spec.manual:
            continue
        fn = MANUAL_TOOLS.get(spec.name)
        if fn is None:
            raise RuntimeError(f"spec row {spec.name} is manual=True but tools_manual.py has no implementation")
        mcp.tool(name=spec.name)(fn)
        names.append(spec.name)
        for alias in spec.deprecated_aliases:
            alias_fn = _alias_of(fn, alias, spec.name)
            mcp.tool(name=alias)(alias_fn)
            names.append(alias)
    return names


def _alias_of(fn, alias: str, canonical: str):
    import functools

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    wrapper.__name__ = alias
    wrapper.__qualname__ = alias
    wrapper.__doc__ = f"[Deprecated alias of {canonical}] " + (fn.__doc__ or "")
    return wrapper

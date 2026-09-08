"""External plugin discovery with a short-lived cache."""
from __future__ import annotations

import re
import threading
import time
from typing import Any, Dict, List

_EXTERNAL_PLUGIN_CACHE_TTL_SECONDS = 120.0
_external_plugin_cache_lock = threading.Lock()
_external_plugin_cache: Dict[str, Any] = {"plugins": None, "built_at": 0.0}


def _invalidate_external_plugin_cache() -> None:
    with _external_plugin_cache_lock:
        _external_plugin_cache["plugins"] = None
        _external_plugin_cache["built_at"] = 0.0


def _normalize_plugin_search_text(value: str) -> str:
    if not value:
        return ""
    cleaned = re.sub(r"[\s\-_]+", " ", value.strip().lower())
    return re.sub(r"\s+", " ", cleaned)


def _plugin_match_score(plugin_name: str, query: str) -> int:
    normalized_name = _normalize_plugin_search_text(plugin_name)
    normalized_query = _normalize_plugin_search_text(query)
    if not normalized_query:
        return 1
    if normalized_name == normalized_query:
        return 1000
    if normalized_name.startswith(normalized_query):
        return 900
    query_tokens = [t for t in normalized_query.split(" ") if t]
    if query_tokens and all(token in normalized_name for token in query_tokens):
        return 700 + sum(len(t) for t in query_tokens)
    if normalized_query in normalized_name:
        return 600 + len(normalized_query)
    return 0


def _collect_external_plugins_from_root(ableton, root_path: str, max_depth: int = 8,
                                        max_visited_paths: int = 2000) -> List[Dict[str, Any]]:
    stack: List[tuple[str, int]] = [(root_path, 0)]
    visited: set[str] = set()
    plugins: List[Dict[str, Any]] = []
    while stack:
        current_path, depth = stack.pop()
        if current_path in visited:
            continue
        visited.add(current_path)
        if len(visited) > max_visited_paths:
            raise RuntimeError("Plugin traversal exceeded safety limit ({0} paths).".format(max_visited_paths))
        result = ableton.send_command("get_browser_items_at_path", {"path": current_path})
        if "error" in result:
            if depth == 0:
                raise ValueError(result.get("error", "Unknown browser root error"))
            continue
        for item in result.get("items", []):
            name = (item.get("name") or "").strip()
            if not name:
                continue
            child_path = "{0}/{1}".format(current_path, name)
            is_folder = bool(item.get("is_folder", False))
            is_loadable = bool(item.get("is_loadable", False))
            uri = item.get("uri")
            if is_loadable and uri:
                plugins.append({"name": name, "uri": uri, "path": child_path,
                                "is_device": bool(item.get("is_device", False)), "root": root_path})
            if is_folder and depth < max_depth:
                stack.append((child_path, depth + 1))
    return plugins


def _discover_external_plugins(ableton) -> List[Dict[str, Any]]:
    candidate_roots = ["plugins", "vst3", "vst2", "au", "plug-ins"]
    discovered_any_root = False
    errors: List[str] = []
    for root in candidate_roots:
        try:
            found = _collect_external_plugins_from_root(ableton, root_path=root)
            discovered_any_root = True
            if not found:
                continue
            found.sort(key=lambda p: _normalize_plugin_search_text(p.get("name", "")))
            return found
        except Exception as e:
            errors.append("{0}: {1}".format(root, str(e)))
    if discovered_any_root:
        return []
    raise ValueError("Could not discover external plugins. Tried roots: {0}. Last errors: {1}".format(
        ", ".join(candidate_roots), " | ".join(errors) if errors else "none"))


def _get_cached_external_plugins(ableton, force_refresh: bool = False) -> List[Dict[str, Any]]:
    now = time.monotonic()
    with _external_plugin_cache_lock:
        cached_plugins = _external_plugin_cache.get("plugins")
        built_at = float(_external_plugin_cache.get("built_at", 0.0) or 0.0)
        if not force_refresh and cached_plugins is not None and (now - built_at) <= _EXTERNAL_PLUGIN_CACHE_TTL_SECONDS:
            return list(cached_plugins)
    discovered = _discover_external_plugins(ableton)
    with _external_plugin_cache_lock:
        _external_plugin_cache["plugins"] = list(discovered)
        _external_plugin_cache["built_at"] = time.monotonic()
    return discovered

"""Build FastMCP tools from the spec table.

For each non-manual, non-hidden ``ToolSpec`` a function with a real signature is
created (so FastMCP derives the JSON schema), whose body converts 1-based index
params to 0-based, sends the command, rewrites indices in the response back to
1-based and echoes the requested indices.
"""
from __future__ import annotations

import inspect
import json
import logging
from typing import Any, Callable, Dict, List, Optional

from .connection import get_ableton_connection
from .convert import _optional_to_zero_based, _to_zero_based, to_one_based
from .spec import REQUIRED, Param, ToolSpec, TOOL_SPECS

logger = logging.getLogger("AbletonMCPUnified")

_TYPE_MAP = {
    "int": int, "float": float, "str": str, "bool": bool, "list": List[Any], "list[int]": List[int],
    "list[str]": List[str], "list[dict]": List[Dict[str, Any]], "dict": Dict[str, Any], "any": Any,
}


def annotation_for(param: Param):
    base = _TYPE_MAP[param.type]
    if param.default is None:
        return Optional[base]
    return base


def build_params(spec: ToolSpec, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Convert tool kwargs (1-based) into Remote Script params (0-based)."""
    out: Dict[str, Any] = {}
    for p in spec.params:
        if p.name not in kwargs:
            continue
        value = kwargs[p.name]
        wire = p.rs_name or p.name
        if p.index:
            out[wire] = _to_zero_based(value, p.name)
        elif p.optional_index:
            converted = _optional_to_zero_based(value, p.name)
            if converted is None:
                if p.rs_default is not None:
                    out[wire] = p.rs_default
                # otherwise omit so the RS default applies
            else:
                out[wire] = converted
        elif p.index_list:
            out[wire] = [_to_zero_based(v, p.name) for v in value]
        else:
            if value is None and p.default is None:
                continue  # unset optional -> omit
            out[wire] = value
    return out


def format_result(spec: ToolSpec, result: Any, kwargs: Dict[str, Any]) -> str:
    """Rewrite indices to 1-based, echo requested indices, render."""
    result = to_one_based(result)
    if isinstance(result, dict):
        for p in spec.params:
            if (p.index or p.optional_index) and p.name in kwargs and p.name not in result:
                value = kwargs[p.name]
                if isinstance(value, int) and value > 0:
                    result[p.name] = value
    if spec.format == "json":
        return json.dumps(result, indent=2)
    return str(result)


def run_spec(spec: ToolSpec, kwargs: Dict[str, Any]) -> str:
    try:
        params = build_params(spec, kwargs)
        ableton = get_ableton_connection()
        result = ableton.send_command(spec.command, params)
        return format_result(spec, result, kwargs)
    except Exception as e:
        logger.error(f"Error in {spec.name}: {e}")
        return f"Error in {spec.name}: {e}"


def make_tool_function(spec: ToolSpec, name: Optional[str] = None, deprecated_of: Optional[str] = None) -> Callable[..., str]:
    """Create a function whose signature mirrors ``spec.params`` and which runs ``run_spec``."""
    fn_name = name or spec.name
    param_names = [p.name for p in spec.params]

    def tool(**kwargs) -> str:
        for p in spec.params:
            if p.name not in kwargs and p.default is not REQUIRED:
                kwargs[p.name] = p.default
        return run_spec(spec, kwargs)

    sig_params = []
    annotations: Dict[str, Any] = {}
    for p in spec.params:
        ann = annotation_for(p)
        default = inspect.Parameter.empty if p.default is REQUIRED else p.default
        sig_params.append(inspect.Parameter(p.name, inspect.Parameter.KEYWORD_ONLY, default=default, annotation=ann))
        annotations[p.name] = ann
    annotations["return"] = str
    tool.__signature__ = inspect.Signature(sig_params, return_annotation=str)  # type: ignore[attr-defined]
    tool.__annotations__ = annotations
    tool.__name__ = fn_name
    tool.__qualname__ = fn_name
    doc = spec.doc.strip()
    param_docs = [f"- {p.name}: {p.doc}" for p in spec.params if p.doc]
    idx = [p.name for p in spec.params if p.index or p.optional_index or p.index_list]
    if idx:
        param_docs.append(f"Indices ({', '.join(idx)}) are 1-based" + (" (0 = unset)" if any(p.optional_index for p in spec.params) else "") + ".")
    if param_docs:
        doc += "\n\n" + "\n".join(param_docs)
    if deprecated_of:
        doc = f"[Deprecated alias of {deprecated_of}] " + doc
    tool.__doc__ = doc
    tool._spec = spec  # type: ignore[attr-defined]
    tool._param_names = param_names  # type: ignore[attr-defined]
    return tool


def build_generated_tools() -> Dict[str, Callable[..., str]]:
    tools: Dict[str, Callable[..., str]] = {}
    for spec in TOOL_SPECS:
        if spec.manual:
            continue
        tools[spec.name] = make_tool_function(spec)
        for alias in spec.deprecated_aliases:
            tools[alias] = make_tool_function(spec, name=alias, deprecated_of=spec.name)
    return tools


def register(mcp) -> List[str]:
    names = []
    for name, fn in build_generated_tools().items():
        mcp.tool(name=name)(fn)
        names.append(name)
    return names

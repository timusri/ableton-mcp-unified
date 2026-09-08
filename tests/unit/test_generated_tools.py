"""Every generated tool converts 1-based indices to 0-based and rewrites responses back."""
import inspect
import json

import pytest

from ableton_mcp.spec import REQUIRED, TOOL_SPECS
from ableton_mcp.tools_generated import build_generated_tools, build_params, format_result

GENERATED = [s for s in TOOL_SPECS if not s.manual]
TOOLS = build_generated_tools()


def _sample_kwargs(spec, index_value=1):
    kwargs = {}
    for p in spec.params:
        if p.index or p.optional_index:
            kwargs[p.name] = index_value
        elif p.index_list:
            kwargs[p.name] = [index_value, index_value + 1]
        elif p.default is REQUIRED:
            kwargs[p.name] = {"int": 1, "float": 0.5, "str": "x", "bool": True, "list": [], "list[int]": [1],
                              "list[str]": ["a"], "list[dict]": [{}], "dict": {}, "any": 1}[p.type]
    return kwargs


@pytest.mark.parametrize("spec", GENERATED, ids=lambda s: s.name)
def test_index_one_becomes_zero(spec):
    params = build_params(spec, _sample_kwargs(spec, 1))
    for p in spec.params:
        wire = p.rs_name or p.name
        if p.index:
            assert params[wire] == 0
        elif p.optional_index:
            assert params[wire] == 0
        elif p.index_list:
            assert params[wire] == [0, 1]


@pytest.mark.parametrize("spec", [s for s in GENERATED if any(p.index for p in s.params)], ids=lambda s: s.name)
def test_index_zero_is_rejected(spec):
    with pytest.raises(ValueError, match="must be >= 1"):
        build_params(spec, _sample_kwargs(spec, 0))


@pytest.mark.parametrize("spec", [s for s in GENERATED if any(p.optional_index for p in s.params)], ids=lambda s: s.name)
def test_optional_index_zero_is_unset(spec):
    kwargs = _sample_kwargs(spec, 1)
    for p in spec.params:
        if p.optional_index:
            kwargs[p.name] = 0
    params = build_params(spec, kwargs)
    for p in spec.params:
        if p.optional_index:
            wire = p.rs_name or p.name
            if p.rs_default is None:
                assert wire not in params
            else:
                assert params[wire] == p.rs_default


@pytest.mark.parametrize("spec", GENERATED, ids=lambda s: s.name)
def test_signature_matches_spec(spec):
    fn = TOOLS[spec.name]
    sig = inspect.signature(fn)
    assert list(sig.parameters) == [p.name for p in spec.params]
    for p in spec.params:
        param = sig.parameters[p.name]
        if p.default is REQUIRED:
            assert param.default is inspect.Parameter.empty
        else:
            assert param.default == p.default
    assert fn.__doc__


def test_response_indices_rewritten_and_echoed():
    spec = next(s for s in GENERATED if s.name == "set_track_mute")
    out = json.loads(format_result(spec, {"mute": True, "devices": [{"index": 0}]}, {"track_index": 3, "mute": True}))
    assert out["track_index"] == 3
    assert out["devices"][0]["index"] == 1


def test_tool_sends_converted_params(mock_conn):
    mock_conn.send_command.return_value = {"track_index": 1, "mute": True}
    out = TOOLS["set_track_mute"](track_index=2, mute=True)
    mock_conn.send_command.assert_called_once_with("set_track_mute", {"track_index": 1, "mute": True})
    assert json.loads(out)["track_index"] == 2


def test_deprecated_alias_is_registered():
    assert "focus_view" in TOOLS and TOOLS["focus_view"].__doc__.startswith("[Deprecated alias of set_view]")


def test_rs_name_rewrite(mock_conn):
    TOOLS["set_view"](view="Session")
    mock_conn.send_command.assert_called_once_with("set_view", {"view_name": "Session"})


def test_errors_are_returned_as_text(mock_conn):
    mock_conn.send_command.side_effect = Exception("boom")
    assert TOOLS["set_tempo"](tempo=120.0).startswith("Error in set_tempo: boom")

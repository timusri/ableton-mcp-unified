"""Shared fixtures: stub Live's _Framework so the Remote Script imports outside Live."""
import os
import sys
import types
from unittest.mock import MagicMock

import pytest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, ROOT)


class _StubControlSurface(object):
    def __init__(self, c_instance):
        pass

    def log_message(self, msg):
        pass

    def show_message(self, msg):
        pass

    def disconnect(self):
        pass

    def song(self):
        return None


if "_Framework" not in sys.modules:
    _framework = types.ModuleType("_Framework")
    _cs_module = types.ModuleType("_Framework.ControlSurface")
    _cs_module.ControlSurface = _StubControlSurface
    sys.modules["_Framework"] = _framework
    sys.modules["_Framework.ControlSurface"] = _cs_module

from tests.fixtures.mock_ableton import MockSong  # noqa: E402
from AbletonMCPUnified import AbletonMCP  # noqa: E402


def make_script(song=None, browser=None):
    """Create an AbletonMCP instance without running ControlSurface.__init__ or opening sockets."""
    script = AbletonMCP.__new__(AbletonMCP)
    script._song = song if song is not None else MockSong()
    script.log_message = lambda _msg: None
    script.show_message = lambda _msg: None
    app = types.SimpleNamespace(browser=browser, view=MagicMock())
    app.view.is_view_visible = lambda name: True
    script.application = lambda: app
    return script


@pytest.fixture
def song():
    return MockSong()


@pytest.fixture
def script(song):
    return make_script(song)


@pytest.fixture
def dispatch(script):
    """Send a wire command through the registry dispatch and return the response dict."""
    def _dispatch(command_type, **params):
        return script._process_command({"type": command_type, "params": params})
    return _dispatch


@pytest.fixture
def mock_conn(mocker):
    """Patch the connection used by generated + manual tools; returns the MagicMock connection."""
    conn = MagicMock()
    conn.send_command.return_value = {}
    mocker.patch("ableton_mcp.tools_generated.get_ableton_connection", return_value=conn)
    mocker.patch("ableton_mcp.tools_manual.get_ableton_connection", return_value=conn)
    return conn

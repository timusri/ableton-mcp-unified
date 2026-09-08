"""Handler mixins. Import order = MRO order; keep _base first and lom last."""
from ._base import BaseHandlers
from .session import SessionHandlers
from .tracks import TrackHandlers
from .clips import ClipHandlers
from .notes import NoteHandlers
from .scenes import SceneHandlers
from .devices import DeviceHandlers
from .chains import ChainHandlers
from .browser import BrowserHandlers
from .routing import RoutingHandlers
from .view import ViewHandlers
from .recording import RecordingHandlers
from .arrangement import ArrangementHandlers
from .cue_points import CuePointHandlers
from .lom import LomHandlers

ALL_MIXINS = (
    BaseHandlers, SessionHandlers, TrackHandlers, ClipHandlers, NoteHandlers, SceneHandlers,
    DeviceHandlers, ChainHandlers, BrowserHandlers, RoutingHandlers, ViewHandlers,
    RecordingHandlers, ArrangementHandlers, CuePointHandlers, LomHandlers,
)

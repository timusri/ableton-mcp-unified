"""_notes_api: prefer the Live 11 note API, fall back to the legacy one."""
from AbletonMCPUnified.handlers import _notes_api as api


class FakeMidiNote(object):
    def __init__(self, pitch, start_time, duration, velocity, mute=False):
        self.pitch = pitch
        self.start_time = start_time
        self.duration = duration
        self.velocity = velocity
        self.mute = mute
        self.note_id = id(self)
        self.probability = 0.5  # extra Live 11 data that must survive


class NewApiClip(object):
    """Mimics a Live 11+ clip: no set_notes, notes are objects."""
    length = 4.0
    end_marker = 4.0

    def __init__(self, notes):
        self.notes = list(notes)
        self.calls = []

    def get_notes_extended(self, from_pitch, pitch_span, from_time, time_span):
        self.calls.append(("get", from_pitch, pitch_span, from_time, time_span))
        return tuple(self.notes)

    def add_new_notes(self, specs):
        self.calls.append(("add", len(specs)))
        self.notes.extend(FakeMidiNote(*s) if isinstance(s, tuple) else s for s in specs)

    def remove_notes_extended(self, from_pitch, pitch_span, from_time, time_span):
        self.calls.append(("remove", from_pitch, pitch_span, from_time, time_span))
        self.notes = []

    def apply_note_modifications(self, notes):
        self.calls.append(("apply", len(notes)))


class LegacyClip(object):
    length = 4.0

    def __init__(self, notes):
        self.notes = list(notes)
        self.calls = []

    def get_notes(self, from_time, from_pitch, time_span, pitch_span):
        return tuple(self.notes)

    def set_notes(self, notes):
        self.calls.append("set")
        self.notes.extend(notes)

    def remove_notes(self, from_time, from_pitch, time_span, pitch_span):
        self.calls.append("remove")
        self.notes = []


def test_read_notes_new_api_returns_tuples():
    clip = NewApiClip([FakeMidiNote(60, 0.0, 0.5, 100)])
    assert api.read_all_notes(clip) == [(60, 0.0, 0.5, 100, False)]
    assert clip.calls[0][0] == "get"
    # argument order of get_notes_extended is (pitch, pitch_span, time, time_span)
    assert clip.calls[0][1:3] == (0, 128)


def test_add_notes_uses_add_new_notes():
    clip = NewApiClip([])
    assert api.add_notes(clip, [(60, 0.0, 1.0, 90, False), (64, 1.0, 1.0, 90, False)]) == 2
    assert clip.calls == [("add", 2)]
    assert len(clip.notes) == 2


def test_modify_notes_keeps_note_objects_and_extra_data():
    note = FakeMidiNote(60, 0.0, 0.5, 100)
    clip = NewApiClip([note])
    out = api.modify_notes(clip, lambda p, s, d, v, m: (p + 12, s, d, v, m))
    assert out == [(72, 0.0, 0.5, 100, False)]
    assert note.pitch == 72 and note.probability == 0.5
    assert ("apply", 1) in clip.calls
    assert not any(c[0] == "remove" for c in clip.calls)


def test_remove_notes_new_api_argument_order():
    clip = NewApiClip([FakeMidiNote(60, 0.0, 0.5, 100)])
    api.remove_notes(clip, 1.0, 36, 2.0, 12)
    assert clip.calls[-1] == ("remove", 36, 12, 1.0, 2.0)


def test_legacy_fallback():
    clip = LegacyClip([(60, 0.0, 0.5, 100, False)])
    assert api.read_all_notes(clip) == [(60, 0.0, 0.5, 100, False)]
    out = api.modify_notes(clip, lambda p, s, d, v, m: (p, s, d, 64, m))
    assert out == [(60, 0.0, 0.5, 64, False)]
    assert clip.calls == ["remove", "set"]
    api.add_notes(clip, [(62, 1.0, 0.5, 80, False)])
    assert clip.calls[-1] == "set"

"""Note read/write helpers that prefer the Live 11+ note API.

Live 11 replaced ``set_notes`` / ``get_selected_notes`` / ``remove_notes`` with
``add_new_notes`` / ``get_notes_extended`` / ``remove_notes_extended`` /
``apply_note_modifications``.  Live shows a blocking "custom MIDI Remote Script
uses an older process to modify MIDI notes" dialog whenever a script edits an
existing clip through the legacy calls, and the legacy calls drop the extra
per-note data (probability, velocity deviation, release velocity).

Every handler goes through these helpers.  The new API is used when the clip
offers it; the legacy API is the fallback for Live 10 and for the unit-test mock.

Note tuples everywhere in this package are ``(pitch, start_time, duration,
velocity, mute)``.
"""

try:  # only importable inside Live
    import Live
except ImportError:  # pragma: no cover - unit tests run outside Live
    Live = None


def _has_new_api(clip):
    return hasattr(clip, "get_notes_extended") and hasattr(clip, "add_new_notes")


def _to_tuple(note):
    """Accept a legacy 5-tuple or a Live MidiNote/MidiNoteSpecification object."""
    if isinstance(note, (tuple, list)):
        return (note[0], note[1], note[2], note[3], note[4] if len(note) > 4 else False)
    return (
        int(note.pitch),
        float(note.start_time),
        float(note.duration),
        int(round(note.velocity)),
        bool(note.mute),
    )


def _to_spec(note):
    """Build a MidiNoteSpecification (or keep the tuple when Live is unavailable)."""
    pitch, start_time, duration, velocity, mute = note
    if Live is not None and hasattr(Live, "Clip") and hasattr(Live.Clip, "MidiNoteSpecification"):
        return Live.Clip.MidiNoteSpecification(
            pitch=int(pitch),
            start_time=float(start_time),
            duration=float(duration),
            velocity=float(velocity),
            mute=bool(mute),
        )
    return (int(pitch), float(start_time), float(duration), int(velocity), bool(mute))


def read_notes(clip, from_time=0.0, from_pitch=0, time_span=None, pitch_span=128):
    """Return notes in the range as a list of 5-tuples."""
    if time_span is None:
        time_span = max(float(clip.length), 0.0)
    if _has_new_api(clip):
        raw = clip.get_notes_extended(int(from_pitch), int(pitch_span), float(from_time), float(time_span))
    elif hasattr(clip, "get_notes"):
        raw = clip.get_notes(float(from_time), int(from_pitch), float(time_span), int(pitch_span))
    else:
        clip.select_all_notes()
        raw = clip.get_selected_notes()
        clip.deselect_all_notes()
    return [_to_tuple(n) for n in raw]


def read_all_notes(clip):
    """Return every note in the clip, including notes past the loop end."""
    span = float(clip.length)
    try:  # notes may sit beyond the loop brace; widen the read window
        span = max(span, float(clip.end_marker))
    except Exception:
        pass
    return read_notes(clip, 0.0, 0, span if span > 0 else 1e6, 128)


def add_notes(clip, notes):
    """Add 5-tuple notes to the clip without touching existing notes."""
    notes = [tuple(n) for n in notes]
    if not notes:
        return 0
    if _has_new_api(clip):
        clip.add_new_notes(tuple(_to_spec(n) for n in notes))
    else:
        clip.set_notes(tuple(notes))
    return len(notes)


def remove_notes(clip, from_time=0.0, from_pitch=0, time_span=None, pitch_span=128):
    """Remove notes in the range."""
    if time_span is None:
        time_span = float(clip.length)
    if hasattr(clip, "remove_notes_extended"):
        clip.remove_notes_extended(int(from_pitch), int(pitch_span), float(from_time), float(time_span))
    else:
        clip.remove_notes(float(from_time), int(from_pitch), float(time_span), int(pitch_span))


def modify_notes(clip, transform):
    """Apply ``transform(pitch, start, duration, velocity, mute) -> 5-tuple`` to every note.

    With the new API the notes keep their identity and extra data
    (``apply_note_modifications``); otherwise the clip is cleared and rewritten.
    Returns the list of resulting 5-tuples.
    """
    if _has_new_api(clip) and hasattr(clip, "apply_note_modifications"):
        span = float(clip.length)
        try:
            span = max(span, float(clip.end_marker))
        except Exception:
            pass
        raw = clip.get_notes_extended(0, 128, 0.0, span if span > 0 else 1e6)
        results = []
        for note in raw:
            pitch, start, duration, velocity, mute = transform(*_to_tuple(note))
            note.pitch = int(pitch)
            note.start_time = float(start)
            note.duration = float(duration)
            note.velocity = float(velocity)
            note.mute = bool(mute)
            results.append((int(pitch), float(start), float(duration), int(velocity), bool(mute)))
        clip.apply_note_modifications(raw)
        return results
    original = read_all_notes(clip)
    results = [tuple(transform(*n)) for n in original]
    remove_notes(clip, 0.0, 0, float(clip.length), 128)
    if results:
        clip.set_notes(tuple(results))
    return results

"""Note command handlers.

The ``cmd_*`` adapters are registered through registry.py.
"""
import random
import traceback

from ..registry import command
from . import _notes_api as notes_api


class NoteHandlers(object):

    def _get_clip_notes(self, track_index, clip_index):
        """Get all notes from a clip"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]

            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip index out of range")

            clip_slot = track.clip_slots[clip_index]

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip = clip_slot.clip

            if not clip.is_midi_clip:
                raise Exception("Clip is not a MIDI clip")

            notes_data = notes_api.read_all_notes(clip)

            notes = []
            for note in notes_data:
                notes.append({
                    "pitch": note[0],
                    "start_time": note[1],
                    "duration": note[2],
                    "velocity": note[3],
                    "mute": note[4]
                })

            result = {
                "track_index": track_index,
                "clip_index": clip_index,
                "clip_name": clip.name,
                "length": clip.length,
                "note_count": len(notes),
                "notes": notes
            }
            return result
        except Exception as e:
            self.log_message("Error getting clip notes: " + str(e))
            raise
    def _add_notes_to_clip(self, track_index, clip_index, notes):
        """Add MIDI notes to a clip"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")
            
            track = self._song.tracks[track_index]
            
            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip index out of range")
            
            clip_slot = track.clip_slots[clip_index]
            
            if not clip_slot.has_clip:
                raise Exception("No clip in slot")
            
            clip = clip_slot.clip
            
            # Convert note data to Live's format
            live_notes = []
            for note in notes:
                pitch = note.get("pitch", 60)
                start_time = note.get("start_time", 0.0)
                duration = note.get("duration", 0.25)
                velocity = note.get("velocity", 100)
                mute = note.get("mute", False)
                
                live_notes.append((pitch, start_time, duration, velocity, mute))
            
            notes_api.add_notes(clip, live_notes)
            
            result = {
                "note_count": len(notes)
            }
            return result
        except Exception as e:
            self.log_message("Error adding notes to clip: " + str(e))
            raise
    def _remove_notes(self, track_index, clip_index, from_time, time_span, from_pitch, pitch_span):
        """Remove notes from a clip within a range"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]

            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip index out of range")

            clip_slot = track.clip_slots[clip_index]

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip = clip_slot.clip

            if not clip.is_midi_clip:
                raise Exception("Clip is not a MIDI clip")

            notes_api.remove_notes(clip, from_time, from_pitch, time_span, pitch_span)

            result = {
                "removed": True,
                "track_index": track_index,
                "clip_index": clip_index,
                "from_time": from_time,
                "time_span": time_span,
                "from_pitch": from_pitch,
                "pitch_span": pitch_span
            }
            return result
        except Exception as e:
            self.log_message("Error removing notes: " + str(e))
            raise
    def _remove_all_notes(self, track_index, clip_index):
        """Remove all notes from a clip"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]

            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip index out of range")

            clip_slot = track.clip_slots[clip_index]

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip = clip_slot.clip

            if not clip.is_midi_clip:
                raise Exception("Clip is not a MIDI clip")

            notes_api.remove_notes(clip)

            result = {
                "removed": True,
                "track_index": track_index,
                "clip_index": clip_index
            }
            return result
        except Exception as e:
            self.log_message("Error removing all notes: " + str(e))
            raise
    def _transpose_notes(self, track_index, clip_index, semitones):
        """Transpose all notes in a clip by a number of semitones"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]

            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip index out of range")

            clip_slot = track.clip_slots[clip_index]

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip = clip_slot.clip

            if not clip.is_midi_clip:
                raise Exception("Clip is not a MIDI clip")

            transposed_notes = notes_api.modify_notes(
                clip,
                lambda pitch, start, duration, velocity, mute: (
                    max(0, min(127, pitch + semitones)), start, duration, velocity, mute))

            result = {
                "transposed": True,
                "track_index": track_index,
                "clip_index": clip_index,
                "semitones": semitones,
                "note_count": len(transposed_notes)
            }
            return result
        except Exception as e:
            self.log_message("Error transposing notes: " + str(e))
            raise
    def _get_scale_notes(self, root, scale_type):
        """Get notes in a scale"""
        try:
            # Scale intervals (semitones from root)
            scales = {
                "major": [0, 2, 4, 5, 7, 9, 11],
                "minor": [0, 2, 3, 5, 7, 8, 10],
                "dorian": [0, 2, 3, 5, 7, 9, 10],
                "phrygian": [0, 1, 3, 5, 7, 8, 10],
                "lydian": [0, 2, 4, 6, 7, 9, 11],
                "mixolydian": [0, 2, 4, 5, 7, 9, 10],
                "locrian": [0, 1, 3, 5, 6, 8, 10],
                "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
                "melodic_minor": [0, 2, 3, 5, 7, 9, 11],
                "pentatonic_major": [0, 2, 4, 7, 9],
                "pentatonic_minor": [0, 3, 5, 7, 10],
                "blues": [0, 3, 5, 6, 7, 10],
                "chromatic": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
            }

            scale = scales.get(scale_type.lower(), scales["major"])
            notes = [(root + interval) % 12 for interval in scale]
            midi_notes = [root + interval for interval in scale]

            note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

            result = {
                "root": root,
                "root_name": note_names[root % 12],
                "scale_type": scale_type,
                "intervals": scale,
                "notes": notes,
                "note_names": [note_names[n] for n in notes],
                "midi_notes_octave": midi_notes
            }
            return result
        except Exception as e:
            self.log_message("Error getting scale notes: " + str(e))
            raise
    def _quantize_clip_notes(self, track_index, clip_index, grid):
        """Quantize notes in a clip to a grid"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]

            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip index out of range")

            clip_slot = track.clip_slots[clip_index]

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip = clip_slot.clip

            if not clip.is_midi_clip:
                raise Exception("Clip is not a MIDI clip")

            quantized_notes = notes_api.modify_notes(
                clip,
                lambda pitch, start, duration, velocity, mute: (
                    pitch, round(start / grid) * grid, duration, velocity, mute))

            result = {
                "quantized": True,
                "note_count": len(quantized_notes),
                "grid": grid
            }
            return result
        except Exception as e:
            self.log_message("Error quantizing clip notes: " + str(e))
            raise
    def _humanize_clip_timing(self, track_index, clip_index, amount):
        """Add random timing variation to notes"""
        try:
            import random

            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]

            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip index out of range")

            clip_slot = track.clip_slots[clip_index]

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip = clip_slot.clip

            if not clip.is_midi_clip:
                raise Exception("Clip is not a MIDI clip")

            # amount is in beats, e.g., 0.1 = up to a tenth of a beat either way
            humanized_notes = notes_api.modify_notes(
                clip,
                lambda pitch, start, duration, velocity, mute: (
                    pitch, max(0, start + (random.random() - 0.5) * 2 * amount), duration, velocity, mute))

            result = {
                "humanized": True,
                "note_count": len(humanized_notes),
                "amount": amount
            }
            return result
        except Exception as e:
            self.log_message("Error humanizing clip timing: " + str(e))
            raise
    def _humanize_clip_velocity(self, track_index, clip_index, amount):
        """Add random velocity variation to notes"""
        try:
            import random

            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]

            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip index out of range")

            clip_slot = track.clip_slots[clip_index]

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip = clip_slot.clip

            if not clip.is_midi_clip:
                raise Exception("Clip is not a MIDI clip")

            # amount is 0-1, e.g., 0.1 = +/-10% velocity variation
            humanized_notes = notes_api.modify_notes(
                clip,
                lambda pitch, start, duration, velocity, mute: (
                    pitch, start, duration,
                    max(1, min(127, velocity + int((random.random() - 0.5) * 2 * amount * 127))), mute))

            result = {
                "humanized": True,
                "note_count": len(humanized_notes),
                "amount": amount
            }
            return result
        except Exception as e:
            self.log_message("Error humanizing clip velocity: " + str(e))
            raise
    def _generate_bassline(self, track_index, clip_index, root, scale_type, length):
        """Generate a bassline pattern"""
        try:
            import random

            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]

            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip index out of range")

            clip_slot = track.clip_slots[clip_index]

            # Create clip if it doesn't exist
            if not clip_slot.has_clip:
                clip_slot.create_clip(length)

            clip = clip_slot.clip

            # Clear existing notes
            notes_api.remove_notes(clip)

            # Get scale notes
            scales = {
                "major": [0, 2, 4, 5, 7, 9, 11],
                "minor": [0, 2, 3, 5, 7, 8, 10],
                "dorian": [0, 2, 3, 5, 7, 9, 10],
                "phrygian": [0, 1, 3, 5, 7, 8, 10],
                "pentatonic_minor": [0, 3, 5, 7, 10],
                "blues": [0, 3, 5, 6, 7, 10]
            }
            scale = scales.get(scale_type.lower(), scales["minor"])

            notes = []
            beats = int(length)
            current_note = root

            for beat in range(beats):
                # Root note on beat 1
                if beat % 4 == 0:
                    notes.append((root, float(beat), 0.5, 100, False))
                else:
                    # Choose from scale
                    interval = random.choice(scale)
                    note = root + interval
                    # Vary octave occasionally
                    if random.random() > 0.7:
                        note += 12
                    duration = random.choice([0.25, 0.5, 0.75])
                    velocity = random.randint(80, 110)
                    notes.append((note, float(beat), duration, velocity, False))

                # Add some 8th note movement
                if random.random() > 0.5:
                    interval = random.choice(scale)
                    note = root + interval
                    notes.append((note, beat + 0.5, 0.25, random.randint(70, 90), False))

            notes_api.add_notes(clip, notes)

            result = {
                "generated": True,
                "root": root,
                "scale_type": scale_type,
                "length": length,
                "note_count": len(notes)
            }
            return result
        except Exception as e:
            self.log_message("Error generating bassline: " + str(e))
            raise
    def _get_notes_in_range(self, track_index, clip_index, start_time, end_time, pitch_start=0, pitch_end=127):
        """Get MIDI notes within time and pitch range"""
        try:
            clip = list(self._song.tracks)[track_index].clip_slots[clip_index].clip
            if not clip.is_midi_clip:
                return {"error": "Not a MIDI clip"}
            notes = notes_api.read_notes(clip, start_time, pitch_start, end_time - start_time, pitch_end - pitch_start + 1)
            return {
                "notes": [
                    {"pitch": n[0], "start": n[1], "duration": n[2], "velocity": n[3], "mute": n[4]}
                    for n in notes
                ],
                "count": len(notes)
            }
        except Exception as e:
            return {"error": str(e)}
    def _quantize_clip(self, track_index, clip_index, quantize_to, amount=1.0):
        """Quantize clip to grid"""
        try:
            clip = list(self._song.tracks)[track_index].clip_slots[clip_index].clip
            if not clip.is_midi_clip:
                return {"error": "Not a MIDI clip"}
            # quantize_to: 0.25 = 1/16, 0.5 = 1/8, 1.0 = 1/4, etc.
            clip.quantize(quantize_to, amount)
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    def _deselect_all_notes(self, track_index, clip_index):
        """Deselect all notes in clip"""
        try:
            clip = list(self._song.tracks)[track_index].clip_slots[clip_index].clip
            if not clip.is_midi_clip:
                return {"error": "Not a MIDI clip"}
            clip.deselect_all_notes()
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    def _set_clip_notes(self, track_index, clip_index, notes):
        """Replace all notes in clip"""
        try:
            clip = list(self._song.tracks)[track_index].clip_slots[clip_index].clip
            if not clip.is_midi_clip:
                return {"error": "Not a MIDI clip"}
            notes_api.remove_notes(clip)
            note_tuples = tuple(
                (n['pitch'], n['start_time'], n['duration'], n['velocity'], n.get('mute', False))
                for n in notes
            )
            notes_api.add_notes(clip, note_tuples)
            return {"success": True, "count": len(notes)}
        except Exception as e:
            return {"error": str(e)}
    def _move_clip_notes(self, track_index, clip_index, time_delta, pitch_delta, start_time=0, end_time=None, pitch_start=0, pitch_end=127):
        """Move notes in clip by time and/or pitch delta"""
        try:
            clip = list(self._song.tracks)[track_index].clip_slots[clip_index].clip
            if not clip.is_midi_clip:
                return {"error": "Not a MIDI clip"}
            if end_time is None:
                end_time = clip.length
            # Get notes in range
            notes = notes_api.read_notes(clip, start_time, pitch_start, end_time - start_time, pitch_end - pitch_start + 1)
            if not notes:
                return {"moved": 0}
            # Remove old
            notes_api.remove_notes(clip, start_time, pitch_start, end_time - start_time, pitch_end - pitch_start + 1)
            # Add shifted
            new_notes = tuple(
                (max(0, min(127, n[0] + pitch_delta)), max(0, n[1] + time_delta), n[2], n[3], n[4])
                for n in notes
            )
            notes_api.add_notes(clip, new_notes)
            return {"moved": len(notes)}
        except Exception as e:
            return {"error": str(e)}
    # ---- command adapters (generated from the original dispatch chain) ----

    @command("get_clip_notes")
    def cmd_get_clip_notes(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._get_clip_notes(track_index, clip_index)

    @command("get_notes_in_range")
    def cmd_get_notes_in_range(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        start_time = params.get("start_time", 0)
        end_time = params.get("end_time", 4)
        pitch_start = params.get("pitch_start", 0)
        pitch_end = params.get("pitch_end", 127)
        return self._get_notes_in_range(track_index, clip_index, start_time, end_time, pitch_start, pitch_end)

    @command("get_scale_notes")
    def cmd_get_scale_notes(self, params):
        root = params.get("root", 0)
        scale_type = params.get("scale_type", "major")
        return self._get_scale_notes(root, scale_type)

    @command("add_notes_to_clip", modifying=True)
    def cmd_add_notes_to_clip(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        notes = params.get("notes", [])
        return self._add_notes_to_clip(track_index, clip_index, notes)

    @command("remove_notes", modifying=True)
    def cmd_remove_notes(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        from_time = params.get("from_time", 0.0)
        time_span = params.get("time_span", 4.0)
        from_pitch = params.get("from_pitch", 0)
        pitch_span = params.get("pitch_span", 128)
        return self._remove_notes(track_index, clip_index, from_time, time_span, from_pitch, pitch_span)

    @command("remove_all_notes", modifying=True)
    def cmd_remove_all_notes(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._remove_all_notes(track_index, clip_index)

    @command("transpose_notes", modifying=True)
    def cmd_transpose_notes(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        semitones = params.get("semitones", 0)
        return self._transpose_notes(track_index, clip_index, semitones)

    @command("quantize_clip_notes", modifying=True)
    def cmd_quantize_clip_notes(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        grid = params.get("grid", 0.25)
        return self._quantize_clip_notes(track_index, clip_index, grid)

    @command("humanize_clip_timing", modifying=True)
    def cmd_humanize_clip_timing(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        amount = params.get("amount", 0.1)
        return self._humanize_clip_timing(track_index, clip_index, amount)

    @command("humanize_clip_velocity", modifying=True)
    def cmd_humanize_clip_velocity(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        amount = params.get("amount", 0.1)
        return self._humanize_clip_velocity(track_index, clip_index, amount)

    @command("generate_bassline", modifying=True)
    def cmd_generate_bassline(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        root = params.get("root", 36)
        scale_type = params.get("scale_type", "minor")
        length = params.get("length", 4.0)
        return self._generate_bassline(track_index, clip_index, root, scale_type, length)

    @command("quantize_clip", modifying=True)
    def cmd_quantize_clip(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        quantize_to = params.get("quantize_to", 0.25)
        amount = params.get("amount", 1.0)
        return self._quantize_clip(track_index, clip_index, quantize_to, amount)

    @command("deselect_all_notes", modifying=True)
    def cmd_deselect_all_notes(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._deselect_all_notes(track_index, clip_index)

    @command("set_clip_notes", modifying=True)
    def cmd_set_clip_notes(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        notes = params.get("notes", [])
        return self._set_clip_notes(track_index, clip_index, notes)

    @command("move_clip_notes", modifying=True)
    def cmd_move_clip_notes(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        time_delta = params.get("time_delta", 0)
        pitch_delta = params.get("pitch_delta", 0)
        return self._move_clip_notes(track_index, clip_index, time_delta, pitch_delta)


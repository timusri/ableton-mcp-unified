"""Arrangement command handlers.

The ``cmd_*`` adapters are registered through registry.py.
"""
import random
import traceback

from ..registry import command
from . import _notes_api as notes_api


class ArrangementHandlers(object):

    def _get_arrangement_length(self):
        """Get the length of the arrangement"""
        try:
            result = {
                "length": self._song.last_event_time if hasattr(self._song, 'last_event_time') else 0,
                "loop_start": self._song.loop_start,
                "loop_length": self._song.loop_length,
                "loop_enabled": self._song.loop if hasattr(self._song, 'loop') else False
            }
            return result
        except Exception as e:
            self.log_message("Error getting arrangement length: " + str(e))
            raise
    def _get_arrangement_clip_info(self, clip):
        """Serialize a Clip object to ArrangementClipInfo dict."""
        try:
            return {
                "name": clip.name,
                "start_time": clip.start_time,
                "end_time": clip.end_time,
                "length": clip.end_time - clip.start_time,
                "is_midi": clip.is_midi_clip,
                "is_audio": clip.is_audio_clip,
                "muted": clip.muted,
                "color": clip.color,
                "looping": clip.looping,
                "loop_start": clip.loop_start,
                "loop_end": clip.loop_end,
            }
        except Exception as e:
            self.log_message("Error getting arrangement clip info: " + str(e))
            return {"name": "unknown", "error": str(e)}
    def _get_transport_info(self):
        """Serialize Song transport state to TransportInfo dict."""
        try:
            return {
                "is_playing": self._song.is_playing,
                "tempo": self._song.tempo,
                "signature_numerator": self._song.signature_numerator,
                "signature_denominator": self._song.signature_denominator,
                "current_time": self._song.current_song_time,
                "song_length": self._song.song_length,
                "loop_enabled": self._song.loop,
                "loop_start": self._song.loop_start,
                "loop_length": self._song.loop_length,
                "arrangement_overdub": self._song.arrangement_overdub,
                "back_to_arranger": self._song.back_to_arranger,
            }
        except Exception as e:
            self.log_message("Error getting transport info: " + str(e))
            raise
    def _resolve_arrangement_clip(self, track_index, clip_index=None, clip_name=None):
        """Resolve an arrangement clip by index or name.

        Returns (track, clip) tuple.
        """
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index {0} out of range (0-{1})".format(
                track_index, len(self._song.tracks) - 1))

        track = self._song.tracks[track_index]
        clips = track.arrangement_clips

        if clip_name:
            matches = [(i, c) for i, c in enumerate(clips) if c.name == clip_name]
            if len(matches) == 0:
                raise ValueError("No arrangement clip named '{0}' on track '{1}'".format(
                    clip_name, track.name))
            if len(matches) > 1:
                raise ValueError("Ambiguous: {0} clips named '{1}' on track '{2}'".format(
                    len(matches), clip_name, track.name))
            return track, matches[0][1]

        if clip_index is None:
            raise ValueError("Either clip_index or clip_name must be provided")

        if clip_index < 0 or clip_index >= len(clips):
            raise IndexError("Clip index {0} out of range (0-{1}) on track '{2}'".format(
                clip_index, len(clips) - 1, track.name))

        return track, clips[clip_index]
    def _check_overlap(self, track, position, length):
        """Return list of clip names that overlap with [position, position+length)."""
        overlapped = []
        end = position + length
        for clip in track.arrangement_clips:
            if clip.start_time < end and clip.end_time > position:
                overlapped.append(clip.name or "(unnamed)")
        return overlapped
    def _get_arrangement_info(self, track_index):
        """Get arrangement clips and transport for one or all tracks."""
        try:
            transport = self._get_transport_info()
            tracks_data = []

            if track_index == -1:
                tracks = list(enumerate(self._song.tracks))
            else:
                if track_index < 0 or track_index >= len(self._song.tracks):
                    raise IndexError("Track index out of range")
                tracks = [(track_index, self._song.tracks[track_index])]

            for idx, track in tracks:
                is_group = bool(getattr(track, "is_foldable", False))
                if is_group and track_index == -1:
                    continue

                clips = []
                if not is_group:
                    for ci, clip in enumerate(track.arrangement_clips):
                        clip_info = self._get_arrangement_clip_info(clip)
                        clip_info["index"] = ci
                        clips.append(clip_info)

                tracks_data.append({
                    "index": idx,
                    "name": track.name,
                    "is_midi": track.has_midi_input,
                    "is_audio": track.has_audio_input,
                    "is_group_track": is_group,
                    "arrangement_clips": clips,
                    "clip_count": len(clips),
                })

            return {"transport": transport, "tracks": tracks_data}
        except Exception as e:
            self.log_message("Error getting arrangement info: " + str(e))
            raise
    def _validate_not_return_or_master(self, track_index):
        """Raise if track is a return or master track."""
        track = self._song.tracks[track_index]
        # Return tracks and master track are separate in the Live API,
        # but if accessed via tracks list they are regular tracks.
        # Check by comparing against return_tracks and master_track.
        for rt in self._song.return_tracks:
            if track == rt:
                raise ValueError("Cannot create arrangement clips on return track '{0}'".format(track.name))
        if track == self._song.master_track:
            raise ValueError("Cannot create arrangement clips on master track")
    def _create_arrangement_clip(self, track_index, position, length):
        """Create MIDI clip in arrangement."""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")
            self._validate_not_return_or_master(track_index)
            track = self._song.tracks[track_index]
            overlapped = self._check_overlap(track, position, length)
            track.create_midi_clip(position, length)
            # Find the newly created clip
            result = {"start_time": position, "length": length, "is_midi": True}
            for clip in track.arrangement_clips:
                if abs(clip.start_time - position) < 0.01:
                    result = self._get_arrangement_clip_info(clip)
                    break
            result["overlapped_clips"] = overlapped
            return result
        except Exception as e:
            self.log_message("Error creating arrangement clip: " + str(e))
            raise
    def _create_arrangement_audio_clip(self, track_index, position, file_path):
        """Create audio clip in arrangement from file."""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")
            self._validate_not_return_or_master(track_index)
            track = self._song.tracks[track_index]
            track.create_audio_clip(file_path, position)
            # Find the newly created clip
            result = {"start_time": position, "file_path": file_path, "is_audio": True}
            for clip in track.arrangement_clips:
                if abs(clip.start_time - position) < 0.01:
                    result = self._get_arrangement_clip_info(clip)
                    break
            return result
        except Exception as e:
            self.log_message("Error creating arrangement audio clip: " + str(e))
            raise
    def _duplicate_to_arrangement(self, track_index, clip_index, destination_time):
        """Duplicate a session clip to arrangement."""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")
            track = self._song.tracks[track_index]
            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip slot index out of range")
            slot = track.clip_slots[clip_index]
            if not slot.has_clip:
                raise ValueError("No clip in slot {0}".format(clip_index))
            clip = slot.clip
            track.duplicate_clip_to_arrangement(clip, destination_time)
            # Find the duplicated clip
            result = {"start_time": destination_time, "duplicated": True}
            for arr_clip in track.arrangement_clips:
                if abs(arr_clip.start_time - destination_time) < 0.01:
                    result = self._get_arrangement_clip_info(arr_clip)
                    result["duplicated"] = True
                    break
            return result
        except Exception as e:
            self.log_message("Error duplicating to arrangement: " + str(e))
            raise
    def _add_notes_to_arrangement_clip(self, track_index, clip_index, notes):
        """Add MIDI notes to an arrangement clip."""
        try:
            track, clip = self._resolve_arrangement_clip(track_index, clip_index)
            if not clip.is_midi_clip:
                raise ValueError("Clip is not a MIDI clip")
            live_notes = []
            for note in notes:
                pitch = note.get("pitch", 60)
                start_time = note.get("start_time", 0.0)
                duration = note.get("duration", 0.25)
                velocity = note.get("velocity", 100)
                mute = note.get("mute", False)
                live_notes.append((pitch, start_time, duration, velocity, mute))
            notes_api.add_notes(clip, live_notes)
            return {"note_count": len(notes)}
        except Exception as e:
            self.log_message("Error adding notes to arrangement clip: " + str(e))
            raise
    def _delete_arrangement_clip(self, track_index, clip_index=None, clip_name=None):
        """Delete an arrangement clip."""
        try:
            track, clip = self._resolve_arrangement_clip(track_index, clip_index, clip_name)
            track.delete_clip(clip)
            return {"deleted": True}
        except Exception as e:
            self.log_message("Error deleting arrangement clip: " + str(e))
            raise
    def _set_arrangement_clip_property(self, track_index, clip_index, property_name, value):
        """Set a property on an arrangement clip."""
        try:
            ALLOWED = ("name", "muted", "color", "looping", "loop_start", "loop_end",
                       "gain", "pitch_coarse", "pitch_fine", "warping", "warp_mode")
            if property_name not in ALLOWED:
                raise ValueError("Property '{0}' not allowed. Allowed: {1}".format(
                    property_name, ", ".join(ALLOWED)))
            track, clip = self._resolve_arrangement_clip(track_index, clip_index)
            setattr(clip, property_name, value)
            return {"property": property_name, "value": getattr(clip, property_name)}
        except Exception as e:
            self.log_message("Error setting arrangement clip property: " + str(e))
            raise
    def _manage_clip_automation(self, track_index, clip_index, action, parameter_name=""):
        """Create or clear automation envelopes."""
        try:
            track, clip = self._resolve_arrangement_clip(track_index, clip_index)
            if action == "clear_all":
                clip.clear_all_envelopes()
                return {"action": "clear_all", "done": True}
            # Find the parameter
            param = None
            # Check mixer device first
            mixer = track.mixer_device
            for p in [mixer.volume, mixer.panning]:
                if p.name.lower() == parameter_name.lower():
                    param = p
                    break
            # Check sends
            if param is None:
                for send in mixer.sends:
                    if send.name.lower() == parameter_name.lower():
                        param = send
                        break
            # Check track devices
            if param is None:
                for device in track.devices:
                    for p in device.parameters:
                        if p.name.lower() == parameter_name.lower():
                            param = p
                            break
                    if param:
                        break
            if param is None:
                raise ValueError("Parameter '{0}' not found on track '{1}'".format(
                    parameter_name, track.name))
            if action == "create":
                clip.create_automation_envelope(param)
                return {"action": "create", "parameter": param.name, "done": True}
            elif action == "clear":
                clip.clear_envelope(param)
                return {"action": "clear", "parameter": param.name, "done": True}
            else:
                raise ValueError("Unknown action: " + action)
        except Exception as e:
            self.log_message("Error managing clip automation: " + str(e))
            raise
    # ---- unified additions ----

    def _set_arrangement_loop(self, enabled=True, start=None, length=None, end=None):
        """Set arrangement loop state and region (accepts start+length or start+end)."""
        try:
            self._song.loop = enabled
            if start is not None:
                self._song.loop_start = start
            if length is None and end is not None:
                length = end - self._song.loop_start
            if length is not None:
                self._song.loop_length = length
            loop_start = self._song.loop_start
            loop_length = self._song.loop_length
            return {
                "enabled": self._song.loop,
                "start": loop_start,
                "length": loop_length,
                "end": loop_start + loop_length,
                "loop_enabled": self._song.loop,
                "loop_start": loop_start,
                "loop_length": loop_length,
            }
        except Exception as e:
            self.log_message("Error setting arrangement loop: " + str(e))
            raise

    def _set_song_time(self, time):
        """Set playback position (beats)."""
        try:
            self._song.current_song_time = time
            return {"time": self._song.current_song_time, "current_time": self._song.current_song_time}
        except Exception as e:
            self.log_message("Error setting song time: " + str(e))
            raise

    @command("get_arrangement_info")
    def cmd_get_arrangement_info(self, params):
        track_index = params.get("track_index", -1)
        return self._get_arrangement_info(track_index)

    @command("set_arrangement_loop", modifying=True)
    def cmd_set_arrangement_loop(self, params):
        enabled = params.get("enabled", True)
        return self._set_arrangement_loop(enabled, params.get("start", None),
                                          params.get("length", None), params.get("end", None))

    @command("set_song_time", modifying=True, aliases=("jump_to_time",))
    def cmd_set_song_time(self, params):
        return self._set_song_time(params.get("time", 0.0))

    @command("create_arrangement_clip", modifying=True)
    def cmd_create_arrangement_clip(self, params):
        ti = params.get("track_index", 0)
        pos = params.get("position", 0.0)
        length = params.get("length", 4.0)
        return self._create_arrangement_clip(ti, pos, length)

    @command("create_arrangement_audio_clip", modifying=True)
    def cmd_create_arrangement_audio_clip(self, params):
        ti = params.get("track_index", 0)
        pos = params.get("position", 0.0)
        fp = params.get("file_path", "")
        return self._create_arrangement_audio_clip(ti, pos, fp)

    @command("duplicate_to_arrangement", modifying=True)
    def cmd_duplicate_to_arrangement(self, params):
        ti = params.get("track_index", 0)
        ci = params.get("clip_index", 0)
        dt = params.get("destination_time", 0.0)
        return self._duplicate_to_arrangement(ti, ci, dt)

    @command("add_notes_to_arrangement_clip", modifying=True)
    def cmd_add_notes_to_arrangement_clip(self, params):
        ti = params.get("track_index", 0)
        ci = params.get("clip_index", 0)
        notes = params.get("notes", [])
        return self._add_notes_to_arrangement_clip(ti, ci, notes)

    @command("delete_arrangement_clip", modifying=True)
    def cmd_delete_arrangement_clip(self, params):
        ti = params.get("track_index", 0)
        ci = params.get("clip_index", None)
        cn = params.get("clip_name", None)
        return self._delete_arrangement_clip(ti, ci, cn)

    @command("set_arrangement_clip_property", modifying=True)
    def cmd_set_arrangement_clip_property(self, params):
        ti = params.get("track_index", 0)
        ci = params.get("clip_index", 0)
        prop = params.get("property", "")
        val = params.get("value", None)
        return self._set_arrangement_clip_property(ti, ci, prop, val)

    @command("manage_clip_automation", modifying=True)
    def cmd_manage_clip_automation(self, params):
        ti = params.get("track_index", 0)
        ci = params.get("clip_index", 0)
        action = params.get("action", "create")
        pn = params.get("parameter_name", "")
        return self._manage_clip_automation(ti, ci, action, pn)
    # ---- command adapters (generated from the original dispatch chain) ----

    @command("get_arrangement_length")
    def cmd_get_arrangement_length(self, params):
        return self._get_arrangement_length()


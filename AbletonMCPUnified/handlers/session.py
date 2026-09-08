"""Session command handlers.

The ``cmd_*`` adapters are registered through registry.py.
"""
import random
import traceback

from ..registry import command


class SessionHandlers(object):

    def _get_session_info(self):
        """Get information about the current session"""
        try:
            result = {
                "tempo": self._song.tempo,
                "signature_numerator": self._song.signature_numerator,
                "signature_denominator": self._song.signature_denominator,
                "track_count": len(self._song.tracks),
                "return_track_count": len(self._song.return_tracks),
                "master_track": {
                    "name": "Master",
                    "volume": self._song.master_track.mixer_device.volume.value,
                    "panning": self._song.master_track.mixer_device.panning.value
                }
            }
            return result
        except Exception as e:
            self.log_message("Error getting session info: " + str(e))
            raise
    def _get_playback_position(self):
        """Get the current playback position"""
        try:
            result = {
                "current_song_time": self._song.current_song_time,
                "is_playing": self._song.is_playing,
                "tempo": self._song.tempo,
                "signature_numerator": self._song.signature_numerator,
                "signature_denominator": self._song.signature_denominator
            }
            return result
        except Exception as e:
            self.log_message("Error getting playback position: " + str(e))
            raise
    def _set_tempo(self, tempo):
        """Set the tempo of the session"""
        try:
            self._song.tempo = tempo
            
            result = {
                "tempo": self._song.tempo
            }
            return result
        except Exception as e:
            self.log_message("Error setting tempo: " + str(e))
            raise
    def _start_playback(self):
        """Start playing the session"""
        try:
            self._song.start_playing()
            
            result = {
                "playing": self._song.is_playing
            }
            return result
        except Exception as e:
            self.log_message("Error starting playback: " + str(e))
            raise
    def _stop_playback(self):
        """Stop playing the session"""
        try:
            self._song.stop_playing()

            result = {
                "playing": self._song.is_playing
            }
            return result
        except Exception as e:
            self.log_message("Error stopping playback: " + str(e))
            raise
    def _undo(self):
        """Undo the last operation"""
        try:
            if self._song.can_undo:
                self._song.undo()
                result = {
                    "undone": True
                }
            else:
                result = {
                    "undone": False,
                    "error": "Nothing to undo"
                }
            return result
        except Exception as e:
            self.log_message("Error undoing: " + str(e))
            raise
    def _redo(self):
        """Redo the last undone operation"""
        try:
            if self._song.can_redo:
                self._song.redo()
                result = {
                    "redone": True
                }
            else:
                result = {
                    "redone": False,
                    "error": "Nothing to redo"
                }
            return result
        except Exception as e:
            self.log_message("Error redoing: " + str(e))
            raise
    def _get_cpu_load(self):
        """Get the current CPU load"""
        try:
            app = self.application()
            result = {
                "cpu_load": app.get_cpu_load() if hasattr(app, 'get_cpu_load') else None
            }
            return result
        except Exception as e:
            self.log_message("Error getting CPU load: " + str(e))
            raise
    def _get_session_path(self):
        """Get the path of the current session"""
        try:
            app = self.application()
            doc = app.get_document() if hasattr(app, 'get_document') else None

            result = {
                "path": doc.file_path if doc and hasattr(doc, 'file_path') else None,
                "name": self._song.name if hasattr(self._song, 'name') else None
            }
            return result
        except Exception as e:
            self.log_message("Error getting session path: " + str(e))
            raise
    def _is_session_modified(self):
        """Check if the session has unsaved changes"""
        try:
            app = self.application()
            doc = app.get_document() if hasattr(app, 'get_document') else None

            result = {
                "modified": doc.is_modified if doc and hasattr(doc, 'is_modified') else None
            }
            return result
        except Exception as e:
            self.log_message("Error checking session modified: " + str(e))
            raise
    def _get_metronome_state(self):
        """Get the metronome state"""
        try:
            result = {
                "enabled": self._song.metronome if hasattr(self._song, 'metronome') else None
            }
            return result
        except Exception as e:
            self.log_message("Error getting metronome state: " + str(e))
            raise
    def _set_metronome(self, enabled):
        """Set the metronome on/off"""
        try:
            if hasattr(self._song, 'metronome'):
                self._song.metronome = enabled

            result = {
                "enabled": self._song.metronome if hasattr(self._song, 'metronome') else enabled
            }
            return result
        except Exception as e:
            self.log_message("Error setting metronome: " + str(e))
            raise
    def _get_crossfader(self):
        """Get the master crossfader value"""
        try:
            master = self._song.master_track
            crossfader = master.mixer_device.crossfader if hasattr(master.mixer_device, 'crossfader') else None
            if crossfader:
                return {
                    "value": crossfader.value,
                    "min": crossfader.min,
                    "max": crossfader.max
                }
            return {"error": "Crossfader not available"}
        except Exception as e:
            self.log_message("Error getting crossfader: " + str(e))
            return {"error": str(e)}
    def _set_crossfader(self, value):
        """Set the master crossfader value (0.0 to 1.0)"""
        try:
            master = self._song.master_track
            crossfader = master.mixer_device.crossfader if hasattr(master.mixer_device, 'crossfader') else None
            if crossfader:
                crossfader.value = max(0.0, min(1.0, value))
                return {"success": True, "value": crossfader.value}
            return {"error": "Crossfader not available"}
        except Exception as e:
            self.log_message("Error setting crossfader: " + str(e))
            return {"error": str(e)}
    def _get_swing_amount(self):
        """Get the global swing amount"""
        try:
            swing = self._song.swing_amount if hasattr(self._song, 'swing_amount') else 0.0
            return {"swing_amount": swing}
        except Exception as e:
            self.log_message("Error getting swing amount: " + str(e))
            return {"error": str(e)}
    def _set_swing_amount(self, amount):
        """Set the global swing amount (0.0 to 1.0)"""
        try:
            self._song.swing_amount = max(0.0, min(1.0, amount))
            return {"success": True, "swing_amount": self._song.swing_amount}
        except Exception as e:
            self.log_message("Error setting swing amount: " + str(e))
            return {"error": str(e)}
    def _get_song_root_note(self):
        """Get the song's root note (key signature)"""
        try:
            root_note = self._song.root_note if hasattr(self._song, 'root_note') else 0
            note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            return {
                "root_note": root_note,
                "root_note_name": note_names[root_note % 12]
            }
        except Exception as e:
            self.log_message("Error getting song root note: " + str(e))
            return {"error": str(e)}
    def _set_song_root_note(self, root_note):
        """Set the song's root note (0-11, C=0)"""
        try:
            self._song.root_note = root_note % 12
            return {"success": True, "root_note": self._song.root_note}
        except Exception as e:
            self.log_message("Error setting song root note: " + str(e))
            return {"error": str(e)}
    def _get_song_scale(self):
        """Get the song's scale mode"""
        try:
            scale_mode = self._song.scale_mode if hasattr(self._song, 'scale_mode') else None
            scale_name = self._song.scale_name if hasattr(self._song, 'scale_name') else "Unknown"
            return {
                "scale_mode": scale_mode,
                "scale_name": scale_name
            }
        except Exception as e:
            self.log_message("Error getting song scale: " + str(e))
            return {"error": str(e)}
    def _get_back_to_arrangement(self):
        """Get whether back to arrangement is needed"""
        try:
            back = self._song.back_to_arranger if hasattr(self._song, 'back_to_arranger') else False
            return {"back_to_arrangement": back}
        except Exception as e:
            self.log_message("Error getting back to arrangement: " + str(e))
            return {"error": str(e)}
    def _trigger_back_to_arrangement(self):
        """Trigger back to arrangement"""
        try:
            if hasattr(self._song, 'back_to_arranger'):
                self._song.back_to_arranger = False
                return {"success": True}
            return {"error": "Back to arrangement not available"}
        except Exception as e:
            self.log_message("Error triggering back to arrangement: " + str(e))
            return {"error": str(e)}
    def _get_exclusive_arm(self):
        """Get exclusive arm setting"""
        try:
            return {"exclusive_arm": self._song.exclusive_arm if hasattr(self._song, 'exclusive_arm') else True}
        except Exception as e:
            return {"error": str(e)}
    def _set_exclusive_arm(self, enabled):
        """Set exclusive arm"""
        try:
            self._song.exclusive_arm = enabled
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    def _get_exclusive_solo(self):
        """Get exclusive solo setting"""
        try:
            return {"exclusive_solo": self._song.exclusive_solo if hasattr(self._song, 'exclusive_solo') else False}
        except Exception as e:
            return {"error": str(e)}
    def _set_exclusive_solo(self, enabled):
        """Set exclusive solo"""
        try:
            self._song.exclusive_solo = enabled
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    def _continue_playing(self):
        """Continue playing from current position"""
        try:
            self._song.continue_playing()
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    def _tap_tempo(self):
        """Tap tempo"""
        try:
            self._song.tap_tempo()
            return {"success": True, "tempo": self._song.tempo}
        except Exception as e:
            return {"error": str(e)}
    def _get_signature(self):
        """Get time signature"""
        try:
            return {"numerator": self._song.signature_numerator, "denominator": self._song.signature_denominator}
        except Exception as e:
            return {"error": str(e)}
    def _set_signature(self, numerator, denominator):
        """Set time signature"""
        try:
            self._song.signature_numerator = numerator
            self._song.signature_denominator = denominator
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    def _get_song_length(self):
        """Get song length in beats"""
        try:
            return {"song_length": self._song.song_length if hasattr(self._song, 'song_length') else 0}
        except Exception as e:
            return {"error": str(e)}
    def _get_current_song_time(self):
        """Get current playback position"""
        try:
            return {"current_song_time": self._song.current_song_time, "is_playing": self._song.is_playing}
        except Exception as e:
            return {"error": str(e)}
    def _set_current_song_time(self, time):
        """Set playback position (scrub)"""
        try:
            self._song.current_song_time = time
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    def _get_cue_volume(self):
        """Get cue/preview volume"""
        try:
            return {"cue_volume": self._song.master_track.mixer_device.cue_volume.value}
        except Exception as e:
            return {"error": str(e)}
    def _set_cue_volume(self, volume):
        """Set cue/preview volume (0.0-1.0)"""
        try:
            self._song.master_track.mixer_device.cue_volume.value = max(0.0, min(1.0, volume))
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    def _scrub_by(self, delta):
        """Scrub playback position by delta beats"""
        try:
            self._song.scrub_by(delta)
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    # ---- unified additions ----

    def _health_check(self):
        """Check if Ableton is responsive (extended with Remote Script identity)."""
        from .. import RS_VERSION
        from ..registry import canonical_commands
        return {
            "status": "ok",
            "rs_version": RS_VERSION,
            "command_count": len(canonical_commands()),
            "tempo": self._song.tempo,
            "is_playing": self._song.is_playing,
            "track_count": len(self._song.tracks),
        }

    @command("health_check")
    def cmd_health_check(self, params):
        return self._health_check()

    @command("list_commands")
    def cmd_list_commands(self, params):
        from .. import RS_VERSION
        from ..registry import describe_commands, canonical_commands, modifying_commands
        return {
            "rs_version": RS_VERSION,
            "command_count": len(canonical_commands()),
            "modifying": modifying_commands(),
            "commands": describe_commands(),
        }
    # ---- command adapters (generated from the original dispatch chain) ----

    @command("get_session_info")
    def cmd_get_session_info(self, params):
        return self._get_session_info()

    @command("get_playback_position")
    def cmd_get_playback_position(self, params):
        return self._get_playback_position()

    @command("get_cpu_load")
    def cmd_get_cpu_load(self, params):
        return self._get_cpu_load()

    @command("get_session_path")
    def cmd_get_session_path(self, params):
        return self._get_session_path()

    @command("is_session_modified")
    def cmd_is_session_modified(self, params):
        return self._is_session_modified()

    @command("get_metronome_state")
    def cmd_get_metronome_state(self, params):
        return self._get_metronome_state()

    @command("get_crossfader")
    def cmd_get_crossfader(self, params):
        return self._get_crossfader()

    @command("get_swing_amount")
    def cmd_get_swing_amount(self, params):
        return self._get_swing_amount()

    @command("get_song_root_note")
    def cmd_get_song_root_note(self, params):
        return self._get_song_root_note()

    @command("get_song_scale")
    def cmd_get_song_scale(self, params):
        return self._get_song_scale()

    @command("get_back_to_arrangement")
    def cmd_get_back_to_arrangement(self, params):
        return self._get_back_to_arrangement()

    @command("get_exclusive_arm")
    def cmd_get_exclusive_arm(self, params):
        return self._get_exclusive_arm()

    @command("get_exclusive_solo")
    def cmd_get_exclusive_solo(self, params):
        return self._get_exclusive_solo()

    @command("get_signature")
    def cmd_get_signature(self, params):
        return self._get_signature()

    @command("get_song_length")
    def cmd_get_song_length(self, params):
        return self._get_song_length()

    @command("get_current_song_time")
    def cmd_get_current_song_time(self, params):
        return self._get_current_song_time()

    @command("get_cue_volume")
    def cmd_get_cue_volume(self, params):
        return self._get_cue_volume()

    @command("set_tempo", modifying=True)
    def cmd_set_tempo(self, params):
        tempo = params.get("tempo", 120.0)
        return self._set_tempo(tempo)

    @command("start_playback", modifying=True)
    def cmd_start_playback(self, params):
        return self._start_playback()

    @command("stop_playback", modifying=True)
    def cmd_stop_playback(self, params):
        return self._stop_playback()

    @command("undo", modifying=True)
    def cmd_undo(self, params):
        return self._undo()

    @command("redo", modifying=True)
    def cmd_redo(self, params):
        return self._redo()

    @command("set_metronome", modifying=True)
    def cmd_set_metronome(self, params):
        enabled = params.get("enabled", True)
        return self._set_metronome(enabled)

    @command("set_crossfader", modifying=True)
    def cmd_set_crossfader(self, params):
        value = params.get("value", 0.5)
        return self._set_crossfader(value)

    @command("set_swing_amount", modifying=True)
    def cmd_set_swing_amount(self, params):
        amount = params.get("amount", 0.0)
        return self._set_swing_amount(amount)

    @command("set_song_root_note", modifying=True)
    def cmd_set_song_root_note(self, params):
        root_note = params.get("root_note", 0)
        return self._set_song_root_note(root_note)

    @command("trigger_back_to_arrangement", modifying=True)
    def cmd_trigger_back_to_arrangement(self, params):
        return self._trigger_back_to_arrangement()

    @command("set_exclusive_arm", modifying=True)
    def cmd_set_exclusive_arm(self, params):
        enabled = params.get("enabled", True)
        return self._set_exclusive_arm(enabled)

    @command("set_exclusive_solo", modifying=True)
    def cmd_set_exclusive_solo(self, params):
        enabled = params.get("enabled", False)
        return self._set_exclusive_solo(enabled)

    @command("continue_playing", modifying=True)
    def cmd_continue_playing(self, params):
        return self._continue_playing()

    @command("tap_tempo", modifying=True)
    def cmd_tap_tempo(self, params):
        return self._tap_tempo()

    @command("set_signature", modifying=True)
    def cmd_set_signature(self, params):
        numerator = params.get("numerator", 4)
        denominator = params.get("denominator", 4)
        return self._set_signature(numerator, denominator)

    @command("set_current_song_time", modifying=True)
    def cmd_set_current_song_time(self, params):
        time = params.get("time", 0)
        return self._set_current_song_time(time)

    @command("set_cue_volume", modifying=True)
    def cmd_set_cue_volume(self, params):
        volume = params.get("volume", 0.85)
        return self._set_cue_volume(volume)

    @command("scrub_by", modifying=True)
    def cmd_scrub_by(self, params):
        delta = params.get("delta", 0)
        return self._scrub_by(delta)


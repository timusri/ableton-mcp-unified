"""Recording command handlers.

The ``cmd_*`` adapters are registered through registry.py.
"""
import random
import traceback

from ..registry import command


class RecordingHandlers(object):

    def _start_recording(self):
        """Start recording"""
        try:
            self._song.record_mode = True

            result = {
                "recording": self._song.record_mode
            }
            return result
        except Exception as e:
            self.log_message("Error starting recording: " + str(e))
            raise
    def _stop_recording(self):
        """Stop recording"""
        try:
            self._song.record_mode = False

            result = {
                "recording": self._song.record_mode
            }
            return result
        except Exception as e:
            self.log_message("Error stopping recording: " + str(e))
            raise
    def _toggle_session_record(self):
        """Toggle session record mode"""
        try:
            if hasattr(self._song, 'session_record'):
                self._song.session_record = not self._song.session_record
                result = {
                    "session_record": self._song.session_record
                }
            else:
                result = {
                    "error": "Session record not available"
                }
            return result
        except Exception as e:
            self.log_message("Error toggling session record: " + str(e))
            raise
    def _toggle_arrangement_record(self):
        """Toggle arrangement record mode"""
        try:
            self._song.record_mode = not self._song.record_mode

            result = {
                "arrangement_record": self._song.record_mode
            }
            return result
        except Exception as e:
            self.log_message("Error toggling arrangement record: " + str(e))
            raise
    def _set_overdub(self, enabled):
        """Set overdub mode"""
        try:
            if hasattr(self._song, 'overdub'):
                self._song.overdub = enabled
                result = {
                    "overdub": self._song.overdub
                }
            else:
                result = {
                    "error": "Overdub not available"
                }
            return result
        except Exception as e:
            self.log_message("Error setting overdub: " + str(e))
            raise
    def _capture_midi(self):
        """Capture MIDI that was played recently"""
        try:
            if hasattr(self._song, 'capture_midi'):
                self._song.capture_midi()
                result = {
                    "captured": True
                }
            else:
                result = {
                    "captured": False,
                    "error": "Capture MIDI not available"
                }
            return result
        except Exception as e:
            self.log_message("Error capturing MIDI: " + str(e))
            raise
    def _get_punch_settings(self):
        """Get punch in/out settings"""
        try:
            result = {}
            if hasattr(self._song, 'punch_in'):
                result["punch_in"] = self._song.punch_in
            if hasattr(self._song, 'punch_out'):
                result["punch_out"] = self._song.punch_out
            if hasattr(self._song, 'loop_start'):
                result["punch_in_position"] = self._song.loop_start
            if hasattr(self._song, 'loop_length'):
                result["punch_out_position"] = self._song.loop_start + self._song.loop_length
            return result if result else {"error": "Punch settings not available"}
        except Exception as e:
            self.log_message("Error getting punch settings: " + str(e))
            return {"error": str(e)}
    def _set_punch_in(self, enabled):
        """Enable/disable punch in"""
        try:
            self._song.punch_in = enabled
            return {"success": True, "punch_in": enabled}
        except Exception as e:
            self.log_message("Error setting punch in: " + str(e))
            return {"error": str(e)}
    def _set_punch_out(self, enabled):
        """Enable/disable punch out"""
        try:
            self._song.punch_out = enabled
            return {"success": True, "punch_out": enabled}
        except Exception as e:
            self.log_message("Error setting punch out: " + str(e))
            return {"error": str(e)}
    def _get_midi_recording_quantization(self):
        """Get MIDI recording quantization"""
        try:
            return {"midi_recording_quantization": self._song.midi_recording_quantization}
        except Exception as e:
            return {"error": str(e)}
    def _set_midi_recording_quantization(self, quant):
        """Set MIDI recording quantization"""
        try:
            self._song.midi_recording_quantization = quant
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    def _get_record_mode(self):
        """Get record mode states"""
        try:
            return {
                "session_record": self._song.session_record,
                "overdub": self._song.overdub if hasattr(self._song, 'overdub') else False
            }
        except Exception as e:
            return {"error": str(e)}
    def _get_can_capture_midi(self):
        """Check if MIDI can be captured"""
        try:
            return {"can_capture_midi": self._song.can_capture_midi if hasattr(self._song, 'can_capture_midi') else False}
        except Exception as e:
            return {"error": str(e)}
    def _get_session_automation_record(self):
        """Get session automation record state"""
        try:
            return {"session_automation_record": self._song.session_automation_record}
        except Exception as e:
            return {"error": str(e)}
    def _set_session_automation_record(self, enabled):
        """Set session automation record state"""
        try:
            self._song.session_automation_record = enabled
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    def _get_arrangement_overdub(self):
        """Get arrangement overdub state"""
        try:
            return {"arrangement_overdub": self._song.arrangement_overdub}
        except Exception as e:
            return {"error": str(e)}
    def _set_arrangement_overdub(self, enabled):
        """Set arrangement overdub state"""
        try:
            self._song.arrangement_overdub = enabled
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    def _get_count_in_duration(self):
        """Get count-in duration"""
        try:
            return {"count_in_duration": self._song.count_in_duration}
        except Exception as e:
            return {"error": str(e)}
    def _set_count_in_duration(self, duration):
        """Set count-in duration (0=None, 1=1bar, 2=2bars, 4=4bars)"""
        try:
            self._song.count_in_duration = duration
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    def _re_enable_automation(self):
        """Re-enable automation (un-override all)"""
        try:
            self._song.re_enable_automation()
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    # ---- command adapters (generated from the original dispatch chain) ----

    @command("get_punch_settings")
    def cmd_get_punch_settings(self, params):
        return self._get_punch_settings()

    @command("get_midi_recording_quantization")
    def cmd_get_midi_recording_quantization(self, params):
        return self._get_midi_recording_quantization()

    @command("get_record_mode")
    def cmd_get_record_mode(self, params):
        return self._get_record_mode()

    @command("get_can_capture_midi")
    def cmd_get_can_capture_midi(self, params):
        return self._get_can_capture_midi()

    @command("get_session_automation_record")
    def cmd_get_session_automation_record(self, params):
        return self._get_session_automation_record()

    @command("get_arrangement_overdub")
    def cmd_get_arrangement_overdub(self, params):
        return self._get_arrangement_overdub()

    @command("get_count_in_duration")
    def cmd_get_count_in_duration(self, params):
        return self._get_count_in_duration()

    @command("start_recording", modifying=True)
    def cmd_start_recording(self, params):
        return self._start_recording()

    @command("stop_recording", modifying=True)
    def cmd_stop_recording(self, params):
        return self._stop_recording()

    @command("toggle_session_record", modifying=True)
    def cmd_toggle_session_record(self, params):
        return self._toggle_session_record()

    @command("toggle_arrangement_record", modifying=True)
    def cmd_toggle_arrangement_record(self, params):
        return self._toggle_arrangement_record()

    @command("set_overdub", modifying=True)
    def cmd_set_overdub(self, params):
        enabled = params.get("enabled", False)
        return self._set_overdub(enabled)

    @command("capture_midi", modifying=True)
    def cmd_capture_midi(self, params):
        return self._capture_midi()

    @command("set_punch_in", modifying=True)
    def cmd_set_punch_in(self, params):
        enabled = params.get("enabled", False)
        return self._set_punch_in(enabled)

    @command("set_punch_out", modifying=True)
    def cmd_set_punch_out(self, params):
        enabled = params.get("enabled", False)
        return self._set_punch_out(enabled)

    @command("set_midi_recording_quantization", modifying=True)
    def cmd_set_midi_recording_quantization(self, params):
        quant = params.get("quantization", 0)
        return self._set_midi_recording_quantization(quant)

    @command("set_session_automation_record", modifying=True)
    def cmd_set_session_automation_record(self, params):
        enabled = params.get("enabled", False)
        return self._set_session_automation_record(enabled)

    @command("set_arrangement_overdub", modifying=True)
    def cmd_set_arrangement_overdub(self, params):
        enabled = params.get("enabled", False)
        return self._set_arrangement_overdub(enabled)

    @command("re_enable_automation", modifying=True)
    def cmd_re_enable_automation(self, params):
        return self._re_enable_automation()

    @command("set_count_in_duration", modifying=True)
    def cmd_set_count_in_duration(self, params):
        duration = params.get("duration", 0)
        return self._set_count_in_duration(duration)


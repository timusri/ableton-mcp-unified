"""Clip command handlers.

The ``cmd_*`` adapters are registered through registry.py.
"""
import random
import traceback

from ..registry import command


class ClipHandlers(object):

    def _get_clip_info(self, track_index, clip_index):
        """Get clip metadata without notes"""
        try:
            clip_slot = self._validate_clip_slot(track_index, clip_index)

            if not clip_slot.has_clip:
                return {
                    "track_index": track_index,
                    "clip_index": clip_index,
                    "has_clip": False
                }

            clip = clip_slot.clip

            result = {
                "track_index": track_index,
                "clip_index": clip_index,
                "has_clip": True,
                "name": clip.name,
                "length": clip.length,
                "is_midi_clip": clip.is_midi_clip,
                "is_audio_clip": clip.is_audio_clip,
                "is_playing": clip.is_playing,
                "is_recording": clip.is_recording,
                "is_triggered": clip.is_triggered,
                "looping": clip.looping,
                "loop_start": clip.loop_start,
                "loop_end": clip.loop_end,
                "start_marker": clip.start_marker,
                "end_marker": clip.end_marker,
                "color_index": clip.color_index
            }

            # Add warp mode for audio clips
            if clip.is_audio_clip:
                result["warping"] = clip.warping
                result["warp_mode"] = clip.warp_mode if hasattr(clip, 'warp_mode') else None

            return result
        except Exception as e:
            self.log_message("Error getting clip info: " + str(e))
            raise
    def _delete_clip(self, track_index, clip_index):
        """Delete a clip from a clip slot"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]

            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip index out of range")

            clip_slot = track.clip_slots[clip_index]

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip_name = clip_slot.clip.name
            clip_slot.delete_clip()

            result = {
                "deleted": True,
                "track_index": track_index,
                "clip_index": clip_index,
                "clip_name": clip_name
            }
            return result
        except Exception as e:
            self.log_message("Error deleting clip: " + str(e))
            raise
    def _create_clip(self, track_index, clip_index, length):
        """Create a new MIDI clip in the specified track and clip slot"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")
            
            track = self._song.tracks[track_index]
            
            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip index out of range")
            
            clip_slot = track.clip_slots[clip_index]
            
            # Check if the clip slot already has a clip
            if clip_slot.has_clip:
                raise Exception("Clip slot already has a clip")
            
            # Create the clip
            clip_slot.create_clip(length)
            
            result = {
                "name": clip_slot.clip.name,
                "length": clip_slot.clip.length
            }
            return result
        except Exception as e:
            self.log_message("Error creating clip: " + str(e))
            raise
    def _set_clip_name(self, track_index, clip_index, name):
        """Set the name of a clip"""
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
            clip.name = name
            
            result = {
                "name": clip.name
            }
            return result
        except Exception as e:
            self.log_message("Error setting clip name: " + str(e))
            raise
    def _fire_clip(self, track_index, clip_index):
        """Fire a clip"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")
            
            track = self._song.tracks[track_index]
            
            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip index out of range")
            
            clip_slot = track.clip_slots[clip_index]
            
            if not clip_slot.has_clip:
                raise Exception("No clip in slot")
            
            clip_slot.fire()
            
            result = {
                "fired": True
            }
            return result
        except Exception as e:
            self.log_message("Error firing clip: " + str(e))
            raise
    def _stop_clip(self, track_index, clip_index):
        """Stop a clip"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")
            
            track = self._song.tracks[track_index]
            
            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip index out of range")
            
            clip_slot = track.clip_slots[clip_index]
            
            clip_slot.stop()
            
            result = {
                "stopped": True
            }
            return result
        except Exception as e:
            self.log_message("Error stopping clip: " + str(e))
            raise
    def _duplicate_clip(self, track_index, clip_index):
        """Duplicate a clip to the next empty slot"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]

            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip index out of range")

            clip_slot = track.clip_slots[clip_index]

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            # Find next empty slot
            target_index = None
            for i in range(clip_index + 1, len(track.clip_slots)):
                if not track.clip_slots[i].has_clip:
                    target_index = i
                    break

            if target_index is None:
                raise Exception("No empty slot available for duplication")

            clip_slot.duplicate_clip_to(track.clip_slots[target_index])

            result = {
                "duplicated": True,
                "original_index": clip_index,
                "new_index": target_index,
                "clip_name": track.clip_slots[target_index].clip.name
            }
            return result
        except Exception as e:
            self.log_message("Error duplicating clip: " + str(e))
            raise
    def _set_clip_color(self, track_index, clip_index, color):
        """Set the color of a clip"""
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
            if hasattr(clip, 'color_index'):
                clip.color_index = color

            result = {
                "track_index": track_index,
                "clip_index": clip_index,
                "color_index": clip.color_index if hasattr(clip, 'color_index') else None
            }
            return result
        except Exception as e:
            self.log_message("Error setting clip color: " + str(e))
            raise
    def _set_clip_loop(self, track_index, clip_index, loop_start, loop_end, looping):
        """Set the loop settings of a clip"""
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
            clip.looping = looping
            clip.loop_start = loop_start
            clip.loop_end = loop_end

            result = {
                "track_index": track_index,
                "clip_index": clip_index,
                "looping": clip.looping,
                "loop_start": clip.loop_start,
                "loop_end": clip.loop_end
            }
            return result
        except Exception as e:
            self.log_message("Error setting clip loop: " + str(e))
            raise
    def _set_clip_gain(self, track_index, clip_index, gain):
        """Set the gain of an audio clip in dB"""
        try:
            clip_slot = self._validate_clip_slot(track_index, clip_index)
            if not clip_slot.has_clip:
                raise ValueError("No clip in slot")

            clip = clip_slot.clip

            # Check if it's an audio clip
            if not clip.is_audio_clip:
                raise ValueError("Clip is not an audio clip")

            # Gain is in dB, convert to Ableton's linear gain
            # Ableton uses a range where 0dB = 1.0
            import math
            linear_gain = math.pow(10, gain / 20.0)
            clip.gain = max(0.0, min(4.0, linear_gain))  # Clamp to reasonable range

            return {
                "track_index": track_index,
                "clip_index": clip_index,
                "gain_db": gain,
                "gain_linear": clip.gain
            }
        except Exception as e:
            self.log_message("Error setting clip gain: " + str(e))
            raise
    def _set_clip_pitch(self, track_index, clip_index, pitch):
        """Set the pitch shift of an audio clip in semitones"""
        try:
            clip_slot = self._validate_clip_slot(track_index, clip_index)
            if not clip_slot.has_clip:
                raise ValueError("No clip in slot")

            clip = clip_slot.clip

            if not clip.is_audio_clip:
                raise ValueError("Clip is not an audio clip")

            # Pitch coarse is in semitones (-48 to +48)
            pitch = max(-48, min(48, int(pitch)))
            clip.pitch_coarse = pitch

            return {
                "track_index": track_index,
                "clip_index": clip_index,
                "pitch_semitones": clip.pitch_coarse
            }
        except Exception as e:
            self.log_message("Error setting clip pitch: " + str(e))
            raise
    def _set_clip_warp_mode(self, track_index, clip_index, warp_mode):
        """Set the warp mode of an audio clip"""
        try:
            clip_slot = self._validate_clip_slot(track_index, clip_index)
            if not clip_slot.has_clip:
                raise ValueError("No clip in slot")

            clip = clip_slot.clip

            if not clip.is_audio_clip:
                raise ValueError("Clip is not an audio clip")

            # Warp modes: beats, tones, texture, repitch, complex, complex_pro
            warp_modes = {
                "beats": 0,
                "tones": 1,
                "texture": 2,
                "repitch": 3,
                "complex": 4,
                "complex_pro": 5
            }

            mode_value = warp_modes.get(warp_mode.lower(), 0)
            clip.warp_mode = mode_value

            return {
                "track_index": track_index,
                "clip_index": clip_index,
                "warp_mode": warp_mode,
                "warp_mode_value": mode_value
            }
        except Exception as e:
            self.log_message("Error setting warp mode: " + str(e))
            raise
    def _get_clip_warp_info(self, track_index, clip_index):
        """Get warp info for an audio clip"""
        try:
            clip_slot = self._validate_clip_slot(track_index, clip_index)
            if not clip_slot.has_clip:
                raise ValueError("No clip in slot")

            clip = clip_slot.clip

            if not clip.is_audio_clip:
                raise ValueError("Clip is not an audio clip")

            warp_mode_names = ["beats", "tones", "texture", "repitch", "complex", "complex_pro"]

            return {
                "track_index": track_index,
                "clip_index": clip_index,
                "warping": clip.warping,
                "warp_mode": warp_mode_names[clip.warp_mode] if clip.warp_mode < len(warp_mode_names) else "unknown",
                "warp_mode_value": clip.warp_mode,
                "gain": clip.gain,
                "pitch_coarse": clip.pitch_coarse,
                "pitch_fine": clip.pitch_fine if hasattr(clip, 'pitch_fine') else 0
            }
        except Exception as e:
            self.log_message("Error getting warp info: " + str(e))
            raise
    def _get_clip_automation(self, track_index, clip_index, parameter_name):
        """Get automation envelope data for a clip parameter"""
        try:
            clip_slot = self._validate_clip_slot(track_index, clip_index)
            if not clip_slot.has_clip:
                raise ValueError("No clip in slot")

            clip = clip_slot.clip
            track = self._song.tracks[track_index]

            # Find the parameter
            param = None
            device_name = None
            for device in track.devices:
                for p in device.parameters:
                    if p.name.lower() == parameter_name.lower():
                        param = p
                        device_name = device.name
                        break
                if param:
                    break

            if not param:
                return {
                    "error": "Parameter not found: " + parameter_name,
                    "available_parameters": [p.name for d in track.devices for p in d.parameters][:20]
                }

            # Get envelope if it exists
            envelope = clip.automation_envelope(param) if hasattr(clip, 'automation_envelope') else None

            if not envelope:
                return {
                    "track_index": track_index,
                    "clip_index": clip_index,
                    "parameter_name": parameter_name,
                    "device_name": device_name,
                    "has_automation": False,
                    "envelope_data": []
                }

            # Read envelope points (simplified - actual implementation would read breakpoints)
            return {
                "track_index": track_index,
                "clip_index": clip_index,
                "parameter_name": parameter_name,
                "device_name": device_name,
                "has_automation": True,
                "parameter_min": param.min,
                "parameter_max": param.max,
                "parameter_value": param.value
            }
        except Exception as e:
            self.log_message("Error getting clip automation: " + str(e))
            raise
    def _set_clip_automation(self, track_index, clip_index, parameter_name, envelope_data):
        """Set automation envelope for a clip parameter"""
        try:
            clip_slot = self._validate_clip_slot(track_index, clip_index)
            if not clip_slot.has_clip:
                raise ValueError("No clip in slot")

            clip = clip_slot.clip
            track = self._song.tracks[track_index]

            # Find the parameter
            param = None
            for device in track.devices:
                for p in device.parameters:
                    if p.name.lower() == parameter_name.lower():
                        param = p
                        break
                if param:
                    break

            if not param:
                raise ValueError("Parameter not found: " + parameter_name)

            # Reuse an existing envelope; Live raises if one is created twice
            envelope = None
            if hasattr(clip, 'automation_envelope'):
                envelope = clip.automation_envelope(param)
            if envelope is None:
                if hasattr(clip, 'create_automation_envelope'):
                    envelope = clip.create_automation_envelope(param)
                else:
                    return {"error": "Automation envelopes not supported in this version"}

            # Clear existing and add new points
            if hasattr(envelope, 'clear'):
                envelope.clear()

            # Add breakpoints from envelope_data
            # envelope_data format: [{"time": float, "value": float}, ...]
            # Values are in the parameter's own range (param.min..param.max),
            # not normalized 0-1; see get_clip_automation for the range.
            for point in envelope_data:
                time = point.get("time", 0)
                value = point.get("value", param.value)
                if hasattr(envelope, 'insert_value'):
                    envelope.insert_value(time, value)

            return {
                "track_index": track_index,
                "clip_index": clip_index,
                "parameter_name": parameter_name,
                "points_added": len(envelope_data)
            }
        except Exception as e:
            self.log_message("Error setting clip automation: " + str(e))
            raise
    def _clear_clip_automation(self, track_index, clip_index, parameter_name):
        """Clear automation envelope for a parameter in a clip"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]
            clip_slots = list(track.clip_slots)
            if clip_index >= len(clip_slots):
                return {"error": "Clip index out of range"}
            clip_slot = clip_slots[clip_index]
            if not clip_slot.has_clip:
                return {"error": "No clip in slot"}
            clip = clip_slot.clip

            # Find the parameter
            # First check track mixer parameters
            mixer = track.mixer_device
            param = None
            if parameter_name.lower() == "volume":
                param = mixer.volume
            elif parameter_name.lower() == "pan" or parameter_name.lower() == "panning":
                param = mixer.panning

            if param is None:
                # Then device parameters, first exact name match wins (same rule as set_clip_automation)
                for device in track.devices:
                    for p in device.parameters:
                        if p.name.lower() == parameter_name.lower():
                            param = p
                            break
                    if param is not None:
                        break

            if param is None:
                return {"error": "Parameter '{0}' not found".format(parameter_name)}

            # Clear the automation
            clip.clear_envelope(param)

            return {"success": True, "parameter": parameter_name}
        except Exception as e:
            self.log_message("Error clearing clip automation: " + str(e))
            return {"error": str(e)}
    def _get_groove_pool(self):
        """Get available grooves from the groove pool"""
        try:
            if not hasattr(self._song, 'groove_pool') or not self._song.groove_pool:
                return {"error": "Groove pool not available", "grooves": []}

            grooves = []
            for i, groove in enumerate(self._song.groove_pool.grooves):
                grooves.append({
                    "index": i,
                    "name": groove.name if hasattr(groove, 'name') else "Groove " + str(i),
                    "amount": groove.amount if hasattr(groove, 'amount') else 1.0
                })

            return {
                "groove_count": len(grooves),
                "grooves": grooves
            }
        except Exception as e:
            self.log_message("Error getting groove pool: " + str(e))
            raise
    def _apply_groove(self, track_index, clip_index, groove_index):
        """Apply a groove to a clip"""
        try:
            clip_slot = self._validate_clip_slot(track_index, clip_index)
            if not clip_slot.has_clip:
                raise ValueError("No clip in slot")

            clip = clip_slot.clip

            if not hasattr(self._song, 'groove_pool') or not self._song.groove_pool:
                return {"error": "Groove pool not available"}

            grooves = list(self._song.groove_pool.grooves)
            if groove_index < 0 or groove_index >= len(grooves):
                raise IndexError("Groove index out of range")

            groove = grooves[groove_index]

            # Apply groove to clip
            if hasattr(clip, 'groove'):
                clip.groove = groove
                return {
                    "track_index": track_index,
                    "clip_index": clip_index,
                    "groove_applied": True,
                    "groove_name": groove.name if hasattr(groove, 'name') else "Groove " + str(groove_index)
                }
            else:
                return {"error": "Groove assignment not supported"}
        except Exception as e:
            self.log_message("Error applying groove: " + str(e))
            raise
    def _commit_groove(self, track_index, clip_index):
        """Commit groove quantization to clip notes"""
        try:
            clip_slot = self._validate_clip_slot(track_index, clip_index)
            if not clip_slot.has_clip:
                raise ValueError("No clip in slot")

            clip = clip_slot.clip

            # Commit groove (make it permanent)
            if hasattr(clip, 'quantize'):
                # This will apply the groove permanently
                clip.quantize(0.125, 1.0)  # Quantize to 32nd notes with full strength

            return {
                "track_index": track_index,
                "clip_index": clip_index,
                "committed": True
            }
        except Exception as e:
            self.log_message("Error committing groove: " + str(e))
            raise
    def _get_clip_color(self, track_index, clip_index):
        """Get the color index of a clip"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]
            clip_slots = list(track.clip_slots)
            if clip_index >= len(clip_slots):
                return {"error": "Clip index out of range"}
            clip_slot = clip_slots[clip_index]
            if not clip_slot.has_clip:
                return {"error": "No clip in slot"}
            clip = clip_slot.clip
            return {"color_index": clip.color_index}
        except Exception as e:
            self.log_message("Error getting clip color: " + str(e))
            return {"error": str(e)}
    def _get_clip_gain(self, track_index, clip_index):
        """Get the gain of an audio clip in dB"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]
            clip_slots = list(track.clip_slots)
            if clip_index >= len(clip_slots):
                return {"error": "Clip index out of range"}
            clip_slot = clip_slots[clip_index]
            if not clip_slot.has_clip:
                return {"error": "No clip in slot"}
            clip = clip_slot.clip
            if clip.is_midi_clip:
                return {"error": "Gain only applies to audio clips"}
            # gain is in dB, typically -inf to +35.5dB
            return {
                "gain_db": clip.gain,
                "gain_display": clip.gain_display_string if hasattr(clip, 'gain_display_string') else str(clip.gain) + " dB"
            }
        except Exception as e:
            self.log_message("Error getting clip gain: " + str(e))
            return {"error": str(e)}
    def _get_clip_pitch(self, track_index, clip_index):
        """Get the pitch shift of an audio clip in semitones"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]
            clip_slots = list(track.clip_slots)
            if clip_index >= len(clip_slots):
                return {"error": "Clip index out of range"}
            clip_slot = clip_slots[clip_index]
            if not clip_slot.has_clip:
                return {"error": "No clip in slot"}
            clip = clip_slot.clip
            if clip.is_midi_clip:
                return {"error": "Pitch shift only applies to audio clips"}
            # pitch_coarse is in semitones (-48 to +48)
            # pitch_fine is in cents (-50 to +50)
            return {
                "pitch_coarse": clip.pitch_coarse,
                "pitch_fine": clip.pitch_fine,
                "pitch_semitones": clip.pitch_coarse + (clip.pitch_fine / 100.0)
            }
        except Exception as e:
            self.log_message("Error getting clip pitch: " + str(e))
            return {"error": str(e)}
    def _get_clip_loop(self, track_index, clip_index):
        """Get the loop settings of a clip"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]
            clip_slots = list(track.clip_slots)
            if clip_index >= len(clip_slots):
                return {"error": "Clip index out of range"}
            clip_slot = clip_slots[clip_index]
            if not clip_slot.has_clip:
                return {"error": "No clip in slot"}
            clip = clip_slot.clip
            return {
                "loop_start": clip.loop_start,
                "loop_end": clip.loop_end,
                "looping": clip.looping,
                "loop_length": clip.loop_end - clip.loop_start
            }
        except Exception as e:
            self.log_message("Error getting clip loop: " + str(e))
            return {"error": str(e)}
    def _get_warp_markers(self, track_index, clip_index):
        """Get all warp markers from an audio clip"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]
            clip_slots = list(track.clip_slots)
            if clip_index >= len(clip_slots):
                return {"error": "Clip index out of range"}
            clip_slot = clip_slots[clip_index]
            if not clip_slot.has_clip:
                return {"error": "No clip in slot"}
            clip = clip_slot.clip
            if clip.is_midi_clip:
                return {"error": "Warp markers only apply to audio clips"}
            if not clip.warping:
                return {"error": "Warping is disabled for this clip", "warping": False}

            # Get warp markers
            markers = []
            if hasattr(clip, 'warp_markers'):
                for i, marker in enumerate(clip.warp_markers):
                    markers.append({
                        "index": i,
                        "beat_time": marker.beat_time,
                        "sample_time": marker.sample_time
                    })

            return {
                "warping": clip.warping,
                "warp_mode": clip.warp_mode if hasattr(clip, 'warp_mode') else None,
                "warp_markers": markers,
                "count": len(markers)
            }
        except Exception as e:
            self.log_message("Error getting warp markers: " + str(e))
            return {"error": str(e)}
    def _add_warp_marker(self, track_index, clip_index, beat_time, sample_time=None):
        """Add a warp marker to an audio clip"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]
            clip_slots = list(track.clip_slots)
            if clip_index >= len(clip_slots):
                return {"error": "Clip index out of range"}
            clip_slot = clip_slots[clip_index]
            if not clip_slot.has_clip:
                return {"error": "No clip in slot"}
            clip = clip_slot.clip
            if clip.is_midi_clip:
                return {"error": "Warp markers only apply to audio clips"}
            if not clip.warping:
                return {"error": "Warping is disabled for this clip"}

            # Add warp marker
            if sample_time is not None:
                clip.insert_warp_marker(beat_time, sample_time)
            else:
                # If no sample_time provided, use the current time at this beat position
                clip.insert_warp_marker(beat_time)

            return {"success": True, "beat_time": beat_time, "sample_time": sample_time}
        except Exception as e:
            self.log_message("Error adding warp marker: " + str(e))
            return {"error": str(e)}
    def _delete_warp_marker(self, track_index, clip_index, beat_time):
        """Delete a warp marker from an audio clip by beat time"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]
            clip_slots = list(track.clip_slots)
            if clip_index >= len(clip_slots):
                return {"error": "Clip index out of range"}
            clip_slot = clip_slots[clip_index]
            if not clip_slot.has_clip:
                return {"error": "No clip in slot"}
            clip = clip_slot.clip
            if clip.is_midi_clip:
                return {"error": "Warp markers only apply to audio clips"}
            if not clip.warping:
                return {"error": "Warping is disabled for this clip"}

            # Find and delete the warp marker at the given beat time
            if hasattr(clip, 'warp_markers'):
                for marker in clip.warp_markers:
                    if abs(marker.beat_time - beat_time) < 0.001:  # Small tolerance
                        clip.remove_warp_marker(beat_time)
                        return {"success": True, "beat_time": beat_time}

            return {"error": "No warp marker found at beat time {0}".format(beat_time)}
        except Exception as e:
            self.log_message("Error deleting warp marker: " + str(e))
            return {"error": str(e)}
    def _get_clip_launch_mode(self, track_index, clip_index):
        """Get the launch mode of a clip (retrigger, gate, toggle, repeat)"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]
            clip_slots = list(track.clip_slots)
            if clip_index >= len(clip_slots):
                return {"error": "Clip index out of range"}
            clip_slot = clip_slots[clip_index]
            if not clip_slot.has_clip:
                return {"error": "No clip in slot"}
            clip = clip_slot.clip

            # Launch mode: 0=trigger, 1=gate, 2=toggle, 3=repeat
            mode_names = ["trigger", "gate", "toggle", "repeat"]
            mode = clip.launch_mode if hasattr(clip, 'launch_mode') else 0
            return {
                "launch_mode": mode,
                "launch_mode_name": mode_names[mode] if mode < len(mode_names) else "unknown"
            }
        except Exception as e:
            self.log_message("Error getting clip launch mode: " + str(e))
            return {"error": str(e)}
    def _set_clip_launch_mode(self, track_index, clip_index, mode):
        """Set the launch mode of a clip"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]
            clip_slots = list(track.clip_slots)
            if clip_index >= len(clip_slots):
                return {"error": "Clip index out of range"}
            clip_slot = clip_slots[clip_index]
            if not clip_slot.has_clip:
                return {"error": "No clip in slot"}
            clip = clip_slot.clip

            # Convert mode name to number if needed
            mode_names = {"trigger": 0, "gate": 1, "toggle": 2, "repeat": 3}
            if isinstance(mode, str):
                mode = mode_names.get(mode.lower(), 0)

            clip.launch_mode = mode
            return {"success": True, "launch_mode": mode}
        except Exception as e:
            self.log_message("Error setting clip launch mode: " + str(e))
            return {"error": str(e)}
    def _get_clip_launch_quantization(self, track_index, clip_index):
        """Get the launch quantization of a clip"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]
            clip_slots = list(track.clip_slots)
            if clip_index >= len(clip_slots):
                return {"error": "Clip index out of range"}
            clip_slot = clip_slots[clip_index]
            if not clip_slot.has_clip:
                return {"error": "No clip in slot"}
            clip = clip_slot.clip

            quant = clip.launch_quantization if hasattr(clip, 'launch_quantization') else 0
            return {"launch_quantization": quant}
        except Exception as e:
            self.log_message("Error getting clip launch quantization: " + str(e))
            return {"error": str(e)}
    def _set_clip_launch_quantization(self, track_index, clip_index, quantization):
        """Set the launch quantization of a clip"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]
            clip_slots = list(track.clip_slots)
            if clip_index >= len(clip_slots):
                return {"error": "Clip index out of range"}
            clip_slot = clip_slots[clip_index]
            if not clip_slot.has_clip:
                return {"error": "No clip in slot"}
            clip = clip_slot.clip

            clip.launch_quantization = quantization
            return {"success": True, "launch_quantization": quantization}
        except Exception as e:
            self.log_message("Error setting clip launch quantization: " + str(e))
            return {"error": str(e)}
    def _get_clip_follow_action(self, track_index, clip_index):
        """Get the follow action settings of a clip"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]
            clip_slots = list(track.clip_slots)
            if clip_index >= len(clip_slots):
                return {"error": "Clip index out of range"}
            clip_slot = clip_slots[clip_index]
            if not clip_slot.has_clip:
                return {"error": "No clip in slot"}
            clip = clip_slot.clip

            # Follow action types: 0=none, 1=stop, 2=again, 3=prev, 4=next, 5=first, 6=last, 7=any, 8=other, 9=jump
            action_names = ["none", "stop", "again", "previous", "next", "first", "last", "any", "other", "jump"]

            result = {}
            if hasattr(clip, 'follow_action_a'):
                result["follow_action_a"] = clip.follow_action_a
                result["follow_action_a_name"] = action_names[clip.follow_action_a] if clip.follow_action_a < len(action_names) else "unknown"
            if hasattr(clip, 'follow_action_b'):
                result["follow_action_b"] = clip.follow_action_b
                result["follow_action_b_name"] = action_names[clip.follow_action_b] if clip.follow_action_b < len(action_names) else "unknown"
            if hasattr(clip, 'follow_action_chance'):
                result["follow_action_chance"] = clip.follow_action_chance
            if hasattr(clip, 'follow_action_time'):
                result["follow_action_time"] = clip.follow_action_time

            return result
        except Exception as e:
            self.log_message("Error getting clip follow action: " + str(e))
            return {"error": str(e)}
    def _set_clip_follow_action(self, track_index, clip_index, action_a=None, action_b=None, chance=None, time=None):
        """Set the follow action settings of a clip"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]
            clip_slots = list(track.clip_slots)
            if clip_index >= len(clip_slots):
                return {"error": "Clip index out of range"}
            clip_slot = clip_slots[clip_index]
            if not clip_slot.has_clip:
                return {"error": "No clip in slot"}
            clip = clip_slot.clip

            action_names = {"none": 0, "stop": 1, "again": 2, "previous": 3, "next": 4, "first": 5, "last": 6, "any": 7, "other": 8, "jump": 9}

            if action_a is not None:
                if isinstance(action_a, str):
                    action_a = action_names.get(action_a.lower(), 0)
                clip.follow_action_a = action_a
            if action_b is not None:
                if isinstance(action_b, str):
                    action_b = action_names.get(action_b.lower(), 0)
                clip.follow_action_b = action_b
            if chance is not None:
                clip.follow_action_chance = chance
            if time is not None:
                clip.follow_action_time = time

            return {"success": True}
        except Exception as e:
            self.log_message("Error setting clip follow action: " + str(e))
            return {"error": str(e)}
    def _get_clip_ram_mode(self, track_index, clip_index):
        """Get whether an audio clip is loaded into RAM"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]
            clip_slots = list(track.clip_slots)
            if clip_index >= len(clip_slots):
                return {"error": "Clip index out of range"}
            clip_slot = clip_slots[clip_index]
            if not clip_slot.has_clip:
                return {"error": "No clip in slot"}
            clip = clip_slot.clip
            if clip.is_midi_clip:
                return {"error": "RAM mode only applies to audio clips"}

            ram_mode = clip.ram_mode if hasattr(clip, 'ram_mode') else False
            return {"ram_mode": ram_mode}
        except Exception as e:
            self.log_message("Error getting clip ram mode: " + str(e))
            return {"error": str(e)}
    def _set_clip_ram_mode(self, track_index, clip_index, enabled):
        """Set whether an audio clip is loaded into RAM"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]
            clip_slots = list(track.clip_slots)
            if clip_index >= len(clip_slots):
                return {"error": "Clip index out of range"}
            clip_slot = clip_slots[clip_index]
            if not clip_slot.has_clip:
                return {"error": "No clip in slot"}
            clip = clip_slot.clip
            if clip.is_midi_clip:
                return {"error": "RAM mode only applies to audio clips"}

            clip.ram_mode = enabled
            return {"success": True, "ram_mode": enabled}
        except Exception as e:
            self.log_message("Error setting clip ram mode: " + str(e))
            return {"error": str(e)}
    def _get_audio_clip_file_path(self, track_index, clip_index):
        """Get the file path of an audio clip's sample"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]
            clip_slots = list(track.clip_slots)
            if clip_index >= len(clip_slots):
                return {"error": "Clip index out of range"}
            clip_slot = clip_slots[clip_index]
            if not clip_slot.has_clip:
                return {"error": "No clip in slot"}
            clip = clip_slot.clip
            if clip.is_midi_clip:
                return {"error": "File path only applies to audio clips"}

            file_path = clip.file_path if hasattr(clip, 'file_path') else None
            return {"file_path": file_path}
        except Exception as e:
            self.log_message("Error getting audio clip file path: " + str(e))
            return {"error": str(e)}
    def _get_clip_start_end_markers(self, track_index, clip_index):
        """Get clip start/end markers"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            clip_slot = tracks[track_index].clip_slots[clip_index]
            if not clip_slot.has_clip:
                return {"error": "No clip"}
            clip = clip_slot.clip
            return {"start_marker": clip.start_marker, "end_marker": clip.end_marker, "length": clip.length}
        except Exception as e:
            return {"error": str(e)}
    def _set_clip_start_marker(self, track_index, clip_index, position):
        """Set clip start marker"""
        try:
            tracks = list(self._song.tracks)
            clip = tracks[track_index].clip_slots[clip_index].clip
            clip.start_marker = position
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    def _set_clip_end_marker(self, track_index, clip_index, position):
        """Set clip end marker"""
        try:
            tracks = list(self._song.tracks)
            clip = tracks[track_index].clip_slots[clip_index].clip
            clip.end_marker = position
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    def _get_clip_trigger_quantization(self):
        """Get global clip trigger quantization"""
        try:
            return {"clip_trigger_quantization": self._song.clip_trigger_quantization}
        except Exception as e:
            return {"error": str(e)}
    def _set_clip_trigger_quantization(self, quant):
        """Set global clip trigger quantization"""
        try:
            self._song.clip_trigger_quantization = quant
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    def _get_groove_amount(self):
        """Get global groove amount"""
        try:
            return {"groove_amount": self._song.groove_amount if hasattr(self._song, 'groove_amount') else 1.0}
        except Exception as e:
            return {"error": str(e)}
    def _set_groove_amount(self, amount):
        """Set global groove amount"""
        try:
            self._song.groove_amount = max(0.0, min(1.0, amount))
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    def _get_clip_is_playing(self, track_index, clip_index):
        """Check if clip is playing"""
        try:
            clip = list(self._song.tracks)[track_index].clip_slots[clip_index].clip
            return {
                "is_playing": clip.is_playing,
                "is_triggered": clip.is_triggered,
                "playing_position": clip.playing_position if hasattr(clip, 'playing_position') else 0
            }
        except Exception as e:
            return {"error": str(e)}
    def _stop_all_clips(self):
        """Stop all playing clips"""
        try:
            self._song.stop_all_clips()
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    def _get_clip_velocity_amount(self, track_index, clip_index):
        """Get MIDI clip velocity amount"""
        try:
            clip = list(self._song.tracks)[track_index].clip_slots[clip_index].clip
            if not clip.is_midi_clip:
                return {"error": "Not MIDI clip"}
            return {"velocity_amount": clip.velocity_amount if hasattr(clip, 'velocity_amount') else 1.0}
        except Exception as e:
            return {"error": str(e)}
    def _set_clip_velocity_amount(self, track_index, clip_index, amount):
        """Set MIDI clip velocity amount"""
        try:
            clip = list(self._song.tracks)[track_index].clip_slots[clip_index].clip
            clip.velocity_amount = amount
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    def _get_clip_fades(self, track_index, clip_index):
        """Get audio clip fade settings"""
        try:
            clip = list(self._song.tracks)[track_index].clip_slots[clip_index].clip
            if clip.is_midi_clip:
                return {"error": "MIDI clips don't have fades"}
            return {
                "fade_in_start": clip.fade_in_start if hasattr(clip, 'fade_in_start') else None,
                "fade_in_end": clip.fade_in_end if hasattr(clip, 'fade_in_end') else None,
                "fade_out_start": clip.fade_out_start if hasattr(clip, 'fade_out_start') else None,
                "fade_out_end": clip.fade_out_end if hasattr(clip, 'fade_out_end') else None
            }
        except Exception as e:
            return {"error": str(e)}
    def _set_clip_fade_in(self, track_index, clip_index, start, end):
        """Set audio clip fade in"""
        try:
            clip = list(self._song.tracks)[track_index].clip_slots[clip_index].clip
            if clip.is_midi_clip:
                return {"error": "MIDI clips don't have fades"}
            if hasattr(clip, 'fade_in_start'):
                clip.fade_in_start = start
            if hasattr(clip, 'fade_in_end'):
                clip.fade_in_end = end
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    def _set_clip_fade_out(self, track_index, clip_index, start, end):
        """Set audio clip fade out"""
        try:
            clip = list(self._song.tracks)[track_index].clip_slots[clip_index].clip
            if clip.is_midi_clip:
                return {"error": "MIDI clips don't have fades"}
            if hasattr(clip, 'fade_out_start'):
                clip.fade_out_start = start
            if hasattr(clip, 'fade_out_end'):
                clip.fade_out_end = end
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    def _get_clip_start_time(self, track_index, clip_index):
        """Get clip start time"""
        try:
            clip = list(self._song.tracks)[track_index].clip_slots[clip_index].clip
            return {"start_time": clip.start_time if hasattr(clip, 'start_time') else clip.loop_start}
        except Exception as e:
            return {"error": str(e)}
    def _set_clip_start_time(self, track_index, clip_index, time):
        """Set clip start time"""
        try:
            clip = list(self._song.tracks)[track_index].clip_slots[clip_index].clip
            if hasattr(clip, 'start_time'):
                clip.start_time = time
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    def _get_clip_end_time(self, track_index, clip_index):
        """Get clip end time"""
        try:
            clip = list(self._song.tracks)[track_index].clip_slots[clip_index].clip
            return {"end_time": clip.end_time if hasattr(clip, 'end_time') else clip.loop_end}
        except Exception as e:
            return {"error": str(e)}
    def _set_clip_end_time(self, track_index, clip_index, time):
        """Set clip end time"""
        try:
            clip = list(self._song.tracks)[track_index].clip_slots[clip_index].clip
            if hasattr(clip, 'end_time'):
                clip.end_time = time
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    def _get_clip_playing_position(self, track_index, clip_index):
        """Get clip's current playing position"""
        try:
            clip = list(self._song.tracks)[track_index].clip_slots[clip_index].clip
            return {
                "playing_position": clip.playing_position if hasattr(clip, 'playing_position') else None,
                "is_playing": clip.is_playing,
                "is_triggered": clip.is_triggered
            }
        except Exception as e:
            return {"error": str(e)}
    def _duplicate_clip_loop(self, track_index, clip_index):
        """Duplicate clip loop (double length)"""
        try:
            clip = list(self._song.tracks)[track_index].clip_slots[clip_index].clip
            clip.duplicate_loop()
            return {"success": True, "new_length": clip.length}
        except Exception as e:
            return {"error": str(e)}
    def _get_clip_has_envelopes(self, track_index, clip_index):
        """Check if clip has automation envelopes"""
        try:
            clip = list(self._song.tracks)[track_index].clip_slots[clip_index].clip
            return {"has_envelopes": clip.has_envelopes if hasattr(clip, 'has_envelopes') else None}
        except Exception as e:
            return {"error": str(e)}
    # ---- command adapters (generated from the original dispatch chain) ----

    @command("get_clip_info")
    def cmd_get_clip_info(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._get_clip_info(track_index, clip_index)

    @command("get_clip_color")
    def cmd_get_clip_color(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._get_clip_color(track_index, clip_index)

    @command("get_clip_gain")
    def cmd_get_clip_gain(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._get_clip_gain(track_index, clip_index)

    @command("get_clip_pitch")
    def cmd_get_clip_pitch(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._get_clip_pitch(track_index, clip_index)

    @command("get_clip_loop")
    def cmd_get_clip_loop(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._get_clip_loop(track_index, clip_index)

    @command("get_warp_markers")
    def cmd_get_warp_markers(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._get_warp_markers(track_index, clip_index)

    @command("get_clip_launch_mode")
    def cmd_get_clip_launch_mode(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._get_clip_launch_mode(track_index, clip_index)

    @command("get_clip_launch_quantization")
    def cmd_get_clip_launch_quantization(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._get_clip_launch_quantization(track_index, clip_index)

    @command("get_clip_follow_action")
    def cmd_get_clip_follow_action(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._get_clip_follow_action(track_index, clip_index)

    @command("get_clip_ram_mode")
    def cmd_get_clip_ram_mode(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._get_clip_ram_mode(track_index, clip_index)

    @command("get_audio_clip_file_path")
    def cmd_get_audio_clip_file_path(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._get_audio_clip_file_path(track_index, clip_index)

    @command("get_clip_start_end_markers")
    def cmd_get_clip_start_end_markers(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._get_clip_start_end_markers(track_index, clip_index)

    @command("get_clip_is_playing")
    def cmd_get_clip_is_playing(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._get_clip_is_playing(track_index, clip_index)

    @command("get_clip_velocity_amount")
    def cmd_get_clip_velocity_amount(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._get_clip_velocity_amount(track_index, clip_index)

    @command("get_clip_trigger_quantization")
    def cmd_get_clip_trigger_quantization(self, params):
        return self._get_clip_trigger_quantization()

    @command("get_groove_amount")
    def cmd_get_groove_amount(self, params):
        return self._get_groove_amount()

    @command("get_clip_fades")
    def cmd_get_clip_fades(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._get_clip_fades(track_index, clip_index)

    @command("get_clip_start_time")
    def cmd_get_clip_start_time(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._get_clip_start_time(track_index, clip_index)

    @command("get_clip_end_time")
    def cmd_get_clip_end_time(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._get_clip_end_time(track_index, clip_index)

    @command("get_clip_playing_position")
    def cmd_get_clip_playing_position(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._get_clip_playing_position(track_index, clip_index)

    @command("get_clip_has_envelopes")
    def cmd_get_clip_has_envelopes(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._get_clip_has_envelopes(track_index, clip_index)

    @command("create_clip", modifying=True)
    def cmd_create_clip(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        length = params.get("length", 4.0)
        return self._create_clip(track_index, clip_index, length)

    @command("delete_clip", modifying=True)
    def cmd_delete_clip(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._delete_clip(track_index, clip_index)

    @command("set_clip_name", modifying=True)
    def cmd_set_clip_name(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        name = params.get("name", "")
        return self._set_clip_name(track_index, clip_index, name)

    @command("fire_clip", modifying=True)
    def cmd_fire_clip(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._fire_clip(track_index, clip_index)

    @command("stop_clip", modifying=True)
    def cmd_stop_clip(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._stop_clip(track_index, clip_index)

    @command("duplicate_clip", modifying=True)
    def cmd_duplicate_clip(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._duplicate_clip(track_index, clip_index)

    @command("set_clip_color", modifying=True)
    def cmd_set_clip_color(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        color = params.get("color", 0)
        return self._set_clip_color(track_index, clip_index, color)

    @command("set_clip_loop", modifying=True)
    def cmd_set_clip_loop(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        loop_start = params.get("loop_start", 0.0)
        loop_end = params.get("loop_end", 4.0)
        looping = params.get("looping", True)
        return self._set_clip_loop(track_index, clip_index, loop_start, loop_end, looping)

    @command("set_clip_gain", modifying=True)
    def cmd_set_clip_gain(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        gain = params.get("gain", 0.0)  # dB
        return self._set_clip_gain(track_index, clip_index, gain)

    @command("set_clip_pitch", modifying=True)
    def cmd_set_clip_pitch(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        pitch = params.get("pitch", 0)  # semitones
        return self._set_clip_pitch(track_index, clip_index, pitch)

    @command("set_clip_warp_mode", modifying=True)
    def cmd_set_clip_warp_mode(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        warp_mode = params.get("warp_mode", "beats")
        return self._set_clip_warp_mode(track_index, clip_index, warp_mode)

    @command("get_clip_warp_info", modifying=True)
    def cmd_get_clip_warp_info(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._get_clip_warp_info(track_index, clip_index)

    @command("add_warp_marker", modifying=True)
    def cmd_add_warp_marker(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        beat_time = params.get("beat_time", 0.0)
        sample_time = params.get("sample_time", None)
        return self._add_warp_marker(track_index, clip_index, beat_time, sample_time)

    @command("delete_warp_marker", modifying=True)
    def cmd_delete_warp_marker(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        beat_time = params.get("beat_time", 0.0)
        return self._delete_warp_marker(track_index, clip_index, beat_time)

    @command("get_clip_automation", modifying=True)
    def cmd_get_clip_automation(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        parameter_name = params.get("parameter_name", "")
        return self._get_clip_automation(track_index, clip_index, parameter_name)

    @command("set_clip_automation", modifying=True)
    def cmd_set_clip_automation(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        parameter_name = params.get("parameter_name", "")
        envelope_data = params.get("envelope_data", [])
        return self._set_clip_automation(track_index, clip_index, parameter_name, envelope_data)

    @command("clear_clip_automation", modifying=True)
    def cmd_clear_clip_automation(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        parameter_name = params.get("parameter_name", "")
        return self._clear_clip_automation(track_index, clip_index, parameter_name)

    @command("get_groove_pool", modifying=True)
    def cmd_get_groove_pool(self, params):
        return self._get_groove_pool()

    @command("apply_groove", modifying=True)
    def cmd_apply_groove(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        groove_index = params.get("groove_index", 0)
        return self._apply_groove(track_index, clip_index, groove_index)

    @command("commit_groove", modifying=True)
    def cmd_commit_groove(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._commit_groove(track_index, clip_index)

    @command("set_clip_launch_mode", modifying=True)
    def cmd_set_clip_launch_mode(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        mode = params.get("mode", 0)
        return self._set_clip_launch_mode(track_index, clip_index, mode)

    @command("set_clip_launch_quantization", modifying=True)
    def cmd_set_clip_launch_quantization(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        quantization = params.get("quantization", 0)
        return self._set_clip_launch_quantization(track_index, clip_index, quantization)

    @command("set_clip_follow_action", modifying=True)
    def cmd_set_clip_follow_action(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        action_a = params.get("action_a", None)
        action_b = params.get("action_b", None)
        chance = params.get("chance", None)
        time = params.get("time", None)
        return self._set_clip_follow_action(track_index, clip_index, action_a, action_b, chance, time)

    @command("set_clip_ram_mode", modifying=True)
    def cmd_set_clip_ram_mode(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        enabled = params.get("enabled", False)
        return self._set_clip_ram_mode(track_index, clip_index, enabled)

    @command("set_clip_start_marker", modifying=True)
    def cmd_set_clip_start_marker(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        position = params.get("position", 0)
        return self._set_clip_start_marker(track_index, clip_index, position)

    @command("set_clip_end_marker", modifying=True)
    def cmd_set_clip_end_marker(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        position = params.get("position", 0)
        return self._set_clip_end_marker(track_index, clip_index, position)

    @command("set_clip_velocity_amount", modifying=True)
    def cmd_set_clip_velocity_amount(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        amount = params.get("amount", 1.0)
        return self._set_clip_velocity_amount(track_index, clip_index, amount)

    @command("set_clip_trigger_quantization", modifying=True)
    def cmd_set_clip_trigger_quantization(self, params):
        quant = params.get("quantization", 4)
        return self._set_clip_trigger_quantization(quant)

    @command("set_groove_amount", modifying=True)
    def cmd_set_groove_amount(self, params):
        amount = params.get("amount", 1.0)
        return self._set_groove_amount(amount)

    @command("stop_all_clips", modifying=True)
    def cmd_stop_all_clips(self, params):
        return self._stop_all_clips()

    @command("set_clip_fade_in", modifying=True)
    def cmd_set_clip_fade_in(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        start = params.get("start", 0)
        end = params.get("end", 0)
        return self._set_clip_fade_in(track_index, clip_index, start, end)

    @command("set_clip_fade_out", modifying=True)
    def cmd_set_clip_fade_out(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        start = params.get("start", 0)
        end = params.get("end", 0)
        return self._set_clip_fade_out(track_index, clip_index, start, end)

    @command("set_clip_start_time", modifying=True)
    def cmd_set_clip_start_time(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        time = params.get("time", 0)
        return self._set_clip_start_time(track_index, clip_index, time)

    @command("set_clip_end_time", modifying=True)
    def cmd_set_clip_end_time(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        time = params.get("time", 0)
        return self._set_clip_end_time(track_index, clip_index, time)

    @command("duplicate_clip_loop", modifying=True)
    def cmd_duplicate_clip_loop(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._duplicate_clip_loop(track_index, clip_index)


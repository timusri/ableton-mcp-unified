"""Track command handlers.

The ``cmd_*`` adapters are registered through registry.py.
"""
import random
import traceback

from ..registry import command


class TrackHandlers(object):

    def _set_master_volume(self, volume):
        """Set master track volume (0.0 to 1.0)"""
        try:
            volume = self._clamp_volume(volume)
            self._song.master_track.mixer_device.volume.value = volume
            return {
                "volume": self._song.master_track.mixer_device.volume.value,
                "success": True
            }
        except Exception as e:
            self.log_message("Error setting master volume: " + str(e))
            raise
    def _set_master_pan(self, pan):
        """Set master track pan (-1.0 to 1.0)"""
        try:
            pan = self._clamp_pan(pan)
            self._song.master_track.mixer_device.panning.value = pan
            return {
                "panning": self._song.master_track.mixer_device.panning.value,
                "success": True
            }
        except Exception as e:
            self.log_message("Error setting master pan: " + str(e))
            raise
    def _get_master_info(self):
        """Get master track info including devices"""
        try:
            master = self._song.master_track
            devices = []
            for i, device in enumerate(master.devices):
                devices.append({
                    "index": i,
                    "name": device.name,
                    "class_name": device.class_name,
                    "is_active": device.is_active
                })

            return {
                "name": "Master",
                "volume": master.mixer_device.volume.value,
                "panning": master.mixer_device.panning.value,
                "device_count": len(master.devices),
                "devices": devices
            }
        except Exception as e:
            self.log_message("Error getting master info: " + str(e))
            raise
    def _create_midi_track(self, index):
        """Create a new MIDI track at the specified index"""
        try:
            # Create the track
            self._song.create_midi_track(index)
            
            # Get the new track
            new_track_index = len(self._song.tracks) - 1 if index == -1 else index
            new_track = self._song.tracks[new_track_index]
            
            result = {
                "index": new_track_index,
                "name": new_track.name
            }
            return result
        except Exception as e:
            self.log_message("Error creating MIDI track: " + str(e))
            raise
    def _create_audio_track(self, index):
        """Create a new audio track at the specified index"""
        try:
            self._song.create_audio_track(index)
            new_track_index = len(self._song.tracks) - 1 if index == -1 else index
            new_track = self._song.tracks[new_track_index]

            result = {
                "index": new_track_index,
                "name": new_track.name
            }
            return result
        except Exception as e:
            self.log_message("Error creating audio track: " + str(e))
            raise
    def _set_track_mute(self, track_index, mute):
        """Set the mute state of a track"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]
            track.mute = mute

            result = {
                "track_index": track_index,
                "mute": track.mute
            }
            return result
        except Exception as e:
            self.log_message("Error setting track mute: " + str(e))
            raise
    def _set_track_solo(self, track_index, solo):
        """Set the solo state of a track"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]
            track.solo = solo

            result = {
                "track_index": track_index,
                "solo": track.solo
            }
            return result
        except Exception as e:
            self.log_message("Error setting track solo: " + str(e))
            raise
    def _set_track_arm(self, track_index, arm):
        """Set the arm (record enable) state of a track"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]
            if track.can_be_armed:
                track.arm = arm
                result = {
                    "track_index": track_index,
                    "arm": track.arm
                }
            else:
                result = {
                    "track_index": track_index,
                    "arm": False,
                    "error": "Track cannot be armed"
                }
            return result
        except Exception as e:
            self.log_message("Error setting track arm: " + str(e))
            raise
    def _set_track_name(self, track_index, name):
        """Set the name of a track"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")
            
            # Set the name
            track = self._song.tracks[track_index]
            track.name = name
            
            result = {
                "name": track.name
            }
            return result
        except Exception as e:
            self.log_message("Error setting track name: " + str(e))
            raise
    def _duplicate_track(self, track_index):
        """Duplicate a track"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            self._song.duplicate_track(track_index)
            new_index = track_index + 1

            result = {
                "duplicated": True,
                "original_index": track_index,
                "new_index": new_index,
                "new_name": self._song.tracks[new_index].name
            }
            return result
        except Exception as e:
            self.log_message("Error duplicating track: " + str(e))
            raise
    def _set_track_color(self, track_index, color):
        """Set the color of a track"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]
            if hasattr(track, 'color_index'):
                track.color_index = color

            result = {
                "track_index": track_index,
                "color_index": track.color_index if hasattr(track, 'color_index') else None
            }
            return result
        except Exception as e:
            self.log_message("Error setting track color: " + str(e))
            raise
    def _get_return_tracks(self):
        """Get information about all return tracks"""
        try:
            return_tracks = []
            for i, track in enumerate(self._song.return_tracks):
                track_info = {
                    "index": i,
                    "name": track.name,
                    "color_index": track.color_index if hasattr(track, 'color_index') else None,
                    "mute": track.mute,
                    "solo": track.solo,
                    "volume": track.mixer_device.volume.value,
                    "panning": track.mixer_device.panning.value,
                    "device_count": len(track.devices)
                }
                return_tracks.append(track_info)

            result = {
                "return_track_count": len(return_tracks),
                "return_tracks": return_tracks
            }
            return result
        except Exception as e:
            self.log_message("Error getting return tracks: " + str(e))
            raise
    def _get_return_track_info(self, return_index):
        """Get detailed information about a return track"""
        try:
            if return_index < 0 or return_index >= len(self._song.return_tracks):
                raise IndexError("Return track index out of range")

            track = self._song.return_tracks[return_index]

            devices = []
            for i, device in enumerate(track.devices):
                devices.append({
                    "index": i,
                    "name": device.name,
                    "class_name": device.class_name
                })

            result = {
                "index": return_index,
                "name": track.name,
                "color_index": track.color_index if hasattr(track, 'color_index') else None,
                "mute": track.mute,
                "solo": track.solo,
                "volume": track.mixer_device.volume.value,
                "panning": track.mixer_device.panning.value,
                "devices": devices
            }
            return result
        except Exception as e:
            self.log_message("Error getting return track info: " + str(e))
            raise
    def _set_send_level(self, track_index, send_index, level):
        """Set the send level from a track to a return track"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]
            sends = track.mixer_device.sends

            if send_index < 0 or send_index >= len(sends):
                raise IndexError("Send index out of range")

            sends[send_index].value = max(0.0, min(1.0, level))

            result = {
                "track_index": track_index,
                "send_index": send_index,
                "level": sends[send_index].value
            }
            return result
        except Exception as e:
            self.log_message("Error setting send level: " + str(e))
            raise
    def _set_return_volume(self, return_index, volume):
        """Set the volume of a return track"""
        try:
            if return_index < 0 or return_index >= len(self._song.return_tracks):
                raise IndexError("Return track index out of range")

            track = self._song.return_tracks[return_index]
            track.mixer_device.volume.value = max(0.0, min(1.0, volume))

            result = {
                "return_index": return_index,
                "volume": track.mixer_device.volume.value
            }
            return result
        except Exception as e:
            self.log_message("Error setting return volume: " + str(e))
            raise
    def _set_return_pan(self, return_index, pan):
        """Set the panning of a return track"""
        try:
            if return_index < 0 or return_index >= len(self._song.return_tracks):
                raise IndexError("Return track index out of range")

            track = self._song.return_tracks[return_index]
            track.mixer_device.panning.value = max(-1.0, min(1.0, pan))

            result = {
                "return_index": return_index,
                "panning": track.mixer_device.panning.value
            }
            return result
        except Exception as e:
            self.log_message("Error setting return pan: " + str(e))
            raise
    def _create_group_track(self, track_indices, name):
        """Create a group track containing the specified tracks"""
        try:
            if not track_indices:
                raise ValueError("No tracks specified for grouping")

            # Validate all track indices
            for idx in track_indices:
                if idx < 0 or idx >= len(self._song.tracks):
                    raise IndexError("Track index {0} out of range".format(idx))

            # Sort indices in descending order for proper grouping
            sorted_indices = sorted(track_indices, reverse=True)

            # Select the tracks
            for idx in sorted_indices:
                self._song.tracks[idx].is_grouped = True

            # Create group - this may require using Live's grouping functionality
            # In Ableton's API, tracks can be grouped by setting is_part_of_selection
            # and using the song's create_group_track method if available

            if hasattr(self._song, 'create_group_track'):
                # Select the tracks first
                self._song.view.selected_track = self._song.tracks[sorted_indices[0]]
                group_track = self._song.create_group_track(sorted_indices[0])
                if name:
                    group_track.name = name

                return {
                    "created": True,
                    "group_track_index": list(self._song.tracks).index(group_track),
                    "grouped_tracks": track_indices,
                    "name": name
                }
            else:
                return {
                    "error": "Group track creation not supported in this Ableton version",
                    "note": "Try selecting tracks manually and using Cmd+G"
                }
        except Exception as e:
            self.log_message("Error creating group track: " + str(e))
            raise
    def _ungroup_tracks(self, group_track_index):
        """Ungroup a group track"""
        try:
            track = self._validate_track_index(group_track_index)

            if not track.is_foldable:
                raise ValueError("Track is not a group track")

            if hasattr(track, 'ungroup'):
                track.ungroup()
                return {"ungrouped": True, "track_index": group_track_index}
            else:
                return {"error": "Ungrouping not supported in this Ableton version"}
        except Exception as e:
            self.log_message("Error ungrouping tracks: " + str(e))
            raise
    def _fold_track(self, track_index, fold):
        """Fold or unfold a group track"""
        try:
            track = self._validate_track_index(track_index)

            if not track.is_foldable:
                raise ValueError("Track is not foldable (not a group track)")

            track.fold_state = fold

            return {
                "track_index": track_index,
                "folded": track.fold_state
            }
        except Exception as e:
            self.log_message("Error folding track: " + str(e))
            raise
    def _set_track_monitoring(self, track_index, monitoring):
        """Set track monitoring mode (in, auto, off)"""
        try:
            track = self._validate_track_index(track_index)

            if not track.can_be_armed:
                raise ValueError("Track cannot be monitored (not an audio/MIDI track)")

            # Monitoring states: 0=In, 1=Auto, 2=Off
            monitoring_map = {
                "in": 0,
                "auto": 1,
                "off": 2
            }

            mode = monitoring_map.get(monitoring.lower(), 1)
            track.current_monitoring_state = mode

            return {
                "track_index": track_index,
                "monitoring": monitoring,
                "monitoring_value": mode
            }
        except Exception as e:
            self.log_message("Error setting track monitoring: " + str(e))
            raise
    def _get_track_monitoring(self, track_index):
        """Get track monitoring mode"""
        try:
            track = self._validate_track_index(track_index)

            if not track.can_be_armed:
                return {"track_index": track_index, "monitoring": "n/a", "can_monitor": False}

            monitoring_names = ["in", "auto", "off"]
            state = track.current_monitoring_state

            return {
                "track_index": track_index,
                "monitoring": monitoring_names[state] if state < len(monitoring_names) else "unknown",
                "monitoring_value": state,
                "can_monitor": True
            }
        except Exception as e:
            self.log_message("Error getting track monitoring: " + str(e))
            raise
    def _get_track_color(self, track_index):
        """Get the color index of a track"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]
            return {"color_index": track.color_index}
        except Exception as e:
            self.log_message("Error getting track color: " + str(e))
            return {"error": str(e)}
    def _get_send_level(self, track_index, send_index):
        """Get the send level from a track to a return track"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]
            sends = list(track.mixer_device.sends)
            if send_index >= len(sends):
                return {"error": "Send index out of range (max: {0})".format(len(sends) - 1)}
            send = sends[send_index]
            return {
                "level": send.value,
                "min": send.min,
                "max": send.max,
                "name": send.name
            }
        except Exception as e:
            self.log_message("Error getting send level: " + str(e))
            return {"error": str(e)}
    def _get_track_playing_slot_index(self, track_index):
        """Get the index of the currently playing clip slot on a track"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]

            playing_slot_index = track.playing_slot_index if hasattr(track, 'playing_slot_index') else -1
            return {"playing_slot_index": playing_slot_index}
        except Exception as e:
            self.log_message("Error getting playing slot index: " + str(e))
            return {"error": str(e)}
    def _get_track_fired_slot_index(self, track_index):
        """Get the index of the most recently fired clip slot on a track"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]

            fired_slot_index = track.fired_slot_index if hasattr(track, 'fired_slot_index') else -1
            return {"fired_slot_index": fired_slot_index}
        except Exception as e:
            self.log_message("Error getting fired slot index: " + str(e))
            return {"error": str(e)}
    def _get_track_crossfade_assign(self, track_index):
        """Get the crossfade assignment of a track (A, B, or None)"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]

            # 0 = A, 1 = None, 2 = B
            assign = track.mixer_device.crossfade_assign if hasattr(track.mixer_device, 'crossfade_assign') else 1
            assign_names = {0: "A", 1: "None", 2: "B"}
            return {
                "crossfade_assign": assign,
                "crossfade_assign_name": assign_names.get(assign, "Unknown")
            }
        except Exception as e:
            self.log_message("Error getting track crossfade assign: " + str(e))
            return {"error": str(e)}
    def _set_track_crossfade_assign(self, track_index, assign):
        """Set the crossfade assignment of a track (0=A, 1=None, 2=B)"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]

            # Convert name to number if needed
            assign_names = {"a": 0, "none": 1, "b": 2}
            if isinstance(assign, str):
                assign = assign_names.get(assign.lower(), 1)

            track.mixer_device.crossfade_assign = assign
            return {"success": True, "crossfade_assign": assign}
        except Exception as e:
            self.log_message("Error setting track crossfade assign: " + str(e))
            return {"error": str(e)}
    def _get_track_output_meter(self, track_index):
        """Get the output meter level of a track (for metering)"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]

            result = {}
            if hasattr(track, 'output_meter_left'):
                result["output_meter_left"] = track.output_meter_left
            if hasattr(track, 'output_meter_right'):
                result["output_meter_right"] = track.output_meter_right
            if hasattr(track, 'output_meter_level'):
                result["output_meter_level"] = track.output_meter_level

            return result if result else {"error": "Metering not available"}
        except Exception as e:
            self.log_message("Error getting track output meter: " + str(e))
            return {"error": str(e)}
    def _get_track_delay(self, track_index):
        """Get track delay in ms"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]
            if hasattr(track.mixer_device, 'track_delay'):
                return {"track_delay": track.mixer_device.track_delay.value}
            return {"error": "Track delay not available"}
        except Exception as e:
            return {"error": str(e)}
    def _set_track_delay(self, track_index, delay_ms):
        """Set track delay in ms"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]
            if hasattr(track.mixer_device, 'track_delay'):
                track.mixer_device.track_delay.value = delay_ms
                return {"success": True}
            return {"error": "Track delay not available"}
        except Exception as e:
            return {"error": str(e)}
    def _get_track_is_grouped(self, track_index):
        """Check if track is in a group"""
        try:
            track = list(self._song.tracks)[track_index]
            return {"is_grouped": track.is_grouped if hasattr(track, 'is_grouped') else False}
        except Exception as e:
            return {"error": str(e)}
    def _get_track_is_foldable(self, track_index):
        """Check if track can be folded (is group track)"""
        try:
            track = list(self._song.tracks)[track_index]
            return {
                "is_foldable": track.is_foldable if hasattr(track, 'is_foldable') else False,
                "fold_state": track.fold_state if hasattr(track, 'fold_state') else None
            }
        except Exception as e:
            return {"error": str(e)}
    def _create_return_track(self):
        """Create return track"""
        try:
            self._song.create_return_track()
            return {"success": True, "count": len(list(self._song.return_tracks))}
        except Exception as e:
            return {"error": str(e)}
    def _delete_return_track(self, index):
        """Delete return track"""
        try:
            self._song.delete_return_track(index)
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    def _get_master_output_meter(self):
        """Get master output meter levels"""
        try:
            m = self._song.master_track
            return {
                "left": m.output_meter_left if hasattr(m, 'output_meter_left') else 0,
                "right": m.output_meter_right if hasattr(m, 'output_meter_right') else 0
            }
        except Exception as e:
            return {"error": str(e)}
    def _solo_exclusive(self, track_index):
        """Solo track exclusively"""
        try:
            for t in self._song.tracks:
                t.solo = False
            list(self._song.tracks)[track_index].solo = True
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    def _unsolo_all(self):
        """Unsolo all tracks"""
        try:
            for t in self._song.tracks:
                t.solo = False
            for t in self._song.return_tracks:
                t.solo = False
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    def _unmute_all(self):
        """Unmute all tracks"""
        try:
            for t in self._song.tracks:
                t.mute = False
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    def _get_send_pre_post(self, track_index, send_index):
        """Get send pre/post fader state"""
        try:
            track = list(self._song.tracks)[track_index]
            sends = list(track.mixer_device.sends)
            if send_index >= len(sends):
                return {"error": "Invalid send index"}
            # Note: pre_post is not directly accessible on sends in Live's LOM
            # Return what we can access
            return {
                "send_value": sends[send_index].value,
                "send_name": sends[send_index].name,
                "note": "pre/post state not directly accessible via LOM"
            }
        except Exception as e:
            return {"error": str(e)}
    def _get_track_implicit_arm(self, track_index):
        """Get track implicit arm state"""
        try:
            track = list(self._song.tracks)[track_index]
            return {"implicit_arm": track.implicit_arm if hasattr(track, 'implicit_arm') else None}
        except Exception as e:
            return {"error": str(e)}
    def _set_track_implicit_arm(self, track_index, enabled):
        """Set track implicit arm state"""
        try:
            track = list(self._song.tracks)[track_index]
            if hasattr(track, 'implicit_arm'):
                track.implicit_arm = enabled
                return {"success": True}
            return {"error": "Not available"}
        except Exception as e:
            return {"error": str(e)}
    def _get_track_capabilities(self, track_index):
        """Get track capabilities"""
        try:
            track = list(self._song.tracks)[track_index]
            return {
                "can_be_armed": track.can_be_armed,
                "has_midi_input": track.has_midi_input,
                "has_midi_output": track.has_midi_output,
                "has_audio_input": track.has_audio_input,
                "has_audio_output": track.has_audio_output,
                "is_visible": track.is_visible
            }
        except Exception as e:
            return {"error": str(e)}
    def _get_all_track_names(self):
        """Get all track names quickly"""
        try:
            return {
                "tracks": [{"index": i, "name": t.name} for i, t in enumerate(self._song.tracks)],
                "returns": [{"index": i, "name": t.name} for i, t in enumerate(self._song.return_tracks)],
                "master": self._song.master_track.name
            }
        except Exception as e:
            return {"error": str(e)}
    def _freeze_track(self, track_index):
        """Freeze a track to reduce CPU usage"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                return {"error": "Track index out of range"}
            track = list(self._song.tracks)[track_index]
            if hasattr(track, 'freeze'):
                track.freeze()
                return {"success": True, "track_index": track_index}
            return {"error": "Track cannot be frozen"}
        except Exception as e:
            return {"error": str(e)}
    def _flatten_track(self, track_index):
        """Flatten a frozen track to audio"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                return {"error": "Track index out of range"}
            track = list(self._song.tracks)[track_index]
            if hasattr(track, 'flatten'):
                track.flatten()
                return {"success": True, "track_index": track_index}
            return {"error": "Track cannot be flattened"}
        except Exception as e:
            return {"error": str(e)}
    def _unarm_all(self):
        """Unarm all tracks"""
        try:
            count = 0
            for track in self._song.tracks:
                if track.can_be_armed and track.arm:
                    track.arm = False
                    count += 1
            return {"success": True, "unarmed_count": count}
        except Exception as e:
            return {"error": str(e)}
    def _get_track_info(self, track_index):
        """Get information about a track"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")
            
            track = self._song.tracks[track_index]
            
            # Get clip slots
            clip_slots = []
            for slot_index, slot in enumerate(track.clip_slots):
                clip_info = None
                if slot.has_clip:
                    clip = slot.clip
                    clip_info = {
                        "name": clip.name,
                        "length": clip.length,
                        "is_playing": clip.is_playing,
                        "is_recording": clip.is_recording
                    }
                
                clip_slots.append({
                    "index": slot_index,
                    "has_clip": slot.has_clip,
                    "clip": clip_info
                })
            
            # Get devices
            devices = []
            for device_index, device in enumerate(track.devices):
                devices.append({
                    "index": device_index,
                    "name": device.name,
                    "class_name": device.class_name,
                    "type": self._get_device_type(device)
                })
            
            is_group = bool(getattr(track, "is_foldable", False))

            result = {
                "index": track_index,
                "name": track.name,
                "is_audio_track": track.has_audio_input,
                "is_midi_track": track.has_midi_input,
                "is_group_track": is_group,
                "mute": track.mute,
                "solo": track.solo,
                "arm": None if is_group else track.arm,
                "volume": track.mixer_device.volume.value,
                "panning": track.mixer_device.panning.value,
                "clip_slots": clip_slots,
                "devices": devices
            }
            return result
        except Exception as e:
            self.log_message("Error getting track info: " + str(e))
            raise
    def _get_track_volume(self, track_index):
        """Get current volume and panning for a track's mixer fader."""
        try:
            all_tracks = list(self._song.tracks) + list(self._song.return_tracks)
            if track_index < 0 or track_index >= len(all_tracks):
                raise IndexError("Track index {0} out of range (0-{1})".format(
                    track_index, len(all_tracks) - 1))
            track = all_tracks[track_index]
            vol_param = track.mixer_device.volume
            pan_param = track.mixer_device.panning
            return {
                "track_name": track.name,
                "volume": vol_param.value,
                "volume_min": vol_param.min,
                "volume_max": vol_param.max,
                "panning": pan_param.value,
                "panning_min": pan_param.min,
                "panning_max": pan_param.max,
            }
        except Exception as e:
            self.log_message("Error getting track volume: " + str(e))
            raise
    def _set_track_volume(self, track_index, volume):
        """Set the mixer fader volume for a track.
        
        Args:
            track_index: 0-based track index (includes return tracks after session tracks)
            volume: normalized 0.0 (silence) to 1.0 (max). 0.85 = 0dB unity gain.
        """
        try:
            all_tracks = list(self._song.tracks) + list(self._song.return_tracks)
            if track_index < 0 or track_index >= len(all_tracks):
                raise IndexError("Track index {0} out of range (0-{1})".format(
                    track_index, len(all_tracks) - 1))
            track = all_tracks[track_index]
            vol_param = track.mixer_device.volume
            # Clamp to valid range
            clamped = max(vol_param.min, min(vol_param.max, float(volume)))
            vol_param.value = clamped
            return {
                "track_name": track.name,
                "volume": vol_param.value,
            }
        except Exception as e:
            self.log_message("Error setting track volume: " + str(e))
            raise
    def _set_track_panning(self, track_index, panning):
        """Set the mixer panning for a track.
        
        Args:
            track_index: 0-based track index
            panning: -1.0 (full left) to +1.0 (full right), 0.0 = center
        """
        try:
            all_tracks = list(self._song.tracks) + list(self._song.return_tracks)
            if track_index < 0 or track_index >= len(all_tracks):
                raise IndexError("Track index {0} out of range (0-{1})".format(
                    track_index, len(all_tracks) - 1))
            track = all_tracks[track_index]
            pan_param = track.mixer_device.panning
            clamped = max(pan_param.min, min(pan_param.max, float(panning)))
            pan_param.value = clamped
            return {
                "track_name": track.name,
                "panning": pan_param.value,
            }
        except Exception as e:
            self.log_message("Error setting track panning: " + str(e))
            raise
    def _delete_track(self, track_index):
        """Delete a track from the session."""
        try:
            if len(self._song.tracks) <= 1:
                raise ValueError(
                    "Cannot delete the last remaining session track. "
                    "Ableton must always have at least one track."
                )
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index {0} out of range (0-{1})".format(
                    track_index, len(self._song.tracks) - 1))
            track_name = self._song.tracks[track_index].name
            self._song.delete_track(track_index)
            return {
                "deleted_track": track_name,
                "remaining_tracks": len(self._song.tracks),
            }
        except Exception as e:
            self.log_message("Error deleting track: " + str(e))
            raise
    # ---- unified additions ----

    @command("get_track_info")
    def cmd_get_track_info(self, params):
        track_index = params.get("track_index", 0)
        return self._get_track_info(track_index)

    @command("get_track_volume")
    def cmd_get_track_volume(self, params):
        track_index = params.get("track_index", 0)
        return self._get_track_volume(track_index)

    @command("set_track_volume", modifying=True)
    def cmd_set_track_volume(self, params):
        track_index = params.get("track_index", 0)
        volume = params.get("volume", 0.85)
        return self._set_track_volume(track_index, volume)

    @command("set_track_panning", modifying=True, aliases=("set_track_pan",))
    def cmd_set_track_panning(self, params):
        track_index = params.get("track_index", 0)
        panning = params.get("panning", params.get("pan", 0.0))
        result = self._set_track_panning(track_index, panning)
        result["pan"] = result["panning"]
        return result

    @command("delete_track", modifying=True)
    def cmd_delete_track(self, params):
        track_index = params.get("track_index", 0)
        return self._delete_track(track_index)
    # ---- command adapters (generated from the original dispatch chain) ----

    @command("get_return_tracks")
    def cmd_get_return_tracks(self, params):
        return self._get_return_tracks()

    @command("get_return_track_info")
    def cmd_get_return_track_info(self, params):
        return_index = params.get("return_index", 0)
        return self._get_return_track_info(return_index)

    @command("get_track_color")
    def cmd_get_track_color(self, params):
        track_index = params.get("track_index", 0)
        return self._get_track_color(track_index)

    @command("get_send_level")
    def cmd_get_send_level(self, params):
        track_index = params.get("track_index", 0)
        send_index = params.get("send_index", 0)
        return self._get_send_level(track_index, send_index)

    @command("get_track_playing_slot_index")
    def cmd_get_track_playing_slot_index(self, params):
        track_index = params.get("track_index", 0)
        return self._get_track_playing_slot_index(track_index)

    @command("get_track_fired_slot_index")
    def cmd_get_track_fired_slot_index(self, params):
        track_index = params.get("track_index", 0)
        return self._get_track_fired_slot_index(track_index)

    @command("get_track_output_meter")
    def cmd_get_track_output_meter(self, params):
        track_index = params.get("track_index", 0)
        return self._get_track_output_meter(track_index)

    @command("get_track_crossfade_assign")
    def cmd_get_track_crossfade_assign(self, params):
        track_index = params.get("track_index", 0)
        return self._get_track_crossfade_assign(track_index)

    @command("get_track_delay")
    def cmd_get_track_delay(self, params):
        track_index = params.get("track_index", 0)
        return self._get_track_delay(track_index)

    @command("get_track_is_grouped")
    def cmd_get_track_is_grouped(self, params):
        track_index = params.get("track_index", 0)
        return self._get_track_is_grouped(track_index)

    @command("get_track_is_foldable")
    def cmd_get_track_is_foldable(self, params):
        track_index = params.get("track_index", 0)
        return self._get_track_is_foldable(track_index)

    @command("get_master_output_meter")
    def cmd_get_master_output_meter(self, params):
        return self._get_master_output_meter()

    @command("get_send_pre_post")
    def cmd_get_send_pre_post(self, params):
        track_index = params.get("track_index", 0)
        send_index = params.get("send_index", 0)
        return self._get_send_pre_post(track_index, send_index)

    @command("get_track_capabilities")
    def cmd_get_track_capabilities(self, params):
        track_index = params.get("track_index", 0)
        return self._get_track_capabilities(track_index)

    @command("get_track_implicit_arm")
    def cmd_get_track_implicit_arm(self, params):
        track_index = params.get("track_index", 0)
        return self._get_track_implicit_arm(track_index)

    @command("get_all_track_names")
    def cmd_get_all_track_names(self, params):
        return self._get_all_track_names()

    @command("create_midi_track", modifying=True)
    def cmd_create_midi_track(self, params):
        index = params.get("index", -1)
        return self._create_midi_track(index)

    @command("create_audio_track", modifying=True)
    def cmd_create_audio_track(self, params):
        index = params.get("index", -1)
        return self._create_audio_track(index)

    @command("set_track_name", modifying=True)
    def cmd_set_track_name(self, params):
        track_index = params.get("track_index", 0)
        name = params.get("name", "")
        return self._set_track_name(track_index, name)

    @command("set_track_mute", modifying=True)
    def cmd_set_track_mute(self, params):
        track_index = params.get("track_index", 0)
        mute = params.get("mute", False)
        return self._set_track_mute(track_index, mute)

    @command("set_track_solo", modifying=True)
    def cmd_set_track_solo(self, params):
        track_index = params.get("track_index", 0)
        solo = params.get("solo", False)
        return self._set_track_solo(track_index, solo)

    @command("set_track_arm", modifying=True)
    def cmd_set_track_arm(self, params):
        track_index = params.get("track_index", 0)
        arm = params.get("arm", False)
        return self._set_track_arm(track_index, arm)

    @command("duplicate_track", modifying=True)
    def cmd_duplicate_track(self, params):
        track_index = params.get("track_index", 0)
        return self._duplicate_track(track_index)

    @command("set_track_color", modifying=True)
    def cmd_set_track_color(self, params):
        track_index = params.get("track_index", 0)
        color = params.get("color", 0)
        return self._set_track_color(track_index, color)

    @command("set_send_level", modifying=True)
    def cmd_set_send_level(self, params):
        track_index = params.get("track_index", 0)
        send_index = params.get("send_index", 0)
        level = params.get("level", 0.0)
        return self._set_send_level(track_index, send_index, level)

    @command("set_return_volume", modifying=True)
    def cmd_set_return_volume(self, params):
        return_index = params.get("return_index", 0)
        volume = params.get("volume", 0.85)
        return self._set_return_volume(return_index, volume)

    @command("set_return_pan", modifying=True)
    def cmd_set_return_pan(self, params):
        return_index = params.get("return_index", 0)
        pan = params.get("pan", 0.0)
        return self._set_return_pan(return_index, pan)

    @command("create_group_track", modifying=True)
    def cmd_create_group_track(self, params):
        track_indices = params.get("track_indices", [])
        name = params.get("name", "Group")
        return self._create_group_track(track_indices, name)

    @command("ungroup_tracks", modifying=True)
    def cmd_ungroup_tracks(self, params):
        group_track_index = params.get("group_track_index", 0)
        return self._ungroup_tracks(group_track_index)

    @command("fold_track", modifying=True)
    def cmd_fold_track(self, params):
        track_index = params.get("track_index", 0)
        return self._fold_track(track_index, True)

    @command("unfold_track", modifying=True)
    def cmd_unfold_track(self, params):
        track_index = params.get("track_index", 0)
        return self._fold_track(track_index, False)

    @command("set_track_monitoring", modifying=True)
    def cmd_set_track_monitoring(self, params):
        track_index = params.get("track_index", 0)
        monitoring = params.get("monitoring", "auto")
        return self._set_track_monitoring(track_index, monitoring)

    @command("get_track_monitoring", modifying=True)
    def cmd_get_track_monitoring(self, params):
        track_index = params.get("track_index", 0)
        return self._get_track_monitoring(track_index)

    @command("set_track_crossfade_assign", modifying=True)
    def cmd_set_track_crossfade_assign(self, params):
        track_index = params.get("track_index", 0)
        assign = params.get("assign", 1)
        return self._set_track_crossfade_assign(track_index, assign)

    @command("set_track_delay", modifying=True)
    def cmd_set_track_delay(self, params):
        track_index = params.get("track_index", 0)
        delay_ms = params.get("delay_ms", 0)
        return self._set_track_delay(track_index, delay_ms)

    @command("create_return_track", modifying=True)
    def cmd_create_return_track(self, params):
        return self._create_return_track()

    @command("delete_return_track", modifying=True)
    def cmd_delete_return_track(self, params):
        index = params.get("index", 0)
        return self._delete_return_track(index)

    @command("solo_exclusive", modifying=True)
    def cmd_solo_exclusive(self, params):
        track_index = params.get("track_index", 0)
        return self._solo_exclusive(track_index)

    @command("unsolo_all", modifying=True)
    def cmd_unsolo_all(self, params):
        return self._unsolo_all()

    @command("unmute_all", modifying=True)
    def cmd_unmute_all(self, params):
        return self._unmute_all()

    @command("unarm_all", modifying=True)
    def cmd_unarm_all(self, params):
        return self._unarm_all()

    @command("freeze_track", modifying=True)
    def cmd_freeze_track(self, params):
        track_index = params.get("track_index", 0)
        return self._freeze_track(track_index)

    @command("flatten_track", modifying=True)
    def cmd_flatten_track(self, params):
        track_index = params.get("track_index", 0)
        return self._flatten_track(track_index)

    @command("set_track_implicit_arm", modifying=True)
    def cmd_set_track_implicit_arm(self, params):
        track_index = params.get("track_index", 0)
        enabled = params.get("enabled", False)
        return self._set_track_implicit_arm(track_index, enabled)

    @command("set_master_volume", modifying=True)
    def cmd_set_master_volume(self, params):
        volume = params.get("volume", 0.85)
        return self._set_master_volume(volume)

    @command("set_master_pan", modifying=True)
    def cmd_set_master_pan(self, params):
        pan = params.get("pan", 0.0)
        return self._set_master_pan(pan)

    @command("get_master_info")
    def cmd_get_master_info(self, params):
        return self._get_master_info()


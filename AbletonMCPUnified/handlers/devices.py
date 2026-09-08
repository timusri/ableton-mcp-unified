"""Device command handlers.

The ``cmd_*`` adapters are registered through registry.py.
"""
import random
import traceback

from ..registry import command
from . import _notes_api as notes_api


class DeviceHandlers(object):

    def _generate_drum_pattern(self, track_index, clip_index, style, length):
        """Generate a drum pattern"""
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

            # Drum mappings (General MIDI)
            KICK = 36
            SNARE = 38
            CLOSED_HH = 42
            OPEN_HH = 46
            CLAP = 39

            notes = []
            beats = int(length)

            if style == "basic":
                # Basic 4/4 pattern
                for beat in range(beats):
                    # Kick on 1 and 3
                    if beat % 2 == 0:
                        notes.append((KICK, float(beat), 0.25, 100, False))
                    # Snare on 2 and 4
                    if beat % 2 == 1:
                        notes.append((SNARE, float(beat), 0.25, 100, False))
                    # Hi-hat on every 8th
                    for eighth in range(2):
                        notes.append((CLOSED_HH, beat + eighth * 0.5, 0.25, 80, False))

            elif style == "house":
                # House pattern - 4 on the floor
                for beat in range(beats):
                    notes.append((KICK, float(beat), 0.25, 110, False))
                    if beat % 2 == 1:
                        notes.append((CLAP, float(beat), 0.25, 100, False))
                    # Offbeat hi-hats
                    notes.append((OPEN_HH, beat + 0.5, 0.25, 90, False))

            elif style == "hiphop":
                # Hip-hop pattern
                for beat in range(beats):
                    # Kick pattern
                    if beat % 4 == 0:
                        notes.append((KICK, float(beat), 0.25, 110, False))
                    if beat % 4 == 2:
                        notes.append((KICK, beat + 0.75, 0.25, 90, False))
                    # Snare on 2 and 4
                    if beat % 2 == 1:
                        notes.append((SNARE, float(beat), 0.25, 100, False))
                    # Hi-hats
                    for eighth in range(2):
                        vel = 80 if eighth == 0 else 60
                        notes.append((CLOSED_HH, beat + eighth * 0.5, 0.25, vel, False))

            elif style == "dnb":
                # Drum and bass pattern
                for beat in range(beats):
                    # Two-step kick pattern
                    if beat % 4 == 0:
                        notes.append((KICK, float(beat), 0.25, 110, False))
                    if beat % 4 == 2:
                        notes.append((KICK, beat + 0.5, 0.25, 100, False))
                    # Snare on 2 and 4
                    if beat % 2 == 1:
                        notes.append((SNARE, float(beat), 0.25, 110, False))
                    # Fast hi-hats
                    for sixteenth in range(4):
                        vel = 70 + random.randint(-10, 10)
                        notes.append((CLOSED_HH, beat + sixteenth * 0.25, 0.125, vel, False))

            else:  # Random/experimental
                for beat in range(beats):
                    if random.random() > 0.3:
                        notes.append((KICK, beat + random.choice([0, 0.5]), 0.25, random.randint(80, 110), False))
                    if random.random() > 0.5:
                        notes.append((SNARE, beat + random.choice([0, 0.25, 0.5]), 0.25, random.randint(80, 100), False))
                    if random.random() > 0.2:
                        notes.append((CLOSED_HH, beat + random.random() * 0.5, 0.25, random.randint(60, 90), False))

            notes_api.add_notes(clip, notes)

            result = {
                "generated": True,
                "style": style,
                "length": length,
                "note_count": len(notes)
            }
            return result
        except Exception as e:
            self.log_message("Error generating drum pattern: " + str(e))
            raise
    def _get_device_by_name(self, track_index, device_name):
        """Find a device by name and return its info"""
        try:
            track = self._validate_track_index(track_index)

            for i, device in enumerate(track.devices):
                if device.name.lower() == device_name.lower():
                    params = []
                    for j, param in enumerate(device.parameters):
                        params.append({
                            "index": j,
                            "name": param.name,
                            "value": param.value,
                            "min": param.min,
                            "max": param.max
                        })

                    return {
                        "found": True,
                        "device_index": i,
                        "name": device.name,
                        "class_name": device.class_name,
                        "is_active": device.is_active,
                        "parameters": params
                    }

            return {
                "found": False,
                "device_name": device_name,
                "available_devices": [d.name for d in track.devices]
            }
        except Exception as e:
            self.log_message("Error getting device by name: " + str(e))
            raise
    def _load_device_preset(self, track_index, device_index, preset_uri):
        """Load a preset onto a device"""
        try:
            track = self._validate_track_index(track_index)
            device = self._validate_device_index(track, device_index)

            app = self.application()
            browser = app.browser

            # Find preset in browser
            item = self._find_browser_item_by_uri(browser, preset_uri)

            if not item:
                return {"error": "Preset not found: " + preset_uri}

            if not item.is_loadable:
                return {"error": "Item is not loadable"}

            # Select the device first, then load preset
            self._song.view.selected_track = track
            # Note: Loading presets directly onto devices may require
            # using the browser's hot-swap functionality

            if hasattr(browser, 'hotswap_target'):
                browser.hotswap_target = device
                browser.load_item(item)
                return {
                    "loaded": True,
                    "preset_name": item.name,
                    "device_name": device.name
                }
            else:
                return {"error": "Preset loading not fully supported"}
        except Exception as e:
            self.log_message("Error loading device preset: " + str(e))
            raise
    def _get_drum_rack_pads(self, track_index, device_index):
        """Get info about all pads in a drum rack"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]
            devices = list(track.devices)
            if device_index >= len(devices):
                return {"error": "Device index out of range"}
            device = devices[device_index]

            if not device.can_have_drum_pads:
                return {"error": "Device is not a drum rack"}

            pads = []
            if hasattr(device, 'drum_pads'):
                for pad in device.drum_pads:
                    pad_info = {
                        "note": pad.note,
                        "name": pad.name,
                        "mute": pad.mute,
                        "solo": pad.solo
                    }
                    if hasattr(pad, 'chains') and pad.chains:
                        pad_info["has_chain"] = True
                    pads.append(pad_info)

            return {"pads": pads, "count": len(pads)}
        except Exception as e:
            self.log_message("Error getting drum rack pads: " + str(e))
            return {"error": str(e)}
    def _set_drum_rack_pad_mute(self, track_index, device_index, note, mute):
        """Mute/unmute a drum rack pad by note number"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]
            devices = list(track.devices)
            if device_index >= len(devices):
                return {"error": "Device index out of range"}
            device = devices[device_index]

            if not device.can_have_drum_pads:
                return {"error": "Device is not a drum rack"}

            for pad in device.drum_pads:
                if pad.note == note:
                    pad.mute = mute
                    return {"success": True, "note": note, "mute": mute}

            return {"error": "Pad not found for note {0}".format(note)}
        except Exception as e:
            self.log_message("Error setting drum rack pad mute: " + str(e))
            return {"error": str(e)}
    def _set_drum_rack_pad_solo(self, track_index, device_index, note, solo):
        """Solo/unsolo a drum rack pad by note number"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]
            devices = list(track.devices)
            if device_index >= len(devices):
                return {"error": "Device index out of range"}
            device = devices[device_index]

            if not device.can_have_drum_pads:
                return {"error": "Device is not a drum rack"}

            for pad in device.drum_pads:
                if pad.note == note:
                    pad.solo = solo
                    return {"success": True, "note": note, "solo": solo}

            return {"error": "Pad not found for note {0}".format(note)}
        except Exception as e:
            self.log_message("Error setting drum rack pad solo: " + str(e))
            return {"error": str(e)}
    def _get_rack_macros(self, track_index, device_index):
        """Get all macro knob values from a rack device"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]
            devices = list(track.devices)
            if device_index >= len(devices):
                return {"error": "Device index out of range"}
            device = devices[device_index]

            if not device.can_have_chains:
                return {"error": "Device is not a rack"}

            macros = []
            # Macros are typically the first 8 or 16 parameters
            if hasattr(device, 'parameters'):
                for i, param in enumerate(device.parameters):
                    if 'Macro' in param.name or i < 8:  # First 8 are usually macros
                        macros.append({
                            "index": i,
                            "name": param.name,
                            "value": param.value,
                            "min": param.min,
                            "max": param.max
                        })

            return {"macros": macros, "count": len(macros)}
        except Exception as e:
            self.log_message("Error getting rack macros: " + str(e))
            return {"error": str(e)}
    def _set_rack_macro(self, track_index, device_index, macro_index, value):
        """Set a macro knob value on a rack device"""
        try:
            tracks = list(self._song.tracks)
            if track_index >= len(tracks):
                return {"error": "Track index out of range"}
            track = tracks[track_index]
            devices = list(track.devices)
            if device_index >= len(devices):
                return {"error": "Device index out of range"}
            device = devices[device_index]

            if not device.can_have_chains:
                return {"error": "Device is not a rack"}

            if macro_index >= len(device.parameters):
                return {"error": "Macro index out of range"}

            param = device.parameters[macro_index]
            param.value = max(param.min, min(param.max, value))
            return {"success": True, "macro_index": macro_index, "value": param.value}
        except Exception as e:
            self.log_message("Error setting rack macro: " + str(e))
            return {"error": str(e)}
    def _move_device(self, track_index, device_index, new_index):
        """Move device to new position"""
        try:
            track = list(self._song.tracks)[track_index]
            device = list(track.devices)[device_index]
            self._song.move_device(device, track, new_index)
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    def _get_device_view_state(self, track_index, device_index):
        """Get device view state"""
        try:
            device = list(self._song.tracks)[track_index].devices[device_index]
            return {
                "name": device.name,
                "is_active": device.is_active,
                "is_collapsed": device.view.is_collapsed if hasattr(device, 'view') and hasattr(device.view, 'is_collapsed') else None
            }
        except Exception as e:
            return {"error": str(e)}
    def _set_device_collapsed(self, track_index, device_index, collapsed):
        """Set device collapsed state"""
        try:
            device = list(self._song.tracks)[track_index].devices[device_index]
            if hasattr(device, 'view') and hasattr(device.view, 'is_collapsed'):
                device.view.is_collapsed = collapsed
                return {"success": True}
            return {"error": "Not available"}
        except Exception as e:
            return {"error": str(e)}
    def _select_device(self, track_index, device_index):
        """Select device for viewing"""
        try:
            device = list(self._song.tracks)[track_index].devices[device_index]
            self._song.view.select_device(device)
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    def _get_selected_device(self):
        """Get currently selected device"""
        try:
            track = self._song.view.selected_track
            device = track.view.selected_device if hasattr(track, 'view') else None
            if device:
                for di, d in enumerate(track.devices):
                    if d == device:
                        return {"device_index": di, "name": device.name, "class_name": device.class_name}
            return {"device": None}
        except Exception as e:
            return {"error": str(e)}
    def _set_drum_pad_note(self, track_index, device_index, pad_index, note):
        """Set drum pad MIDI note"""
        try:
            device = list(self._song.tracks)[track_index].devices[device_index]
            if not hasattr(device, 'drum_pads'):
                return {"error": "Not a Drum Rack"}
            # Note: drum pad note mapping is read-only in LOM
            return {"error": "Drum pad note is read-only"}
        except Exception as e:
            return {"error": str(e)}
    def _set_drum_pad_name(self, track_index, device_index, pad_index, name):
        """Set drum pad name"""
        try:
            device = list(self._song.tracks)[track_index].devices[device_index]
            if not hasattr(device, 'drum_pads'):
                return {"error": "Not a Drum Rack"}
            pad = list(device.drum_pads)[pad_index]
            pad.name = name
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    def _get_simpler_sample_info(self, track_index, device_index):
        """Get Simpler/Sampler sample info"""
        try:
            device = list(self._song.tracks)[track_index].devices[device_index]
            if device.class_name not in ['OriginalSimpler', 'MultiSampler']:
                return {"error": "Not Simpler or Sampler"}
            sample = device.sample if hasattr(device, 'sample') else None
            if not sample:
                return {"sample": None}
            return {
                "file_path": sample.file_path if hasattr(sample, 'file_path') else None,
                "length": sample.length if hasattr(sample, 'length') else None,
                "sample_rate": sample.sample_rate if hasattr(sample, 'sample_rate') else None
            }
        except Exception as e:
            return {"error": str(e)}
    def _get_simpler_parameters(self, track_index, device_index):
        """Get Simpler playback parameters"""
        try:
            device = list(self._song.tracks)[track_index].devices[device_index]
            params = {}
            for p in device.parameters:
                params[p.name] = {
                    "value": p.value,
                    "min": p.min,
                    "max": p.max
                }
            return {"parameters": params}
        except Exception as e:
            return {"error": str(e)}
    def _move_device_left(self, track_index, device_index):
        """Move device one position to the left"""
        try:
            if device_index <= 0:
                return {"error": "Device already at leftmost position"}
            track = list(self._song.tracks)[track_index]
            device = list(track.devices)[device_index]
            new_index = device_index - 1
            self._song.move_device(device, track, new_index)
            return {"success": True, "new_index": new_index}
        except Exception as e:
            return {"error": str(e)}
    def _move_device_right(self, track_index, device_index):
        """Move device one position to the right"""
        try:
            track = list(self._song.tracks)[track_index]
            device_count = len(list(track.devices))
            if device_index >= device_count - 1:
                return {"error": "Device already at rightmost position"}
            device = list(track.devices)[device_index]
            new_index = device_index + 1
            self._song.move_device(device, track, new_index)
            return {"success": True, "new_index": new_index}
        except Exception as e:
            return {"error": str(e)}
    def _get_device_parameters(self, track_index, device_index, chain_index=None, show_all=False):
        """Return parameter list for a device."""
        try:
            track, device = self._resolve_device(track_index, device_index)

            # If chain_index, navigate into chain
            target_device = device
            if chain_index is not None:
                if not device.can_have_chains:
                    raise ValueError("Device '{0}' is not a rack".format(device.name))
                chains = device.chains
                if chain_index < 0 or chain_index >= len(chains):
                    raise IndexError("Chain index {0} out of range".format(chain_index))
                chain = chains[chain_index]
                if not chain.devices:
                    raise ValueError("Chain '{0}' has no devices".format(chain.name))
                target_device = chain.devices[0]

            params = target_device.parameters
            param_list = []
            for i, p in enumerate(params):
                pmin = p.min
                pmax = p.max
                raw_val = p.value
                norm = (raw_val - pmin) / (pmax - pmin) if pmax != pmin else 0.0
                entry = {
                    "index": i,
                    "name": p.name,
                    "value": round(norm, 4),
                    "min": pmin,
                    "max": pmax,
                    "display_value": str(p),
                    "is_enabled": p.is_enabled,
                    "is_quantized": p.is_quantized,
                    "value_items": list(p.value_items) if p.is_quantized else [],
                }
                param_list.append(entry)

            result = {
                "device_name": target_device.name,
                "device_class": target_device.class_name,
                "parameter_count": len(params),
                "parameters": param_list,
            }
            return result
        except Exception as e:
            self.log_message("Error getting device parameters: " + str(e))
            raise
    def _set_device_enabled(self, track_index, device_index, chain_index=None, enabled=True):
        """Enable or disable a device via its 'Device On' parameter."""
        try:
            track, device = self._resolve_device(track_index, device_index)

            target_device = device
            if chain_index is not None:
                if not device.can_have_chains:
                    raise ValueError("Device '{0}' is not a rack".format(device.name))
                chain = device.chains[chain_index]
                if not chain.devices:
                    raise ValueError("Chain has no devices")
                target_device = chain.devices[0]

            # Use "Device On" parameter (always index 0) instead of
            # is_active which is read-only in the Live API.
            params = target_device.parameters
            if not params:
                raise ValueError("Device '{0}' has no parameters".format(target_device.name))
            on_param = params[0]
            on_param.value = on_param.max if enabled else on_param.min

            return {
                "device_name": target_device.name,
                "is_active": enabled,
            }
        except Exception as e:
            self.log_message("Error setting device enabled: " + str(e))
            raise
    def _delete_device(self, track_index, device_index):
        """Delete a device from a track."""
        try:
            track, device = self._resolve_device(track_index, device_index)
            device_name = device.name
            track.delete_device(device_index)
            return {
                "deleted_device": device_name,
                "remaining_devices": len(track.devices),
            }
        except Exception as e:
            self.log_message("Error deleting device: " + str(e))
            raise
    def _navigate_preset(self, track_index, device_index, chain_index=None, direction="current"):
        """Navigate device presets."""
        try:
            track, device = self._resolve_device(track_index, device_index)

            target_device = device
            if chain_index is not None:
                if not device.can_have_chains:
                    raise ValueError("Device '{0}' is not a rack".format(device.name))
                chain = device.chains[chain_index]
                if not chain.devices:
                    raise ValueError("Chain has no devices")
                target_device = chain.devices[0]

            if not hasattr(target_device, 'presets') or not target_device.presets:
                raise ValueError("Device '{0}' has no presets available".format(
                    target_device.name))

            presets = list(target_device.presets)
            current_idx = target_device.selected_preset_index

            if direction == "next":
                new_idx = min(current_idx + 1, len(presets) - 1)
                target_device.selected_preset_index = new_idx
            elif direction == "previous":
                new_idx = max(current_idx - 1, 0)
                target_device.selected_preset_index = new_idx
            elif direction == "current":
                new_idx = current_idx
            else:
                raise ValueError("Invalid direction: {0}".format(direction))

            return {
                "device_name": target_device.name,
                "preset_name": presets[new_idx] if new_idx < len(presets) else "",
                "preset_index": new_idx,
                "preset_count": len(presets),
            }
        except Exception as e:
            self.log_message("Error navigating preset: " + str(e))
            raise
    def _resolve_device(self, track_index, device_index, chain_index=None):
        """Resolve a device reference to (track, device) tuple.

        Parameters:
        - track_index: 0-based track index
        - device_index: 0-based device index on track (or within chain)
        - chain_index: optional 0-based chain index for rack devices

        Returns (track, device) tuple.
        Raises IndexError or ValueError on invalid references.
        """
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index {0} out of range (0-{1})".format(
                track_index, len(self._song.tracks) - 1))

        track = self._song.tracks[track_index]

        if device_index < 0 or device_index >= len(track.devices):
            raise IndexError("Device index {0} out of range on track '{1}' (0-{2})".format(
                device_index, track.name,
                len(track.devices) - 1 if track.devices else 0))

        device = track.devices[device_index]

        if chain_index is not None:
            # Navigate into rack chain
            if not device.can_have_chains:
                raise ValueError("Device '{0}' is not a rack and has no chains".format(device.name))
            chains = device.chains
            if chain_index < 0 or chain_index >= len(chains):
                raise IndexError("Chain index {0} out of range on '{1}' (0-{2})".format(
                    chain_index, device.name, len(chains) - 1))
            # Return the first device in the chain (or the chain's device list)
            # For now, return the chain's first device. If a nested device_index
            # is needed, callers can extend this.
            chain = chains[chain_index]
            if not chain.devices:
                raise ValueError("Chain '{0}' has no devices".format(chain.name))
            # Use device_index 0 within the chain for now (callers pass separate index)
            return track, device

        return track, device
    def _find_parameter(self, device, name=None, index=None):
        """Find a parameter on a device by name or index.

        Lookup order:
        1. Exact name match (case-sensitive)
        2. Case-insensitive exact match
        3. Case-insensitive partial match
        4. By 0-based index

        Returns (parameter, match_type) tuple where match_type is
        'exact', 'case_insensitive', 'partial', or 'index'.
        Raises ValueError if not found.
        """
        params = device.parameters

        if name is not None:
            # Step 1: exact match
            for p in params:
                if p.name == name:
                    return p, "exact"

            # Step 2: case-insensitive exact match
            name_lower = name.lower()
            for p in params:
                if p.name.lower() == name_lower:
                    return p, "case_insensitive"

            # Step 3: case-insensitive partial match
            for p in params:
                if name_lower in p.name.lower():
                    return p, "partial"

            raise ValueError("Parameter '{0}' not found on device '{1}'".format(
                name, device.name))

        if index is not None:
            if index < 0 or index >= len(params):
                raise IndexError("Parameter index {0} out of range on '{1}' (0-{2})".format(
                    index, device.name, len(params) - 1))
            return params[index], "index"

        raise ValueError("Either name or index must be provided")
    def _get_device_info(self, device):
        """Build a device info dict."""
        info = {
            "name": device.name,
            "class_name": device.class_name,
            "type": self._get_device_type(device),
            "is_active": device.is_active,
            "can_have_chains": device.can_have_chains,
            "can_have_drum_pads": device.can_have_drum_pads,
            "parameter_count": len(device.parameters),
        }
        try:
            info["class_display_name"] = device.class_display_name
        except Exception:
            info["class_display_name"] = device.class_name
        return info
    def _get_device_type(self, device):
        """Get the type of a device"""
        try:
            # Simple heuristic - in a real implementation you'd look at the device class
            if device.can_have_drum_pads:
                return "drum_machine"
            elif device.can_have_chains:
                return "rack"
            elif "instrument" in device.class_display_name.lower():
                return "instrument"
            elif "audio_effect" in device.class_name.lower():
                return "audio_effect"
            elif "midi_effect" in device.class_name.lower():
                return "midi_effect"
            else:
                return "unknown"
        except:
            return "unknown"
    # ---- unified additions ----

    def _resolve_target_device(self, track_index, device_index, chain_index=None):
        """Resolve (track, device) and descend into a rack chain's first device when chain_index is given."""
        track, device = self._resolve_device(track_index, device_index)
        if chain_index is None:
            return track, device
        if not device.can_have_chains:
            raise ValueError("Device '{0}' is not a rack".format(device.name))
        chains = device.chains
        if chain_index < 0 or chain_index >= len(chains):
            raise IndexError("Chain index {0} out of range on '{1}' (0-{2})".format(
                chain_index, device.name, len(chains) - 1))
        chain = chains[chain_index]
        if not chain.devices:
            raise ValueError("Chain '{0}' has no devices".format(chain.name))
        return track, chain.devices[0]

    def _describe_parameter(self, param, index=None):
        pmin, pmax = param.min, param.max
        raw = param.value
        norm = (raw - pmin) / (pmax - pmin) if pmax != pmin else 0.0
        info = {
            "parameter_name": param.name,
            "value": round(norm, 4),
            "raw_value": raw,
            "display_value": str(param),
            "min": pmin,
            "max": pmax,
            "is_enabled": param.is_enabled,
        }
        if index is not None:
            info["parameter_index"] = index
        return info

    def _apply_normalized(self, param, value):
        """Set ``param`` from a normalized 0-1 value; returns (old_norm, clamped_norm, was_clamped)."""
        pmin, pmax = param.min, param.max
        old_norm = (param.value - pmin) / (pmax - pmin) if pmax != pmin else 0.0
        clamped = max(0.0, min(1.0, float(value)))
        param.value = pmin + clamped * (pmax - pmin)
        return round(old_norm, 4), round(clamped, 4), clamped != value

    def _set_device_parameter(self, track_index, device_index, chain_index=None,
                              parameter_name=None, parameter_index=None, value=0.0):
        """Set a device parameter by name or index. Value is normalized 0.0-1.0."""
        try:
            track, target_device = self._resolve_target_device(track_index, device_index, chain_index)
            param, match_type = self._find_parameter(target_device, name=parameter_name, index=parameter_index)
            if not param.is_enabled:
                raise ValueError("Parameter '{0}' is currently disabled".format(param.name))
            old_norm, new_norm, was_clamped = self._apply_normalized(param, value)
            result = self._describe_parameter(param, list(target_device.parameters).index(param))
            result.update({
                "device_name": target_device.name,
                "track_name": track.name,
                "old_value": old_norm,
                "new_value": new_norm,
                "match_type": match_type,
                "clamped": was_clamped,
            })
            return result
        except Exception as e:
            self.log_message("Error setting device parameter: " + str(e))
            raise

    def _batch_set_device_parameters(self, track_index, device_index, parameters, chain_index=None):
        """Set several parameters of one device at once. ``parameters`` is a list of
        {parameter_index | parameter_name, value} dicts (normalized 0-1 values)."""
        track, target_device = self._resolve_target_device(track_index, device_index, chain_index)
        results = []
        for entry in parameters or []:
            try:
                param, match_type = self._find_parameter(
                    target_device, name=entry.get("parameter_name"), index=entry.get("parameter_index"))
                if not param.is_enabled:
                    raise ValueError("Parameter '{0}' is currently disabled".format(param.name))
                old_norm, new_norm, was_clamped = self._apply_normalized(param, entry.get("value", 0.0))
                info = self._describe_parameter(param, list(target_device.parameters).index(param))
                info.update({"old_value": old_norm, "new_value": new_norm, "clamped": was_clamped, "ok": True})
                results.append(info)
            except Exception as e:
                results.append({"ok": False, "error": str(e), "request": entry})
        return {
            "device_name": target_device.name,
            "track_name": track.name,
            "updated": len([r for r in results if r.get("ok")]),
            "failed": len([r for r in results if not r.get("ok")]),
            "results": results,
        }

    def _toggle_device(self, track_index, device_index, chain_index=None):
        """Flip a device's 'Device On' state."""
        track, target_device = self._resolve_target_device(track_index, device_index, chain_index)
        params = target_device.parameters
        if not params:
            raise ValueError("Device '{0}' has no parameters".format(target_device.name))
        on_param = params[0]
        currently_on = on_param.value > (on_param.min + on_param.max) / 2.0
        result = self._set_device_enabled(track_index, device_index, chain_index, not currently_on)
        result["was_active"] = currently_on
        return result

    def _get_drum_pad_info(self, track_index, device_index, pad_index=None):
        """List filled drum pads of a Drum Rack, or detail one pad when ``pad_index`` is given."""
        try:
            track, device = self._resolve_device(track_index, device_index)
            if not getattr(device, "can_have_drum_pads", False):
                raise ValueError("Device '{0}' is not a Drum Rack".format(device.name))
            pads = list(device.drum_pads)
            if pad_index is not None:
                if pad_index < 0 or pad_index >= len(pads):
                    raise IndexError("Pad index {0} out of range (0-{1})".format(pad_index, len(pads) - 1))
                pad = pads[pad_index]
                chains = list(pad.chains) if hasattr(pad, "chains") else []
                return {
                    "device_name": device.name,
                    "pad_index": pad_index,
                    "note": pad.note,
                    "name": pad.name,
                    "mute": pad.mute,
                    "solo": pad.solo,
                    "chain_count": len(chains),
                    "chains": [{
                        "name": c.name,
                        "devices": [{"index": di, "name": d.name, "type": self._get_device_type(d)}
                                    for di, d in enumerate(c.devices)]
                    } for c in chains],
                }
            filled_pads = []
            for pi, pad in enumerate(pads):
                if pad.chains:
                    filled_pads.append({
                        "pad_index": pi,
                        "note": pad.note,
                        "name": pad.name,
                        "mute": pad.mute,
                        "solo": pad.solo,
                        "chains": [{
                            "name": c.name,
                            "devices": [{"index": di, "name": d.name, "type": self._get_device_type(d)}
                                        for di, d in enumerate(c.devices)]
                        } for c in pad.chains],
                    })
            return {"device_name": device.name, "pad_count": len(pads), "filled_pads": filled_pads}
        except Exception as e:
            self.log_message("Error getting drum pad info: " + str(e))
            raise

    @command("get_device_parameters")
    def cmd_get_device_parameters(self, params):
        ti = params.get("track_index", 0)
        di = params.get("device_index", 0)
        ci = params.get("chain_index", None)
        show_all = params.get("show_all", False)
        return self._get_device_parameters(ti, di, ci, show_all)

    @command("set_device_parameter", modifying=True)
    def cmd_set_device_parameter(self, params):
        ti = params.get("track_index", 0)
        di = params.get("device_index", 0)
        ci = params.get("chain_index", None)
        pn = params.get("parameter_name", None)
        pi = params.get("parameter_index", None)
        val = params.get("value", 0.0)
        if pn is None and pi is None:
            pi = 0
        return self._set_device_parameter(ti, di, ci, pn, pi, val)

    @command("batch_set_device_parameters", modifying=True)
    def cmd_batch_set_device_parameters(self, params):
        ti = params.get("track_index", 0)
        di = params.get("device_index", 0)
        ci = params.get("chain_index", None)
        parameters = params.get("parameters", [])
        return self._batch_set_device_parameters(ti, di, parameters, ci)

    @command("set_device_enabled", modifying=True)
    def cmd_set_device_enabled(self, params):
        ti = params.get("track_index", 0)
        di = params.get("device_index", 0)
        ci = params.get("chain_index", None)
        enabled = params.get("enabled", True)
        return self._set_device_enabled(ti, di, ci, enabled)

    @command("toggle_device", modifying=True)
    def cmd_toggle_device(self, params):
        ti = params.get("track_index", 0)
        di = params.get("device_index", 0)
        ci = params.get("chain_index", None)
        return self._toggle_device(ti, di, ci)

    @command("delete_device", modifying=True)
    def cmd_delete_device(self, params):
        ti = params.get("track_index", 0)
        di = params.get("device_index", 0)
        return self._delete_device(ti, di)

    @command("navigate_preset", modifying=True)
    def cmd_navigate_preset(self, params):
        ti = params.get("track_index", 0)
        di = params.get("device_index", 0)
        ci = params.get("chain_index", None)
        direction = params.get("direction", "current")
        return self._navigate_preset(ti, di, ci, direction)

    @command("get_drum_pad_info")
    def cmd_get_drum_pad_info(self, params):
        ti = params.get("track_index", 0)
        di = params.get("device_index", 0)
        pad_index = params.get("pad_index", None)
        return self._get_drum_pad_info(ti, di, pad_index)
    # ---- command adapters (generated from the original dispatch chain) ----

    @command("get_drum_rack_pads")
    def cmd_get_drum_rack_pads(self, params):
        track_index = params.get("track_index", 0)
        device_index = params.get("device_index", 0)
        return self._get_drum_rack_pads(track_index, device_index)

    @command("get_rack_macros")
    def cmd_get_rack_macros(self, params):
        track_index = params.get("track_index", 0)
        device_index = params.get("device_index", 0)
        return self._get_rack_macros(track_index, device_index)

    @command("get_device_view_state")
    def cmd_get_device_view_state(self, params):
        track_index = params.get("track_index", 0)
        device_index = params.get("device_index", 0)
        return self._get_device_view_state(track_index, device_index)

    @command("get_selected_device")
    def cmd_get_selected_device(self, params):
        return self._get_selected_device()

    @command("get_simpler_sample_info")
    def cmd_get_simpler_sample_info(self, params):
        track_index = params.get("track_index", 0)
        device_index = params.get("device_index", 0)
        return self._get_simpler_sample_info(track_index, device_index)

    @command("get_simpler_parameters")
    def cmd_get_simpler_parameters(self, params):
        track_index = params.get("track_index", 0)
        device_index = params.get("device_index", 0)
        return self._get_simpler_parameters(track_index, device_index)

    @command("generate_drum_pattern", modifying=True)
    def cmd_generate_drum_pattern(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        style = params.get("style", "basic")
        length = params.get("length", 4.0)
        return self._generate_drum_pattern(track_index, clip_index, style, length)

    @command("get_device_by_name", modifying=True)
    def cmd_get_device_by_name(self, params):
        track_index = params.get("track_index", 0)
        device_name = params.get("device_name", "")
        return self._get_device_by_name(track_index, device_name)

    @command("load_device_preset", modifying=True)
    def cmd_load_device_preset(self, params):
        track_index = params.get("track_index", 0)
        device_index = params.get("device_index", 0)
        preset_uri = params.get("preset_uri", "")
        return self._load_device_preset(track_index, device_index, preset_uri)

    @command("set_drum_rack_pad_mute", modifying=True)
    def cmd_set_drum_rack_pad_mute(self, params):
        track_index = params.get("track_index", 0)
        device_index = params.get("device_index", 0)
        note = params.get("note", 36)
        mute = params.get("mute", False)
        return self._set_drum_rack_pad_mute(track_index, device_index, note, mute)

    @command("set_drum_rack_pad_solo", modifying=True)
    def cmd_set_drum_rack_pad_solo(self, params):
        track_index = params.get("track_index", 0)
        device_index = params.get("device_index", 0)
        note = params.get("note", 36)
        solo = params.get("solo", False)
        return self._set_drum_rack_pad_solo(track_index, device_index, note, solo)

    @command("set_rack_macro", modifying=True)
    def cmd_set_rack_macro(self, params):
        track_index = params.get("track_index", 0)
        device_index = params.get("device_index", 0)
        macro_index = params.get("macro_index", 0)
        value = params.get("value", 0.0)
        return self._set_rack_macro(track_index, device_index, macro_index, value)

    @command("move_device", modifying=True)
    def cmd_move_device(self, params):
        track_index = params.get("track_index", 0)
        device_index = params.get("device_index", 0)
        new_index = params.get("new_index", 0)
        return self._move_device(track_index, device_index, new_index)

    @command("move_device_left", modifying=True)
    def cmd_move_device_left(self, params):
        track_index = params.get("track_index", 0)
        device_index = params.get("device_index", 0)
        return self._move_device_left(track_index, device_index)

    @command("move_device_right", modifying=True)
    def cmd_move_device_right(self, params):
        track_index = params.get("track_index", 0)
        device_index = params.get("device_index", 0)
        return self._move_device_right(track_index, device_index)

    @command("set_device_collapsed", modifying=True)
    def cmd_set_device_collapsed(self, params):
        track_index = params.get("track_index", 0)
        device_index = params.get("device_index", 0)
        collapsed = params.get("collapsed", False)
        return self._set_device_collapsed(track_index, device_index, collapsed)

    @command("select_device", modifying=True)
    def cmd_select_device(self, params):
        track_index = params.get("track_index", 0)
        device_index = params.get("device_index", 0)
        return self._select_device(track_index, device_index)

    @command("set_drum_pad_name", modifying=True)
    def cmd_set_drum_pad_name(self, params):
        track_index = params.get("track_index", 0)
        device_index = params.get("device_index", 0)
        pad_index = params.get("pad_index", 0)
        name = params.get("name", "")
        return self._set_drum_pad_name(track_index, device_index, pad_index, name)


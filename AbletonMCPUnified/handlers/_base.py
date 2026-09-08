"""Shared validators and response enrichment used by every handler mixin."""


class BaseHandlers(object):

    # ---- validation helpers ----

    def _validate_track_index(self, track_index):
        """Validate track index and raise clear error if out of range"""
        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index {0} out of range (0-{1})".format(track_index, len(self._song.tracks) - 1))
        return self._song.tracks[track_index]

    def _validate_clip_slot(self, track_index, clip_index):
        """Validate track and clip indices, return clip slot"""
        track = self._validate_track_index(track_index)
        if clip_index < 0 or clip_index >= len(track.clip_slots):
            raise IndexError("Clip index {0} out of range (0-{1})".format(clip_index, len(track.clip_slots) - 1))
        return track.clip_slots[clip_index]

    def _validate_scene_index(self, scene_index):
        """Validate scene index and raise clear error if out of range"""
        if scene_index < 0 or scene_index >= len(self._song.scenes):
            raise IndexError("Scene index {0} out of range (0-{1})".format(scene_index, len(self._song.scenes) - 1))
        return self._song.scenes[scene_index]

    def _validate_device_index(self, track, device_index):
        """Validate device index on a track"""
        if device_index < 0 or device_index >= len(track.devices):
            raise IndexError("Device index {0} out of range (0-{1})".format(device_index, len(track.devices) - 1))
        return track.devices[device_index]

    def _validate_return_track_index(self, return_index):
        """Validate return track index"""
        if return_index < 0 or return_index >= len(self._song.return_tracks):
            raise IndexError("Return track index {0} out of range (0-{1})".format(return_index, len(self._song.return_tracks) - 1))
        return self._song.return_tracks[return_index]

    def _validate_send_index(self, track, send_index):
        """Validate send index on a track"""
        sends = track.mixer_device.sends
        if send_index < 0 or send_index >= len(sends):
            raise IndexError("Send index {0} out of range (0-{1})".format(send_index, len(sends) - 1))
        return sends[send_index]

    def _clamp_volume(self, value):
        """Clamp volume to valid range 0.0-1.0"""
        return max(0.0, min(1.0, float(value)))

    def _clamp_pan(self, value):
        """Clamp pan to valid range -1.0 to 1.0"""
        return max(-1.0, min(1.0, float(value)))

    # ---- response enrichment (unified convention: echo index + name) ----

    ECHO_INDEX_KEYS = ("track_index", "device_index", "clip_index", "scene_index", "return_index",
                       "send_index", "chain_index", "parameter_index", "pad_index")

    @staticmethod
    def _is_index(value):
        return type(value) is int and value >= 0

    def _capture_names(self, params, command_name=""):
        """Look up the names of objects referenced by index params (before the handler runs).

        clip_index means a Session slot for most commands, but an arrangement clip for
        the *arrangement* commands; echo the matching name.
        """
        names = {}
        arrangement = "arrangement" in (command_name or "")
        try:
            song = self._song
            ti = params.get("track_index")
            track = None
            if self._is_index(ti) and ti < len(song.tracks):
                track = song.tracks[ti]
                names["track_name"] = track.name
            ri = params.get("return_index")
            if self._is_index(ri) and ri < len(song.return_tracks):
                names["return_name"] = song.return_tracks[ri].name
            si = params.get("scene_index")
            if self._is_index(si) and si < len(song.scenes):
                names["scene_name"] = song.scenes[si].name
            if track is not None:
                di = params.get("device_index")
                if self._is_index(di) and di < len(track.devices):
                    names["device_name"] = track.devices[di].name
                ci = params.get("clip_index")
                if arrangement:
                    clips = list(track.arrangement_clips)
                    if self._is_index(ci) and ci < len(clips):
                        names["clip_name"] = clips[ci].name
                elif self._is_index(ci) and ci < len(track.clip_slots):
                    slot = track.clip_slots[ci]
                    if slot.has_clip:
                        names["clip_name"] = slot.clip.name
        except Exception:
            pass
        return names

    def _finalize_result(self, params, result, names):
        """Echo the index params and captured names into a dict result (never overriding handler keys)."""
        if not isinstance(result, dict):
            return result
        for key in self.ECHO_INDEX_KEYS:
            if key in params and key not in result and self._is_index(params[key]):
                result[key] = params[key]
        for key, value in names.items():
            if key not in result:
                result[key] = value
        return result

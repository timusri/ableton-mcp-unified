"""Mock Ableton Live objects with group tracks,
rack chains, drum pads, arrangement clips, cue points and view objects."""


class MockDeviceParameter:
    def __init__(self, name, value, min_val, max_val, is_quantized=False, value_items=()):
        self.name = name
        self._value = value
        self.min = min_val
        self.max = max_val
        self.is_enabled = True
        self.is_quantized = is_quantized
        self.value_items = list(value_items)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self._value = max(self.min, min(self.max, v))

    def __str__(self):
        return "%.2f" % self._value


class MockMixerDevice:
    def __init__(self):
        self._volume = MockDeviceParameter("Volume", 0.85, 0.0, 1.0)
        self._panning = MockDeviceParameter("Pan", 0.0, -1.0, 1.0)
        self._sends = [MockDeviceParameter("Send A", 0.0, 0.0, 1.0), MockDeviceParameter("Send B", 0.0, 0.0, 1.0)]

    @property
    def volume(self):
        return self._volume

    @property
    def panning(self):
        return self._panning

    @property
    def sends(self):
        return self._sends


class MockChain:
    def __init__(self, name="Chain", devices=None):
        self.name = name
        self.devices = devices or []
        self.mute = False
        self.solo = False


class MockDrumPad:
    def __init__(self, note, name="", chains=None):
        self.note = note
        self.name = name
        self.chains = chains or []
        self.mute = False
        self.solo = False


class MockDevice:
    def __init__(self, name="Test Device", class_name="PluginDevice", params=None, chains=None, drum_pads=None):
        self.name = name
        self.class_name = class_name
        self.class_display_name = class_name
        self.parameters = params or [
            MockDeviceParameter("Device On", 1.0, 0.0, 1.0),
            MockDeviceParameter("Dry/Wet", 1.0, 0.0, 1.0),
            MockDeviceParameter("Filter Cutoff", 500.0, 20.0, 20000.0),
        ]
        self.chains = chains or []
        self.can_have_chains = bool(chains)
        self.drum_pads = drum_pads or []
        self.can_have_drum_pads = bool(drum_pads)
        self.presets = []
        self.selected_preset_index = 0

    @property
    def is_active(self):
        return self.parameters[0].value > 0.5


class MockClip:
    def __init__(self, name="Test Clip", length=4.0, is_midi=True, start_time=0.0):
        self.name = name
        self.length = length
        self._is_playing = False
        self._is_recording = False
        self.looping = True
        self.loop_start = 0.0
        self.loop_end = length
        self.start_time = start_time
        self.end_time = start_time + length
        self.color_index = 0
        self.color = 0
        self.muted = False
        self.is_midi_clip = is_midi
        self.is_audio_clip = not is_midi
        self._notes = []
        if not is_midi:
            self.gain = 1.0
            self.pitch_coarse = 0
            self.pitch_fine = 0
            self.warping = True
            self.warp_mode = 0
            self.warp_markers = []

    @property
    def is_playing(self):
        return self._is_playing

    @property
    def is_recording(self):
        return self._is_recording

    def fire(self):
        self._is_playing = True

    def stop(self):
        self._is_playing = False

    def get_notes(self, start_time, start_pitch, time_span, pitch_span):
        return self._notes

    def get_notes_extended(self, from_pitch, pitch_span, from_time, time_span):
        return self._notes

    def set_notes(self, notes):
        self._notes = list(notes)

    def add_new_notes(self, notes):
        self._notes.extend(notes)

    def remove_notes(self, start_time, start_pitch, time_span, pitch_span):
        self._notes = []

    def remove_notes_extended(self, from_pitch, pitch_span, from_time, time_span):
        self._notes = []


class MockClipSlot:
    def __init__(self, has_clip=False):
        self._has_clip = has_clip
        self._clip = MockClip() if has_clip else None

    @property
    def has_clip(self):
        return self._has_clip

    @property
    def clip(self):
        return self._clip

    def create_clip(self, length):
        self._clip = MockClip(length=length)
        self._has_clip = True
        return self._clip

    def delete_clip(self):
        self._clip = None
        self._has_clip = False

    def fire(self):
        if self._clip:
            self._clip.fire()

    def stop(self):
        if self._clip:
            self._clip.stop()


class MockTrack:
    def __init__(self, name="Test Track", is_midi=True, is_group=False):
        self.name = name
        self.has_midi_input = is_midi and not is_group
        self.has_audio_input = (not is_midi) and not is_group
        self.is_foldable = is_group
        self.is_grouped = False
        self._mute = False
        self._solo = False
        self._arm = False
        self.color_index = 0
        self.color = 0
        self.mixer_device = MockMixerDevice()
        self.devices = []
        self.clip_slots = [MockClipSlot() for _ in range(8)]
        self.arrangement_clips = []
        self.is_frozen = False
        self.can_be_armed = not is_group

    @property
    def mute(self):
        return self._mute

    @mute.setter
    def mute(self, v):
        self._mute = v

    @property
    def solo(self):
        return self._solo

    @solo.setter
    def solo(self, v):
        self._solo = v

    @property
    def arm(self):
        if self.is_foldable:
            raise RuntimeError("Master and Return Tracks have no 'Arm' state!")
        return self._arm

    @arm.setter
    def arm(self, v):
        self._arm = v

    def create_midi_clip(self, position, length):
        clip = MockClip(name="", length=length, start_time=position)
        self.arrangement_clips.append(clip)
        return clip

    def delete_clip(self, clip):
        self.arrangement_clips.remove(clip)

    def delete_device(self, index):
        del self.devices[index]

    def duplicate_clip_to_arrangement(self, clip, destination_time):
        new = MockClip(name=clip.name, length=clip.length, start_time=destination_time)
        self.arrangement_clips.append(new)
        return new

    def freeze(self):
        self.is_frozen = True

    def flatten(self):
        self.is_frozen = False


class MockScene:
    def __init__(self, name="Scene 1"):
        self.name = name
        self.color_index = 0
        self.color = 0
        self.is_triggered = False

    def fire(self):
        pass


class MockCuePoint:
    def __init__(self, name, time):
        self.name = name
        self.time = time
        self.jumped = False

    def jump(self):
        self.jumped = True


class MockView:
    def __init__(self):
        self.selected_track = None
        self.selected_scene = None
        self.follow_song = False


class MockSong:
    def __init__(self, n_tracks=8, n_scenes=8):
        self._tempo = 120.0
        self._is_playing = False
        self.signature_numerator = 4
        self.signature_denominator = 4
        self.tracks = [MockTrack("Track %d" % (i + 1)) for i in range(n_tracks)]
        self.scenes = [MockScene("Scene %d" % (i + 1)) for i in range(n_scenes)]
        self.return_tracks = [MockTrack("A-Reverb", is_midi=False), MockTrack("B-Delay", is_midi=False)]
        self.master_track = MockTrack("Master", is_midi=False)
        self.cue_points = []
        self.current_song_time = 0.0
        self.song_length = 64.0
        self.loop = False
        self.loop_start = 0.0
        self.loop_length = 16.0
        self.arrangement_overdub = False
        self.back_to_arranger = False
        self.view = MockView()
        self.view.selected_track = self.tracks[0]

    @property
    def tempo(self):
        return self._tempo

    @tempo.setter
    def tempo(self, v):
        self._tempo = max(20.0, min(999.0, v))

    @property
    def is_playing(self):
        return self._is_playing

    def start_playing(self):
        self._is_playing = True

    def stop_playing(self):
        self._is_playing = False

    def create_midi_track(self, index=-1):
        track = MockTrack("MIDI Track %d" % (len(self.tracks) + 1))
        if index == -1:
            self.tracks.append(track)
        else:
            self.tracks.insert(index, track)
        return track

    def create_audio_track(self, index=-1):
        track = MockTrack("Audio Track %d" % (len(self.tracks) + 1), is_midi=False)
        if index == -1:
            self.tracks.append(track)
        else:
            self.tracks.insert(index, track)
        return track

    def delete_track(self, index):
        del self.tracks[index]

    def duplicate_track(self, index):
        original = self.tracks[index]
        new_track = MockTrack(original.name + " Copy")
        self.tracks.insert(index + 1, new_track)
        return new_track

    def create_scene(self, index=-1):
        scene = MockScene("Scene %d" % (len(self.scenes) + 1))
        if index == -1:
            self.scenes.append(scene)
        else:
            self.scenes.insert(index, scene)
        return scene

    def delete_scene(self, index):
        del self.scenes[index]

    def undo(self):
        pass

    def redo(self):
        pass

    # cue points: Live toggles a cue at the current song time
    def set_or_delete_cue(self):
        for cp in list(self.cue_points):
            if abs(cp.time - self.current_song_time) < 0.01:
                self.cue_points.remove(cp)
                return
        self.cue_points.append(MockCuePoint("%d.1.1" % (int(self.current_song_time // 4) + 1), self.current_song_time))
        self.cue_points.sort(key=lambda c: c.time)

    def jump_to_next_cue(self):
        for cp in sorted(self.cue_points, key=lambda c: c.time):
            if cp.time > self.current_song_time:
                self.current_song_time = cp.time
                return True
        return False

    def jump_to_prev_cue(self):
        for cp in sorted(self.cue_points, key=lambda c: -c.time):
            if cp.time < self.current_song_time:
                self.current_song_time = cp.time
                return True
        return False

# Tools

Generated from `ableton_mcp/spec.py` by `scripts/gen_tools_md.py`. Do not edit by hand.

Conventions: all indices are 1-based (as shown in Live); device parameter values are normalized 0.0–1.0; responses echo the indices and names of the objects touched. Commands marked *modifying* run on Live's main thread.

Tools: 154 (+7 deprecated aliases). Remote Script commands without a dedicated tool: 127 (use `send_command`).

## Session & transport

### `get_cpu_load`

Get the current CPU load of Ableton.

### `get_metronome_state`

Get the current metronome state.

### `get_playback_position`

Get the current playback position and transport state.

### `get_session_info`

Get detailed information about the current Ableton session

### `get_session_path`

Get the file path of the current session.

### `health_check` *(manual)*

Check that Ableton Live is connected and responsive. Returns rs_version and command_count of the Remote Script.

### `is_session_modified`

Check if the session has unsaved changes.

### `redo` *(modifying)*

Redo the last undone operation in Ableton.

### `send_command` *(manual)*

Escape hatch: send any registered Remote Script command by name (see list_commands / docs/tools.md). Params ending in `_index` are 1-based and converted automatically; `index` keeps -1 = append.

Parameters:
  - `command` (str, required) — Remote Script command name.
  - `params` (dict, default `{}`) — Command parameters (1-based indices).

### `set_metronome` *(modifying)*

Turn the metronome on or off.

Parameters:
  - `enabled` (bool, required)

### `set_tempo` *(modifying)*

Set the tempo of the Ableton session.

Parameters:
  - `tempo` (float, required)

### `start_playback` *(modifying)*

Start playing the Ableton session.

### `stop_playback` *(modifying)*

Stop playing the Ableton session.

### `undo` *(modifying)*

Undo the last operation in Ableton.

## Tracks, returns & master

### `create_audio_track` *(modifying)*

Create a new audio track in the Ableton session.

Parameters:
  - `index` (int, default `-1`)

### `create_group_track` *(modifying)*

Create a group track containing the specified tracks.

Parameters:
  - `track_indices` (any, required; list of 1-based)
  - `name` (str, default `'Group'`)

### `create_midi_track` *(modifying)*

Create a new MIDI track in the Ableton session.

Parameters:
  - `index` (int, default `-1`)

### `delete_track` *(modifying)* *(manual)*

Delete a track by 1-based index or by name. Refuses to delete the last remaining session track.

Parameters:
  - `track_index` (int, default `0`; 1-based, 0 = unset) — 1-based; 0 = resolve by track_name.
  - `track_name` (str, default `''`)

### `duplicate_track` *(modifying)*

Duplicate a track with all its clips and devices.

Parameters:
  - `track_index` (int, required; 1-based)

### `flatten_track` *(modifying)*

Flatten a frozen track (convert freeze to permanent audio).

Parameters:
  - `track_index` (int, required; 1-based)

### `fold_track` *(modifying)*

Fold (collapse) a group track.

Parameters:
  - `track_index` (int, required; 1-based)

### `freeze_track` *(modifying)*

Freeze a track (render all devices to audio for CPU optimization).

Parameters:
  - `track_index` (int, required; 1-based)

### `get_master_info`

Get information about the master track including volume, pan, and devices.

### `get_return_track_info`

Get detailed information about a return track.

Parameters:
  - `return_index` (int, required; 1-based)

### `get_return_tracks`

Get information about all return (aux) tracks.

### `get_send_level`

Get the send level from a track to a return track.

Parameters:
  - `track_index` (int, required; 1-based)
  - `send_index` (int, required; 1-based)

### `get_track_color`

Get the color of a track.

Parameters:
  - `track_index` (int, required; 1-based)

### `get_track_deletion_status` *(manual)*

Report whether session tracks can currently be deleted (Live requires at least one track).

Remote Script command: `get_session_info`

### `get_track_info` *(manual)*

Get detailed information about a track: clip slots, devices, mute/solo/arm, volume, panning, is_group_track.

Parameters:
  - `track_index` (int, required; 1-based)

### `get_track_monitoring` *(modifying)*

Get the monitoring mode of a track.

Parameters:
  - `track_index` (int, required; 1-based)

### `get_track_volume` *(manual)*

Get the current fader volume (0.85 = 0 dB unity) and panning of a track. Return tracks come after session tracks.

Parameters:
  - `track_index` (int, required; 1-based)

### `set_master_pan` *(modifying)*

Set the master track panning.

Parameters:
  - `pan` (float, required)

### `set_master_volume` *(modifying)*

Set the master track volume.

Parameters:
  - `volume` (float, required)

### `set_return_pan` *(modifying)*

Set the panning of a return track.

Parameters:
  - `return_index` (int, required; 1-based)
  - `pan` (float, required)

### `set_return_volume` *(modifying)*

Set the volume of a return track.

Parameters:
  - `return_index` (int, required; 1-based)
  - `volume` (float, required)

### `set_send_level` *(modifying)*

Set the send level from a track to a return track.

Parameters:
  - `track_index` (int, required; 1-based)
  - `send_index` (int, required; 1-based)
  - `level` (float, required)

### `set_track_arm` *(modifying)*

Set the arm (record enable) state of a track.

Parameters:
  - `track_index` (int, required; 1-based)
  - `arm` (bool, required)

### `set_track_color` *(modifying)*

Set the color of a track.

Parameters:
  - `track_index` (int, required; 1-based)
  - `color` (int, required)

### `set_track_monitoring` *(modifying)*

Set the monitoring mode of a track.

Parameters:
  - `track_index` (int, required; 1-based)
  - `monitoring` (str, required)

### `set_track_mute` *(modifying)*

Set the mute state of a track.

Parameters:
  - `track_index` (int, required; 1-based)
  - `mute` (bool, required)

### `set_track_name` *(modifying)*

Set the name of a track.

Parameters:
  - `track_index` (int, required; 1-based)
  - `name` (str, required)

### `set_track_panning` *(modifying)* *(manual)*

Set the mixer panning of a track: -1.0 = full left, 0.0 = center, +1.0 = full right.

Deprecated aliases: `set_track_pan`

Parameters:
  - `track_index` (int, required; 1-based)
  - `panning` (float, required)

### `set_track_solo` *(modifying)*

Set the solo state of a track.

Parameters:
  - `track_index` (int, required; 1-based)
  - `solo` (bool, required)

### `set_track_volume` *(modifying)* *(manual)*

Set the mixer fader volume of a track. Normalized: 0.0 = silence, 0.85 = 0 dB unity, 1.0 = max (~+6 dB).

Parameters:
  - `track_index` (int, required; 1-based)
  - `volume` (float, required) — 0.0-1.0; 0.85 = unity.

### `unarm_all` *(modifying)*

Unarm all tracks in the session.

### `unfold_track` *(modifying)*

Unfold (expand) a group track.

Parameters:
  - `track_index` (int, required; 1-based)

## Session clips

### `add_warp_marker` *(modifying)*

Add a warp marker to an audio clip.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)
  - `beat_time` (float, required)
  - `sample_time` (float, default `None`)

### `apply_groove` *(modifying)*

Apply a groove to a clip.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)
  - `groove_index` (int, required; 1-based)

### `clear_clip_automation` *(modifying)*

Clear automation for a clip parameter.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)
  - `parameter_name` (str, required)

### `commit_groove` *(modifying)*

Commit groove quantization to clip notes (make it permanent).

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)

### `create_clip` *(modifying)*

Create a new MIDI clip in the specified track and clip slot.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)
  - `length` (float, default `4.0`)

### `delete_clip` *(modifying)*

Delete a clip from a clip slot.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)

### `delete_warp_marker` *(modifying)*

Delete a warp marker from an audio clip.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)
  - `beat_time` (float, required)

### `duplicate_clip` *(modifying)*

Duplicate a clip to the next empty slot.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)

### `fire_clip` *(modifying)*

Start playing a clip.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)

### `get_clip_automation` *(modifying)*

Get automation data for a clip parameter.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)
  - `parameter_name` (str, required)

### `get_clip_color`

Get the color of a clip.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)

### `get_clip_gain`

Get the gain of an audio clip.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)

### `get_clip_loop`

Get the loop settings of a clip.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)

### `get_clip_pitch`

Get the pitch shift of an audio clip.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)

### `get_clip_warp_info` *(modifying)*

Get warp information for an audio clip.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)

### `get_groove_pool` *(modifying)*

Get available grooves from the groove pool.

### `get_warp_markers`

Get all warp markers from an audio clip.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)

### `set_clip_automation` *(modifying)*

Set automation for a clip parameter.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)
  - `parameter_name` (str, required)
  - `envelope_data` (any, required)

### `set_clip_color` *(modifying)*

Set the color of a clip.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)
  - `color` (int, required)

### `set_clip_gain` *(modifying)*

Set the gain of an audio clip.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)
  - `gain` (float, required)

### `set_clip_loop` *(modifying)*

Set the loop settings of a clip.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)
  - `loop_start` (float, default `0.0`)
  - `loop_end` (float, default `4.0`)
  - `looping` (bool, default `True`)

### `set_clip_name` *(modifying)*

Set the name of a clip.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)
  - `name` (str, required)

### `set_clip_pitch` *(modifying)*

Set the pitch shift of an audio clip.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)
  - `pitch` (int, required)

### `set_clip_warp_mode` *(modifying)*

Set the warp mode of an audio clip.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)
  - `warp_mode` (str, required)

### `stop_clip` *(modifying)*

Stop playing a clip.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)

## MIDI notes & generators

### `add_notes_to_clip` *(modifying)*

Add MIDI notes to a clip.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)
  - `notes` (list[dict], required)

### `generate_bassline` *(modifying)*

Generate a bassline pattern and add it to a clip.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)
  - `root` (int, default `36`)
  - `scale_type` (str, default `'minor'`)
  - `length` (float, default `4.0`)

### `get_clip_notes`

Get all MIDI notes from a clip.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)

### `get_scale_notes`

Get the notes in a musical scale.

Parameters:
  - `root` (int, required)
  - `scale_type` (str, default `'major'`)

### `humanize_clip_timing` *(modifying)*

Add random timing variation to notes in a clip for a more human feel.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)
  - `amount` (float, default `0.05`)

### `humanize_clip_velocity` *(modifying)*

Add random velocity variation to notes in a clip for a more human feel.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)
  - `amount` (float, default `0.1`)

### `quantize_clip_notes` *(modifying)*

Quantize notes in a clip to a grid.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)
  - `grid` (float, default `0.25`)

### `remove_all_notes` *(modifying)*

Remove all notes from a clip.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)

### `remove_notes` *(modifying)*

Remove notes from a clip within a specified range.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)
  - `from_time` (float, default `0.0`)
  - `time_span` (float, default `4.0`)
  - `from_pitch` (int, default `0`)
  - `pitch_span` (int, default `128`)

### `transpose_notes` *(modifying)*

Transpose all notes in a clip.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)
  - `semitones` (int, required)

## Scenes

### `create_scene` *(modifying)*

Create a new scene.

Parameters:
  - `index` (int, default `-1`)

### `delete_scene` *(modifying)*

Delete a scene.

Parameters:
  - `scene_index` (int, required; 1-based)

### `duplicate_scene` *(modifying)*

Duplicate a scene.

Parameters:
  - `scene_index` (int, required; 1-based)

### `fire_scene` *(modifying)*

Fire (trigger) a scene to play all clips in that row.

Parameters:
  - `scene_index` (int, required; 1-based)

### `get_all_scenes`

Get information about all scenes in the session.

### `get_scene_color`

Get the color of a scene.

Parameters:
  - `scene_index` (int, required; 1-based)

### `set_scene_color` *(modifying)*

Set the color of a scene.

Parameters:
  - `scene_index` (int, required; 1-based)
  - `color` (int, required)

### `set_scene_name` *(modifying)*

Set the name of a scene.

Parameters:
  - `scene_index` (int, required; 1-based)
  - `name` (str, required)

### `stop_scene` *(modifying)*

Stop all clips in a scene.

Parameters:
  - `scene_index` (int, required; 1-based)

## Devices & parameters

### `batch_set_device_parameters` *(modifying)* *(manual)*

Set several parameters of one device at once (normalized 0.0-1.0). Default path is fire-and-forget UDP (lowest latency, no response); reliable=True uses TCP and returns per-parameter results.

Parameters:
  - `track_index` (int, required; 1-based)
  - `device_index` (int, default `1`; 1-based)
  - `parameters` (list[dict], required) — [{parameter_index (1-based) | parameter_name, value}]
  - `chain_index` (int, default `0`; 1-based, 0 = unset)
  - `reliable` (bool, default `False`)

### `delete_device` *(modifying)* *(manual)*

Delete a device from a track by 1-based index or by name.

Parameters:
  - `track_index` (int, required; 1-based)
  - `device_index` (int, default `0`; 1-based, 0 = unset)
  - `device_name` (str, default `''`)

### `disable_device` *(modifying)* *(manual)*

Disable (bypass) a device on a track.

Remote Script command: `set_device_enabled`

Parameters:
  - `track_index` (int, required; 1-based)
  - `device_index` (int, default `0`; 1-based, 0 = unset)
  - `device_name` (str, default `''`)
  - `chain_index` (int, default `0`; 1-based, 0 = unset)

### `enable_device` *(modifying)* *(manual)*

Enable (activate) a device on a track.

Remote Script command: `set_device_enabled`

Parameters:
  - `track_index` (int, required; 1-based)
  - `device_index` (int, default `0`; 1-based, 0 = unset)
  - `device_name` (str, default `''`)
  - `chain_index` (int, default `0`; 1-based, 0 = unset)

### `generate_drum_pattern` *(modifying)*

Generate a drum pattern and add it to a clip.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)
  - `style` (str, default `'basic'`)
  - `length` (float, default `4.0`)

### `get_device_by_name` *(modifying)*

Find a device by name and get its parameters.

Parameters:
  - `track_index` (int, required; 1-based)
  - `device_name` (str, required)

### `get_device_parameters` *(manual)*

List parameters of a device (summary grouped by category; pass category or show_all=True for details). Values are normalized 0.0-1.0 with display strings; known plugins get friendly aliases.

Parameters:
  - `track_index` (int, required; 1-based)
  - `device_index` (int, default `1`; 1-based)
  - `chain_index` (int, default `0`; 1-based, 0 = unset) — Chain inside a rack (1-based, 0 = none).
  - `category` (str, default `''`)
  - `show_all` (bool, default `False`)

### `get_drum_pad_info` *(manual)*

List filled pads of a Drum Rack, or detail one pad when pad_index (1-based) is given.

Parameters:
  - `track_index` (int, required; 1-based)
  - `device_index` (int, default `1`; 1-based)
  - `pad_index` (int, default `0`; 1-based, 0 = unset)

### `move_device_left` *(modifying)*

Move a device one position to the left in the device chain.

Parameters:
  - `track_index` (int, required; 1-based)
  - `device_index` (int, required; 1-based)

### `move_device_right` *(modifying)*

Move a device one position to the right in the device chain.

Parameters:
  - `track_index` (int, required; 1-based)
  - `device_index` (int, required; 1-based)

### `navigate_device_preset` *(modifying)* *(manual)*

Navigate device presets: direction = next, previous or current.

Remote Script command: `navigate_preset`

Parameters:
  - `track_index` (int, required; 1-based)
  - `device_index` (int, default `1`; 1-based)
  - `chain_index` (int, default `0`; 1-based, 0 = unset)
  - `direction` (str, default `'next'`)

### `set_device_enabled` *(modifying)* *(manual)*

Enable or bypass a device (by 1-based index or name, optionally inside a rack chain).

Parameters:
  - `track_index` (int, required; 1-based)
  - `device_index` (int, default `0`; 1-based, 0 = unset)
  - `device_name` (str, default `''`)
  - `chain_index` (int, default `0`; 1-based, 0 = unset)
  - `enabled` (bool, default `True`)

### `set_device_parameter` *(modifying)* *(manual)*

Set a device parameter by name (exact, partial or plugin alias) or 1-based index. Value is normalized 0.0-1.0. Response includes value, raw_value, display_value, min, max, old_value.

Parameters:
  - `track_index` (int, required; 1-based)
  - `device_index` (int, default `1`; 1-based)
  - `chain_index` (int, default `0`; 1-based, 0 = unset)
  - `parameter_name` (str, default `''`)
  - `parameter_index` (int, default `0`; 1-based, 0 = unset)
  - `value` (float, default `0.0`)

### `toggle_device` *(modifying)*

Toggle a device on or off.

Parameters:
  - `track_index` (int, required; 1-based)
  - `device_index` (int, required; 1-based)
  - `chain_index` (int, default `0`; 1-based, 0 = unset) — Chain inside a rack (1-based, 0 = none).

## Rack chains

### `get_chain_info` *(manual)*

List chains in a rack device, or the devices inside one chain when chain_index is given.

Parameters:
  - `track_index` (int, required; 1-based)
  - `device_index` (int, default `1`; 1-based)
  - `chain_index` (int, default `0`; 1-based, 0 = unset)

### `get_rack_chains` *(modifying)*

Get chains from an instrument or effect rack.

Parameters:
  - `track_index` (int, required; 1-based)
  - `device_index` (int, required; 1-based)

### `select_rack_chain` *(modifying)*

Select a chain in a rack device.

Parameters:
  - `track_index` (int, required; 1-based)
  - `device_index` (int, required; 1-based)
  - `chain_index` (int, required; 1-based)

## Browser & loading

### `browse_path`

Navigate browser by path list to get items at that location.

Parameters:
  - `path` (any, required)

### `get_browser_items_at_path` *(manual)*

List browser items at 'category/folder/subfolder'. Category aliases like 'audio-effects', 'vst3' are normalized.

Parameters:
  - `path` (str, required)

### `get_browser_tree` *(manual)*

Get a hierarchical tree of browser categories ('all', 'instruments', 'sounds', 'drums', 'audio_effects', 'midi_effects', 'plugins').

Parameters:
  - `category_type` (str, default `'all'`)

### `list_external_plugins` *(manual)*

List discovered external plugins (VST/AU), optionally filtered by name query. Results are cached for 2 minutes.

Remote Script command: `get_browser_items_at_path`

Parameters:
  - `query` (str, default `''`)
  - `max_results` (int, default `50`)
  - `refresh_cache` (bool, default `False`)

### `load_drum_kit` *(modifying)* *(manual)*

Load a Drum Rack by URI and then the first loadable kit found at kit_path.

Remote Script command: `load_browser_item`

Parameters:
  - `track_index` (int, required; 1-based)
  - `rack_uri` (str, required)
  - `kit_path` (str, required)

### `load_external_plugin` *(modifying)* *(manual)*

Load an external plugin onto a track by name (fuzzy match; exact_match=True for strict).

Remote Script command: `load_browser_item`

Parameters:
  - `track_index` (int, required; 1-based)
  - `plugin_name` (str, required)
  - `exact_match` (bool, default `False`)
  - `refresh_cache` (bool, default `False`)

### `load_instrument_or_effect` *(modifying)* *(manual)*

Load an instrument or effect onto a track by browser URI (see get_browser_items_at_path).

Remote Script command: `load_browser_item`

Parameters:
  - `track_index` (int, required; 1-based)
  - `uri` (str, required)

### `load_item_to_return` *(modifying)*

Load a browser item (effect) onto a return track by URI.

Remote Script command: `load_browser_item_to_return`

Parameters:
  - `return_index` (int, required; 1-based)
  - `uri` (str, required)

### `load_item_to_track` *(modifying)*

Load a browser item (instrument or effect) onto a track by URI.

Remote Script command: `load_instrument_or_effect`

Parameters:
  - `track_index` (int, required; 1-based)
  - `uri` (str, required)

### `search_browser`

Search the browser for items matching a query.

Parameters:
  - `query` (str, required)
  - `category` (str, default `'all'`)

## Input/output routing

### `get_available_inputs`

Get available input routing options for a track.

Parameters:
  - `track_index` (int, required; 1-based)

### `get_available_outputs`

Get available output routing options for a track.

Parameters:
  - `track_index` (int, required; 1-based)

### `get_track_input_routing`

Get the input routing of a track.

Parameters:
  - `track_index` (int, required; 1-based)

### `get_track_output_routing`

Get the output routing of a track.

Parameters:
  - `track_index` (int, required; 1-based)

### `set_track_input_routing` *(modifying)*

Set the input routing of a track.

Parameters:
  - `track_index` (int, required; 1-based)
  - `routing_type` (str, required)
  - `routing_channel` (str, default `''`)

### `set_track_output_routing` *(modifying)*

Set the output routing of a track.

Parameters:
  - `track_index` (int, required; 1-based)
  - `routing_type` (str, required)
  - `routing_channel` (str, default `''`)

## Views & selection

### `control_arrangement_view` *(modifying)*

Control the arrangement view: zoom_in, zoom_out, scroll_left, scroll_right, follow_on, follow_off, collapse_track, expand_track.

Parameters:
  - `action` (str, required)
  - `track_index` (int, default `0`; 1-based, 0 = unset)

### `get_current_view`

Get information about the current view state (selected track, scene, etc.).

### `select_clip` *(modifying)*

Select a clip slot.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)

### `select_scene` *(modifying)*

Select a scene.

Parameters:
  - `scene_index` (int, required; 1-based)

### `select_track` *(modifying)*

Select a track.

Parameters:
  - `track_index` (int, required; 1-based)

### `set_view` *(modifying)*

Switch Live's main view: Arranger, Session, Detail, Detail/Clip, Detail/DeviceChain, Browser.

Deprecated aliases: `focus_view`, `set_ableton_view`

Parameters:
  - `view` (str, default `'Arranger'`; wire name `view_name`)

## Recording & automation modes

### `capture_midi` *(modifying)*

Capture MIDI that was played recently (like Ableton's Capture feature).

### `set_overdub` *(modifying)*

Set overdub mode.

Parameters:
  - `enabled` (bool, required)

### `start_recording` *(modifying)*

Start recording in Ableton.

### `stop_recording` *(modifying)*

Stop recording in Ableton.

### `toggle_arrangement_record` *(modifying)*

Toggle arrangement record mode.

### `toggle_session_record` *(modifying)*

Toggle session record mode.

## Arrangement

### `add_notes_to_arrangement_clip` *(modifying)*

Add MIDI notes to an arrangement clip (pitch, start_time, duration, velocity, mute).

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)
  - `notes` (list[dict], required)

### `create_arrangement_audio_clip` *(modifying)* *(manual)*

Place an audio file as a clip in the arrangement.

Parameters:
  - `track_index` (int, required; 1-based)
  - `file_path` (str, required)
  - `start_bar` (int, default `0`)
  - `start_beat` (float, default `0.0`)

### `create_arrangement_midi_clip` *(modifying)* *(manual)*

Create an empty MIDI clip in the arrangement at a bar (1-based) or beat position.

Remote Script command: `create_arrangement_clip`

Parameters:
  - `track_index` (int, required; 1-based)
  - `start_bar` (int, default `0`)
  - `end_bar` (int, default `0`)
  - `start_beat` (float, default `0.0`)
  - `length_beats` (float, default `4.0`)
  - `name` (str, default `''`)

### `delete_arrangement_clip` *(modifying)* *(manual)*

Delete an arrangement clip by 1-based position or by name.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, default `0`; 1-based, 0 = unset)
  - `clip_name` (str, default `''`)

### `duplicate_clip_to_arrangement` *(modifying)* *(manual)*

Copy a session clip to the arrangement at a bar (1-based) or beat position.

Remote Script command: `duplicate_to_arrangement`

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, required; 1-based)
  - `destination_bar` (int, default `0`)
  - `destination_beat` (float, default `0.0`)

### `get_arrangement_info` *(manual)*

Get arrangement clips (with bar positions) and transport state for one track or all tracks.

Parameters:
  - `track_index` (int, default `0`; 1-based, 0 = unset) — 1-based; 0 = all tracks.

### `get_arrangement_length`

Get the length and loop settings of the arrangement.

### `manage_clip_automation` *(modifying)* *(manual)*

Create or clear automation envelopes on an arrangement clip (action: create, clear, clear_all).

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, default `1`; 1-based)
  - `clip_name` (str, default `''`)
  - `action` (str, default `'create'`)
  - `parameter_name` (str, default `'volume'`)

### `set_arrangement_clip_property` *(modifying)* *(manual)*

Set properties (name, muted, color, looping, loop_start/end, gain, pitch, warping, warp_mode) on an arrangement clip.

Parameters:
  - `track_index` (int, required; 1-based)
  - `clip_index` (int, default `1`; 1-based)
  - `clip_name` (str, default `''`)
  - `name` (str, default `''`)
  - `muted` (bool, default `None`)
  - `color` (int, default `None`)
  - `looping` (bool, default `None`)
  - `loop_start` (float, default `None`)
  - `loop_end` (float, default `None`)
  - `gain` (float, default `None`)
  - `pitch_coarse` (int, default `None`)
  - `pitch_fine` (float, default `None`)
  - `warping` (bool, default `None`)
  - `warp_mode` (int, default `None`)

### `set_arrangement_loop` *(modifying)* *(manual)*

Enable/disable the arrangement loop and set its region by bars (1-based) or beats.

Parameters:
  - `enabled` (bool, default `True`)
  - `start_bar` (int, default `0`)
  - `end_bar` (int, default `0`)
  - `start_beat` (float, default `0.0`)
  - `length_beats` (float, default `0.0`)

### `set_song_time` *(modifying)* *(manual)*

Jump the playback position to a bar (1-based) or a raw beat position.

Deprecated aliases: `jump_to_time`

Parameters:
  - `bar` (int, default `0`) — 1-based bar; takes precedence over beat.
  - `beat` (float, default `0.0`)

## Cue points (locators)

### `create_cue_point` *(modifying)* *(manual)*

Create a cue point at a bar (1-based) or beat position.

Deprecated aliases: `create_locator`

Parameters:
  - `bar` (int, default `0`)
  - `beat` (float, default `0.0`)
  - `name` (str, default `''`)

### `delete_cue_point` *(modifying)* *(manual)*

Delete a cue point at a bar (1-based) / beat position, or by 1-based cue_index.

Deprecated aliases: `delete_locator`

Parameters:
  - `bar` (int, default `0`)
  - `beat` (float, default `0.0`)
  - `cue_index` (int, default `0`; 1-based, 0 = unset)

### `get_cue_points` *(manual)*

List all cue points (locators) with bar positions.

Deprecated aliases: `get_locators`

### `jump_to_cue_point` *(modifying)* *(manual)*

Jump to a cue point by direction ('next'/'prev'), by name, or by 1-based cue_index.

Remote Script command: `jump_to_cue`

Parameters:
  - `direction` (str, default `''`)
  - `name` (str, default `''`)
  - `cue_index` (int, default `0`; 1-based, 0 = unset)

## Generic Live Object Model

### `live_call` *(modifying)* *(manual)*

Call a method on a Live object with JSON-primitive args, e.g. path='live_set', method='create_midi_track', args=[-1]. An arg of {'$path': 'live_set tracks 1 devices 2'} is resolved to that Live object (e.g. view.select_device). timeout (seconds, max 60) bounds long operations.

Parameters:
  - `path` (str, required)
  - `method` (str, required)
  - `args` (list, default `None`)
  - `timeout` (float, default `10.0`)

### `live_children` *(manual)*

Enumerate the properties, lists, child objects and methods of a Live object at a path.

Parameters:
  - `path` (str, default `'live_set'`)

### `live_get` *(manual)*

Read properties of any Live object by path, e.g. 'live_set tracks 1 devices 2' (1-based indices). Without props returns a summary; with props returns those attribute values.

Parameters:
  - `path` (str, default `'live_set'`)
  - `props` (list[str], default `None`)

### `live_set` *(modifying)* *(manual)*

Set a property on a Live object, e.g. path='live_set', prop='tempo', value=128. Object-valued properties take a reference: value={'$path': 'live_set tracks 1 devices 1 drum_pads 47'}.

Parameters:
  - `path` (str, required)
  - `prop` (str, required)
  - `value` (any, required)

## Remote Script commands without a dedicated tool

Call these with `send_command(command, params)`; `*_index` params are 1-based and converted automatically.

### Session & transport

- `continue_playing()` *(modifying)* — Continue playing from current position
- `get_back_to_arrangement()` — Get whether back to arrangement is needed
- `get_crossfader()` — Get the master crossfader value
- `get_cue_volume()` — Get cue/preview volume
- `get_current_song_time()` — Get current playback position
- `get_exclusive_arm()` — Get exclusive arm setting
- `get_exclusive_solo()` — Get exclusive solo setting
- `get_signature()` — Get time signature
- `get_song_length()` — Get song length in beats
- `get_song_root_note()` — Get the song's root note (key signature)
- `get_song_scale()` — Get the song's scale mode
- `get_swing_amount()` — Get the global swing amount
- `list_commands()` — List commands
- `scrub_by(delta=0)` *(modifying)* — Scrub playback position by delta beats
- `set_crossfader(value=0.5)` *(modifying)* — Set the master crossfader value (0.0 to 1.0)
- `set_cue_volume(volume=0.85)` *(modifying)* — Set cue/preview volume (0.0-1.0)
- `set_current_song_time(time=0)` *(modifying)* — Set playback position (scrub)
- `set_exclusive_arm(enabled=True)` *(modifying)* — Set exclusive arm
- `set_exclusive_solo(enabled=False)` *(modifying)* — Set exclusive solo
- `set_signature(numerator=4, denominator=4)` *(modifying)* — Set time signature
- `set_song_root_note(root_note=0)` *(modifying)* — Set the song's root note (0-11, C=0)
- `set_swing_amount(amount=0.0)` *(modifying)* — Set the global swing amount (0.0 to 1.0)
- `tap_tempo()` *(modifying)* — Tap tempo
- `trigger_back_to_arrangement()` *(modifying)* — Trigger back to arrangement

### Tracks, returns & master

- `create_return_track()` *(modifying)* — Create return track
- `delete_return_track(index=0)` *(modifying)* — Delete return track
- `get_all_track_names()` — Get all track names quickly
- `get_master_output_meter()` — Get master output meter levels
- `get_send_pre_post(track_index, send_index)` — Get send pre/post fader state
- `get_track_capabilities(track_index)` — Get track capabilities
- `get_track_crossfade_assign(track_index)` — Get the crossfade assignment of a track (A, B, or None)
- `get_track_delay(track_index)` — Get track delay in ms
- `get_track_fired_slot_index(track_index)` — Get the index of the most recently fired clip slot on a track
- `get_track_implicit_arm(track_index)` — Get track implicit arm state
- `get_track_is_foldable(track_index)` — Check if track can be folded (is group track)
- `get_track_is_grouped(track_index)` — Check if track is in a group
- `get_track_output_meter(track_index)` — Get the output meter level of a track (for metering)
- `get_track_playing_slot_index(track_index)` — Get the index of the currently playing clip slot on a track
- `set_track_crossfade_assign(track_index, assign=1)` *(modifying)* — Set the crossfade assignment of a track (0=A, 1=None, 2=B)
- `set_track_delay(track_index, delay_ms=0)` *(modifying)* — Set track delay in ms
- `set_track_implicit_arm(track_index, enabled=False)` *(modifying)* — Set track implicit arm state
- `solo_exclusive(track_index)` *(modifying)* — Solo track exclusively
- `ungroup_tracks(group_track_index=0)` *(modifying)* — Ungroup a group track
- `unmute_all()` *(modifying)* — Unmute all tracks
- `unsolo_all()` *(modifying)* — Unsolo all tracks

### Session clips

- `duplicate_clip_loop(track_index, clip_index)` *(modifying)* — Duplicate clip loop (double length)
- `get_audio_clip_file_path(track_index, clip_index)` — Get the file path of an audio clip's sample
- `get_clip_end_time(track_index, clip_index)` — Get clip end time
- `get_clip_fades(track_index, clip_index)` — Get audio clip fade settings
- `get_clip_follow_action(track_index, clip_index)` — Get the follow action settings of a clip
- `get_clip_has_envelopes(track_index, clip_index)` — Check if clip has automation envelopes
- `get_clip_info(track_index, clip_index)` — Get clip metadata without notes
- `get_clip_is_playing(track_index, clip_index)` — Check if clip is playing
- `get_clip_launch_mode(track_index, clip_index)` — Get the launch mode of a clip (retrigger, gate, toggle, repeat)
- `get_clip_launch_quantization(track_index, clip_index)` — Get the launch quantization of a clip
- `get_clip_playing_position(track_index, clip_index)` — Get clip's current playing position
- `get_clip_ram_mode(track_index, clip_index)` — Get whether an audio clip is loaded into RAM
- `get_clip_start_end_markers(track_index, clip_index)` — Get clip start/end markers
- `get_clip_start_time(track_index, clip_index)` — Get clip start time
- `get_clip_trigger_quantization()` — Get global clip trigger quantization
- `get_clip_velocity_amount(track_index, clip_index)` — Get MIDI clip velocity amount
- `get_groove_amount()` — Get global groove amount
- `set_clip_end_marker(track_index, clip_index, position=0)` *(modifying)* — Set clip end marker
- `set_clip_end_time(track_index, clip_index, time=0)` *(modifying)* — Set clip end time
- `set_clip_fade_in(track_index, clip_index, start=0, end=0)` *(modifying)* — Set audio clip fade in
- `set_clip_fade_out(track_index, clip_index, start=0, end=0)` *(modifying)* — Set audio clip fade out
- `set_clip_follow_action(track_index, clip_index, action_a=None, action_b=None, chance=None, time=None)` *(modifying)* — Set the follow action settings of a clip
- `set_clip_launch_mode(track_index, clip_index, mode=0)` *(modifying)* — Set the launch mode of a clip
- `set_clip_launch_quantization(track_index, clip_index, quantization=0)` *(modifying)* — Set the launch quantization of a clip
- `set_clip_ram_mode(track_index, clip_index, enabled=False)` *(modifying)* — Set whether an audio clip is loaded into RAM
- `set_clip_start_marker(track_index, clip_index, position=0)` *(modifying)* — Set clip start marker
- `set_clip_start_time(track_index, clip_index, time=0)` *(modifying)* — Set clip start time
- `set_clip_trigger_quantization(quantization=4)` *(modifying)* — Set global clip trigger quantization
- `set_clip_velocity_amount(track_index, clip_index, amount=1.0)` *(modifying)* — Set MIDI clip velocity amount
- `set_groove_amount(amount=1.0)` *(modifying)* — Set global groove amount
- `stop_all_clips()` *(modifying)* — Stop all playing clips

### MIDI notes & generators

- `deselect_all_notes(track_index, clip_index)` *(modifying)* — Deselect all notes in clip
- `get_notes_in_range(track_index, clip_index, start_time=0, end_time=4, pitch_start=0, pitch_end=127)` — Get MIDI notes within time and pitch range
- `move_clip_notes(track_index, clip_index, time_delta=0, pitch_delta=0)` *(modifying)* — Move notes in clip by time and/or pitch delta
- `quantize_clip(track_index, clip_index, quantize_to=0.25, amount=1.0)` *(modifying)* — Quantize clip to grid
- `set_clip_notes(track_index, clip_index, notes=[])` *(modifying)* — Replace all notes in clip

### Devices & parameters

- `get_device_view_state(track_index, device_index)` — Get device view state
- `get_drum_rack_pads(track_index, device_index)` — Get info about all pads in a drum rack
- `get_rack_macros(track_index, device_index)` — Get all macro knob values from a rack device
- `get_selected_device()` — Get currently selected device
- `get_simpler_parameters(track_index, device_index)` — Get Simpler playback parameters
- `get_simpler_sample_info(track_index, device_index)` — Get Simpler/Sampler sample info
- `load_device_preset(track_index, device_index, preset_uri='')` *(modifying)* — Load a preset onto a device
- `move_device(track_index, device_index, new_index)` *(modifying)* — Move device to new position
- `select_device(track_index, device_index)` *(modifying)* — Select device for viewing
- `set_device_collapsed(track_index, device_index, collapsed=False)` *(modifying)* — Set device collapsed state
- `set_drum_pad_name(track_index, device_index, pad_index, name='')` *(modifying)* — Set drum pad name
- `set_drum_rack_pad_mute(track_index, device_index, note=36, mute=False)` *(modifying)* — Mute/unmute a drum rack pad by note number
- `set_drum_rack_pad_solo(track_index, device_index, note=36, solo=False)` *(modifying)* — Solo/unsolo a drum rack pad by note number
- `set_rack_macro(track_index, device_index, macro_index, value=0.0)` *(modifying)* — Set a macro knob value on a rack device

### Browser & loading

- `get_browser_children(uri='')` — Get children of browser item by URI
- `get_browser_item(uri=None, path=None)` — Get a browser item by URI or path

### Input/output routing

- `get_track_available_input_types(track_index)` — Get available input routing types for track
- `get_track_available_output_types(track_index)` — Get available output routing types for track

### Views & selection

- `get_detail_clip()` — Get currently selected clip in detail view
- `get_draw_mode()` — Get whether draw mode is enabled (for MIDI note entry)
- `get_follow_mode()` — Get whether follow mode (auto-scroll) is enabled
- `get_grid_quantization()` — Get the current grid quantization setting
- `get_highlighted_clip_slot()` — Get highlighted clip slot
- `get_selected_scene()` — Get selected scene index
- `get_selected_track()` — Get selected track index
- `get_view_zoom()` — Get the current zoom level
- `set_detail_clip(track_index, clip_index)` *(modifying)* — Set clip to show in detail view
- `set_draw_mode(enabled=True)` *(modifying)* — Set draw mode
- `set_follow_mode(enabled=True)` *(modifying)* — Set follow mode (auto-scroll)
- `set_grid_quantization(quantization=4, triplet=False)` *(modifying)* — Set the grid quantization

### Recording & automation modes

- `get_arrangement_overdub()` — Get arrangement overdub state
- `get_can_capture_midi()` — Check if MIDI can be captured
- `get_count_in_duration()` — Get count-in duration
- `get_midi_recording_quantization()` — Get MIDI recording quantization
- `get_punch_settings()` — Get punch in/out settings
- `get_record_mode()` — Get record mode states
- `get_session_automation_record()` — Get session automation record state
- `re_enable_automation()` *(modifying)* — Re-enable automation (un-override all)
- `set_arrangement_overdub(enabled=False)` *(modifying)* — Set arrangement overdub state
- `set_count_in_duration(duration=0)` *(modifying)* — Set count-in duration (0=None, 1=1bar, 2=2bars, 4=4bars)
- `set_midi_recording_quantization(quantization=0)` *(modifying)* — Set MIDI recording quantization
- `set_punch_in(enabled=False)` *(modifying)* — Enable/disable punch in
- `set_punch_out(enabled=False)` *(modifying)* — Enable/disable punch out
- `set_session_automation_record(enabled=False)` *(modifying)* — Set session automation record state

### Cue points (locators)

- `jump_to_next_cue()` *(modifying)* — Jump to cue point by direction or name.
- `jump_to_prev_cue()` *(modifying)* — Jump to cue point by direction or name.

"""Routing command handlers.

The ``cmd_*`` adapters are registered through registry.py.
"""
import random
import traceback

from ..registry import command


class RoutingHandlers(object):

    def _get_track_input_routing(self, track_index):
        """Get the input routing of a track"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]

            result = {
                "track_index": track_index,
                "input_routing_type": str(track.input_routing_type.display_name) if hasattr(track.input_routing_type, 'display_name') else str(track.input_routing_type),
                "input_routing_channel": str(track.input_routing_channel.display_name) if hasattr(track.input_routing_channel, 'display_name') else str(track.input_routing_channel)
            }
            return result
        except Exception as e:
            self.log_message("Error getting track input routing: " + str(e))
            raise
    def _get_track_output_routing(self, track_index):
        """Get the output routing of a track"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]

            result = {
                "track_index": track_index,
                "output_routing_type": str(track.output_routing_type.display_name) if hasattr(track.output_routing_type, 'display_name') else str(track.output_routing_type),
                "output_routing_channel": str(track.output_routing_channel.display_name) if hasattr(track.output_routing_channel, 'display_name') else str(track.output_routing_channel)
            }
            return result
        except Exception as e:
            self.log_message("Error getting track output routing: " + str(e))
            raise
    def _get_available_inputs(self, track_index):
        """Get available input routing options for a track"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]
            inputs = []

            if hasattr(track, 'available_input_routing_types'):
                for rt in track.available_input_routing_types:
                    inputs.append(str(rt.display_name) if hasattr(rt, 'display_name') else str(rt))

            result = {
                "track_index": track_index,
                "available_inputs": inputs
            }
            return result
        except Exception as e:
            self.log_message("Error getting available inputs: " + str(e))
            raise
    def _get_available_outputs(self, track_index):
        """Get available output routing options for a track"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]
            outputs = []

            if hasattr(track, 'available_output_routing_types'):
                for rt in track.available_output_routing_types:
                    outputs.append(str(rt.display_name) if hasattr(rt, 'display_name') else str(rt))

            result = {
                "track_index": track_index,
                "available_outputs": outputs
            }
            return result
        except Exception as e:
            self.log_message("Error getting available outputs: " + str(e))
            raise
    def _set_track_input_routing(self, track_index, routing_type, routing_channel):
        """Set the input routing of a track"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]

            # Find and set the routing type
            if hasattr(track, 'available_input_routing_types'):
                for rt in track.available_input_routing_types:
                    rt_name = str(rt.display_name) if hasattr(rt, 'display_name') else str(rt)
                    if rt_name.lower() == routing_type.lower():
                        track.input_routing_type = rt
                        break

            result = {
                "track_index": track_index,
                "input_routing_type": str(track.input_routing_type.display_name) if hasattr(track.input_routing_type, 'display_name') else str(track.input_routing_type)
            }
            return result
        except Exception as e:
            self.log_message("Error setting track input routing: " + str(e))
            raise
    def _set_track_output_routing(self, track_index, routing_type, routing_channel):
        """Set the output routing of a track"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]

            # Find and set the routing type
            if hasattr(track, 'available_output_routing_types'):
                for rt in track.available_output_routing_types:
                    rt_name = str(rt.display_name) if hasattr(rt, 'display_name') else str(rt)
                    if rt_name.lower() == routing_type.lower():
                        track.output_routing_type = rt
                        break

            result = {
                "track_index": track_index,
                "output_routing_type": str(track.output_routing_type.display_name) if hasattr(track.output_routing_type, 'display_name') else str(track.output_routing_type)
            }
            return result
        except Exception as e:
            self.log_message("Error setting track output routing: " + str(e))
            raise
    def _get_track_available_input_types(self, track_index):
        """Get available input routing types for track"""
        try:
            track = list(self._song.tracks)[track_index]
            types = list(track.available_input_routing_types)
            return {
                "types": [{"display_name": t.display_name} for t in types]
            }
        except Exception as e:
            return {"error": str(e)}
    def _get_track_available_output_types(self, track_index):
        """Get available output routing types for track"""
        try:
            track = list(self._song.tracks)[track_index]
            types = list(track.available_output_routing_types)
            return {
                "types": [{"display_name": t.display_name} for t in types]
            }
        except Exception as e:
            return {"error": str(e)}
    # ---- command adapters (generated from the original dispatch chain) ----

    @command("get_track_input_routing")
    def cmd_get_track_input_routing(self, params):
        track_index = params.get("track_index", 0)
        return self._get_track_input_routing(track_index)

    @command("get_track_output_routing")
    def cmd_get_track_output_routing(self, params):
        track_index = params.get("track_index", 0)
        return self._get_track_output_routing(track_index)

    @command("get_available_inputs")
    def cmd_get_available_inputs(self, params):
        track_index = params.get("track_index", 0)
        return self._get_available_inputs(track_index)

    @command("get_available_outputs")
    def cmd_get_available_outputs(self, params):
        track_index = params.get("track_index", 0)
        return self._get_available_outputs(track_index)

    @command("get_track_available_input_types")
    def cmd_get_track_available_input_types(self, params):
        track_index = params.get("track_index", 0)
        return self._get_track_available_input_types(track_index)

    @command("get_track_available_output_types")
    def cmd_get_track_available_output_types(self, params):
        track_index = params.get("track_index", 0)
        return self._get_track_available_output_types(track_index)

    @command("set_track_input_routing", modifying=True)
    def cmd_set_track_input_routing(self, params):
        track_index = params.get("track_index", 0)
        routing_type = params.get("routing_type", "")
        routing_channel = params.get("routing_channel", "")
        return self._set_track_input_routing(track_index, routing_type, routing_channel)

    @command("set_track_output_routing", modifying=True)
    def cmd_set_track_output_routing(self, params):
        track_index = params.get("track_index", 0)
        routing_type = params.get("routing_type", "")
        routing_channel = params.get("routing_channel", "")
        return self._set_track_output_routing(track_index, routing_type, routing_channel)


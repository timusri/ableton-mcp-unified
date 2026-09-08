"""View command handlers.

The ``cmd_*`` adapters are registered through registry.py.
"""
import random
import traceback

from ..registry import command


class ViewHandlers(object):

    def _get_current_view(self):
        """Get information about the current view state"""
        try:
            view = self._song.view
            app_view = self.application().view

            result = {
                "selected_track_index": list(self._song.tracks).index(view.selected_track) if view.selected_track in self._song.tracks else -1,
                "selected_track_name": view.selected_track.name if view.selected_track else None,
                "selected_scene_index": list(self._song.scenes).index(view.selected_scene) if view.selected_scene else -1,
                "selected_scene_name": view.selected_scene.name if view.selected_scene else None,
                "is_session_visible": app_view.is_view_visible("Session") if hasattr(app_view, 'is_view_visible') else None,
                "is_arranger_visible": app_view.is_view_visible("Arranger") if hasattr(app_view, 'is_view_visible') else None,
            }
            return result
        except Exception as e:
            self.log_message("Error getting current view: " + str(e))
            raise
    def _select_track(self, track_index):
        """Select a track"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]
            self._song.view.selected_track = track

            result = {
                "selected": True,
                "track_index": track_index,
                "track_name": track.name
            }
            return result
        except Exception as e:
            self.log_message("Error selecting track: " + str(e))
            raise
    def _select_scene(self, scene_index):
        """Select a scene"""
        try:
            if scene_index < 0 or scene_index >= len(self._song.scenes):
                raise IndexError("Scene index out of range")

            scene = self._song.scenes[scene_index]
            self._song.view.selected_scene = scene

            result = {
                "selected": True,
                "scene_index": scene_index,
                "scene_name": scene.name
            }
            return result
        except Exception as e:
            self.log_message("Error selecting scene: " + str(e))
            raise
    def _select_clip(self, track_index, clip_index):
        """Select a clip slot"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]

            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip index out of range")

            # Select the track and scene
            self._song.view.selected_track = track
            if clip_index < len(self._song.scenes):
                self._song.view.selected_scene = self._song.scenes[clip_index]

            # Try to highlight the clip slot
            clip_slot = track.clip_slots[clip_index]
            if hasattr(self._song.view, 'highlighted_clip_slot'):
                self._song.view.highlighted_clip_slot = clip_slot

            result = {
                "selected": True,
                "track_index": track_index,
                "clip_index": clip_index,
                "has_clip": clip_slot.has_clip
            }
            return result
        except Exception as e:
            self.log_message("Error selecting clip: " + str(e))
            raise
    def _get_view_zoom(self):
        """Get the current zoom level"""
        try:
            app = self.application()
            view = app.view

            result = {}
            if hasattr(view, 'zoom'):
                result["zoom"] = view.zoom
            if hasattr(self._song.view, 'track_width'):
                result["track_width"] = self._song.view.track_width
            if hasattr(self._song.view, 'track_height'):
                result["track_height"] = self._song.view.track_height

            return result if result else {"error": "Zoom not available"}
        except Exception as e:
            self.log_message("Error getting view zoom: " + str(e))
            return {"error": str(e)}
    def _get_follow_mode(self):
        """Get whether follow mode (auto-scroll) is enabled"""
        try:
            follow = self._song.view.follow_song if hasattr(self._song.view, 'follow_song') else False
            return {"follow_mode": follow}
        except Exception as e:
            self.log_message("Error getting follow mode: " + str(e))
            return {"error": str(e)}
    def _set_follow_mode(self, enabled):
        """Set follow mode (auto-scroll)"""
        try:
            self._song.view.follow_song = enabled
            return {"success": True, "follow_mode": enabled}
        except Exception as e:
            self.log_message("Error setting follow mode: " + str(e))
            return {"error": str(e)}
    def _get_draw_mode(self):
        """Get whether draw mode is enabled (for MIDI note entry)"""
        try:
            app = self.application()
            draw_mode = app.view.draw_mode if hasattr(app.view, 'draw_mode') else False
            return {"draw_mode": draw_mode}
        except Exception as e:
            self.log_message("Error getting draw mode: " + str(e))
            return {"error": str(e)}
    def _set_draw_mode(self, enabled):
        """Set draw mode"""
        try:
            app = self.application()
            app.view.draw_mode = enabled
            return {"success": True, "draw_mode": enabled}
        except Exception as e:
            self.log_message("Error setting draw mode: " + str(e))
            return {"error": str(e)}
    def _get_grid_quantization(self):
        """Get the current grid quantization setting"""
        try:
            grid = self._song.view.grid_quantization if hasattr(self._song.view, 'grid_quantization') else 0
            grid_triplet = self._song.view.grid_is_triplet if hasattr(self._song.view, 'grid_is_triplet') else False
            return {
                "grid_quantization": grid,
                "grid_is_triplet": grid_triplet
            }
        except Exception as e:
            self.log_message("Error getting grid quantization: " + str(e))
            return {"error": str(e)}
    def _set_grid_quantization(self, quantization, triplet=False):
        """Set the grid quantization"""
        try:
            self._song.view.grid_quantization = quantization
            self._song.view.grid_is_triplet = triplet
            return {"success": True, "grid_quantization": quantization, "grid_is_triplet": triplet}
        except Exception as e:
            self.log_message("Error setting grid quantization: " + str(e))
            return {"error": str(e)}
    def _get_selected_track(self):
        """Get selected track index"""
        try:
            selected = self._song.view.selected_track
            for i, t in enumerate(self._song.tracks):
                if t == selected:
                    return {"selected_track_index": i, "name": t.name}
            return {"selected_track_index": -1}
        except Exception as e:
            return {"error": str(e)}
    def _get_selected_scene(self):
        """Get selected scene index"""
        try:
            selected = self._song.view.selected_scene
            for i, s in enumerate(self._song.scenes):
                if s == selected:
                    return {"selected_scene_index": i}
            return {"selected_scene_index": -1}
        except Exception as e:
            return {"error": str(e)}
    def _get_detail_clip(self):
        """Get currently selected clip in detail view"""
        try:
            view = self._song.view
            clip = view.detail_clip
            if clip:
                # Find track and slot
                for ti, track in enumerate(self._song.tracks):
                    for ci, slot in enumerate(track.clip_slots):
                        if slot.clip == clip:
                            return {
                                "track_index": ti,
                                "clip_index": ci,
                                "name": clip.name,
                                "is_midi": clip.is_midi_clip,
                                "length": clip.length
                            }
                return {"clip": "found but location unknown"}
            return {"clip": None}
        except Exception as e:
            return {"error": str(e)}
    def _set_detail_clip(self, track_index, clip_index):
        """Set clip to show in detail view"""
        try:
            clip = list(self._song.tracks)[track_index].clip_slots[clip_index].clip
            if clip:
                self._song.view.detail_clip = clip
                return {"success": True}
            return {"error": "No clip in slot"}
        except Exception as e:
            return {"error": str(e)}
    def _get_highlighted_clip_slot(self):
        """Get highlighted clip slot"""
        try:
            view = self._song.view
            slot = view.highlighted_clip_slot
            if slot:
                for ti, track in enumerate(self._song.tracks):
                    for ci, s in enumerate(track.clip_slots):
                        if s == slot:
                            return {"track_index": ti, "clip_index": ci, "has_clip": slot.has_clip}
            return {"slot": None}
        except Exception as e:
            return {"error": str(e)}
    def _set_view(self, view_name):
        """Switch Ableton view."""
        try:
            app = self.application()
            app.view.show_view(view_name)
            return {"visible": app.view.is_view_visible(view_name)}
        except Exception as e:
            self.log_message("Error setting view: " + str(e))
            raise
    def _control_arrangement_view(self, action, track_index=0):
        """Dispatch arrangement view control actions."""
        try:
            app = self.application()
            if action == "zoom_in":
                app.view.zoom_view(1, "Arranger", False)
            elif action == "zoom_out":
                app.view.zoom_view(0, "Arranger", False)
            elif action == "scroll_right":
                app.view.scroll_view(1, "Arranger", False)
            elif action == "scroll_left":
                app.view.scroll_view(0, "Arranger", False)
            elif action == "follow_on":
                self._song.view.follow_song = True
            elif action == "follow_off":
                self._song.view.follow_song = False
            elif action == "collapse_track":
                if track_index < 0 or track_index >= len(self._song.tracks):
                    raise IndexError("Track index out of range")
                self._song.tracks[track_index].view.is_collapsed = True
            elif action == "expand_track":
                if track_index < 0 or track_index >= len(self._song.tracks):
                    raise IndexError("Track index out of range")
                self._song.tracks[track_index].view.is_collapsed = False
            else:
                raise ValueError("Unknown action: " + action)
            return {"action": action, "done": True}
        except Exception as e:
            self.log_message("Error controlling arrangement view: " + str(e))
            raise
    # ---- unified additions ----

    def _focus_view(self, view_name):
        """Backwards-compatible name for _set_view."""
        return self._set_view(view_name)

    @command("set_view", modifying=True, aliases=("focus_view",))
    def cmd_set_view(self, params):
        view_name = params.get("view_name", params.get("view", "Arranger"))
        result = self._set_view(view_name)
        result["view_name"] = view_name
        result["focused"] = True
        return result

    @command("control_arrangement_view", modifying=True)
    def cmd_control_arrangement_view(self, params):
        action = params.get("action", "")
        ti = params.get("track_index", 0)
        return self._control_arrangement_view(action, ti)
    # ---- command adapters (generated from the original dispatch chain) ----

    @command("get_current_view")
    def cmd_get_current_view(self, params):
        return self._get_current_view()

    @command("get_view_zoom")
    def cmd_get_view_zoom(self, params):
        return self._get_view_zoom()

    @command("get_follow_mode")
    def cmd_get_follow_mode(self, params):
        return self._get_follow_mode()

    @command("get_draw_mode")
    def cmd_get_draw_mode(self, params):
        return self._get_draw_mode()

    @command("get_grid_quantization")
    def cmd_get_grid_quantization(self, params):
        return self._get_grid_quantization()

    @command("get_selected_track")
    def cmd_get_selected_track(self, params):
        return self._get_selected_track()

    @command("get_selected_scene")
    def cmd_get_selected_scene(self, params):
        return self._get_selected_scene()

    @command("get_detail_clip")
    def cmd_get_detail_clip(self, params):
        return self._get_detail_clip()

    @command("get_highlighted_clip_slot")
    def cmd_get_highlighted_clip_slot(self, params):
        return self._get_highlighted_clip_slot()

    @command("select_track", modifying=True)
    def cmd_select_track(self, params):
        track_index = params.get("track_index", 0)
        return self._select_track(track_index)

    @command("select_scene", modifying=True)
    def cmd_select_scene(self, params):
        scene_index = params.get("scene_index", 0)
        return self._select_scene(scene_index)

    @command("select_clip", modifying=True)
    def cmd_select_clip(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._select_clip(track_index, clip_index)

    @command("set_follow_mode", modifying=True)
    def cmd_set_follow_mode(self, params):
        enabled = params.get("enabled", True)
        return self._set_follow_mode(enabled)

    @command("set_draw_mode", modifying=True)
    def cmd_set_draw_mode(self, params):
        enabled = params.get("enabled", True)
        return self._set_draw_mode(enabled)

    @command("set_grid_quantization", modifying=True)
    def cmd_set_grid_quantization(self, params):
        quantization = params.get("quantization", 4)
        triplet = params.get("triplet", False)
        return self._set_grid_quantization(quantization, triplet)

    @command("set_detail_clip", modifying=True)
    def cmd_set_detail_clip(self, params):
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        return self._set_detail_clip(track_index, clip_index)


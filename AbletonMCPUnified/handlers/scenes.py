"""Scene command handlers.

The ``cmd_*`` adapters are registered through registry.py.
"""
import random
import traceback

from ..registry import command


class SceneHandlers(object):

    def _get_all_scenes(self):
        """Get information about all scenes"""
        try:
            scenes = []
            for i, scene in enumerate(self._song.scenes):
                scene_info = {
                    "index": i,
                    "name": scene.name,
                    "color": scene.color if hasattr(scene, 'color') else None,
                    "color_index": scene.color_index if hasattr(scene, 'color_index') else None,
                    "is_triggered": scene.is_triggered if hasattr(scene, 'is_triggered') else False,
                    "tempo": scene.tempo if hasattr(scene, 'tempo') else None,
                }
                scenes.append(scene_info)

            result = {
                "scene_count": len(scenes),
                "scenes": scenes
            }
            return result
        except Exception as e:
            self.log_message("Error getting all scenes: " + str(e))
            raise
    def _create_scene(self, index):
        """Create a new scene at the specified index"""
        try:
            self._song.create_scene(index)
            new_index = len(self._song.scenes) - 1 if index == -1 else index
            new_scene = self._song.scenes[new_index]

            result = {
                "index": new_index,
                "name": new_scene.name
            }
            return result
        except Exception as e:
            self.log_message("Error creating scene: " + str(e))
            raise
    def _delete_scene(self, scene_index):
        """Delete a scene at the specified index"""
        try:
            if scene_index < 0 or scene_index >= len(self._song.scenes):
                raise IndexError("Scene index out of range")

            scene_name = self._song.scenes[scene_index].name
            self._song.delete_scene(scene_index)

            result = {
                "deleted": True,
                "scene_index": scene_index,
                "scene_name": scene_name
            }
            return result
        except Exception as e:
            self.log_message("Error deleting scene: " + str(e))
            raise
    def _fire_scene(self, scene_index):
        """Fire (trigger) a scene"""
        try:
            if scene_index < 0 or scene_index >= len(self._song.scenes):
                raise IndexError("Scene index out of range")

            scene = self._song.scenes[scene_index]
            scene.fire()

            result = {
                "fired": True,
                "scene_index": scene_index,
                "scene_name": scene.name
            }
            return result
        except Exception as e:
            self.log_message("Error firing scene: " + str(e))
            raise
    def _stop_scene(self, scene_index):
        """Stop all clips in a scene"""
        try:
            if scene_index < 0 or scene_index >= len(self._song.scenes):
                raise IndexError("Scene index out of range")

            # Stop all clip slots in this scene row
            for track in self._song.tracks:
                if scene_index < len(track.clip_slots):
                    track.clip_slots[scene_index].stop()

            result = {
                "stopped": True,
                "scene_index": scene_index
            }
            return result
        except Exception as e:
            self.log_message("Error stopping scene: " + str(e))
            raise
    def _set_scene_name(self, scene_index, name):
        """Set the name of a scene"""
        try:
            if scene_index < 0 or scene_index >= len(self._song.scenes):
                raise IndexError("Scene index out of range")

            scene = self._song.scenes[scene_index]
            scene.name = name

            result = {
                "scene_index": scene_index,
                "name": scene.name
            }
            return result
        except Exception as e:
            self.log_message("Error setting scene name: " + str(e))
            raise
    def _set_scene_color(self, scene_index, color):
        """Set the color of a scene"""
        try:
            if scene_index < 0 or scene_index >= len(self._song.scenes):
                raise IndexError("Scene index out of range")

            scene = self._song.scenes[scene_index]
            if hasattr(scene, 'color_index'):
                scene.color_index = color

            result = {
                "scene_index": scene_index,
                "color_index": scene.color_index if hasattr(scene, 'color_index') else None
            }
            return result
        except Exception as e:
            self.log_message("Error setting scene color: " + str(e))
            raise
    def _duplicate_scene(self, scene_index):
        """Duplicate a scene"""
        try:
            if scene_index < 0 or scene_index >= len(self._song.scenes):
                raise IndexError("Scene index out of range")

            self._song.duplicate_scene(scene_index)
            new_index = scene_index + 1

            result = {
                "duplicated": True,
                "original_index": scene_index,
                "new_index": new_index,
                "new_name": self._song.scenes[new_index].name
            }
            return result
        except Exception as e:
            self.log_message("Error duplicating scene: " + str(e))
            raise
    def _get_scene_color(self, scene_index):
        """Get the color index of a scene"""
        try:
            scenes = list(self._song.scenes)
            if scene_index >= len(scenes):
                return {"error": "Scene index out of range"}
            scene = scenes[scene_index]
            return {"color_index": scene.color_index}
        except Exception as e:
            self.log_message("Error getting scene color: " + str(e))
            return {"error": str(e)}
    # ---- command adapters (generated from the original dispatch chain) ----

    @command("get_all_scenes")
    def cmd_get_all_scenes(self, params):
        return self._get_all_scenes()

    @command("get_scene_color")
    def cmd_get_scene_color(self, params):
        scene_index = params.get("scene_index", 0)
        return self._get_scene_color(scene_index)

    @command("create_scene", modifying=True)
    def cmd_create_scene(self, params):
        index = params.get("index", -1)
        return self._create_scene(index)

    @command("delete_scene", modifying=True)
    def cmd_delete_scene(self, params):
        scene_index = params.get("scene_index", 0)
        return self._delete_scene(scene_index)

    @command("fire_scene", modifying=True)
    def cmd_fire_scene(self, params):
        scene_index = params.get("scene_index", 0)
        return self._fire_scene(scene_index)

    @command("stop_scene", modifying=True)
    def cmd_stop_scene(self, params):
        scene_index = params.get("scene_index", 0)
        return self._stop_scene(scene_index)

    @command("set_scene_name", modifying=True)
    def cmd_set_scene_name(self, params):
        scene_index = params.get("scene_index", 0)
        name = params.get("name", "")
        return self._set_scene_name(scene_index, name)

    @command("set_scene_color", modifying=True)
    def cmd_set_scene_color(self, params):
        scene_index = params.get("scene_index", 0)
        color = params.get("color", 0)
        return self._set_scene_color(scene_index, color)

    @command("duplicate_scene", modifying=True)
    def cmd_duplicate_scene(self, params):
        scene_index = params.get("scene_index", 0)
        return self._duplicate_scene(scene_index)


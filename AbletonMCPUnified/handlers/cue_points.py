"""CuePoint command handlers.

The ``cmd_*`` adapters are registered through registry.py.
"""
import random
import traceback

from ..registry import command


class CuePointHandlers(object):

    def _get_cue_points(self):
        """Get all cue points."""
        try:
            cue_points = []
            for cp in self._song.cue_points:
                cue_points.append({"name": cp.name, "time": cp.time})
            return {"cue_points": cue_points}
        except Exception as e:
            self.log_message("Error getting cue points: " + str(e))
            raise
    def _jump_to_cue(self, direction=None, name=None):
        """Jump to cue point by direction or name."""
        try:
            if direction == "next":
                self._song.jump_to_next_cue()
                return {"direction": "next", "time": self._song.current_song_time}
            elif direction == "prev":
                self._song.jump_to_prev_cue()
                return {"direction": "prev", "time": self._song.current_song_time}
            elif name:
                for cp in self._song.cue_points:
                    if cp.name == name:
                        cp.jump()
                        return {"name": cp.name, "time": cp.time}
                raise ValueError("Cue point '{0}' not found".format(name))
            else:
                raise ValueError("Provide direction ('next'/'prev') or name")
        except Exception as e:
            self.log_message("Error jumping to cue: " + str(e))
            raise
    def _create_cue_point(self, time, name=""):
        """Create a cue point at the given time."""
        try:
            for cp in tuple(self._song.cue_points):
                if abs(cp.time - time) < 0.01:
                    raise ValueError("Cue point already exists at this position: " + cp.name)
            self._song.current_song_time = time
            self._song.set_or_delete_cue()
            if name:
                for cp in tuple(self._song.cue_points):
                    if abs(cp.time - time) < 0.01:
                        cp.name = name
                        break
            return {"time": time, "name": name}
        except Exception as e:
            self.log_message("Error creating cue point: " + str(e))
            raise
    # ---- unified additions ----

    def _cue_point_list(self):
        return [{"index": i, "name": cp.name, "time": cp.time}
                for i, cp in enumerate(self._song.cue_points)]

    def _delete_cue_point(self, time=None, cue_index=None):
        """Delete a cue point by time (beats) or by index."""
        try:
            cues = list(self._song.cue_points)
            if cue_index is not None:
                if cue_index < 0 or cue_index >= len(cues):
                    raise IndexError("Cue index {0} out of range (0-{1})".format(cue_index, len(cues) - 1))
                time = cues[cue_index].time
            if time is None:
                raise ValueError("Provide time or cue_index")
            target = None
            for cp in cues:
                if abs(cp.time - time) < 0.01:
                    target = cp
                    break
            if target is None:
                raise ValueError("No cue point at this position")
            name = target.name
            self._song.current_song_time = time
            self._song.set_or_delete_cue()
            return {"deleted": True, "time": time, "name": name}
        except Exception as e:
            self.log_message("Error deleting cue point: " + str(e))
            raise

    @command("get_cue_points", aliases=("get_locators",))
    def cmd_get_cue_points(self, params):
        cues = self._cue_point_list()
        return {"cue_points": cues, "locators": cues, "locator_count": len(cues), "cue_point_count": len(cues)}

    @command("create_cue_point", modifying=True, aliases=("create_locator",))
    def cmd_create_cue_point(self, params):
        time_val = params.get("time", None)
        if time_val is None:
            time_val = self._song.current_song_time
        name = params.get("name", "") or ""
        return self._create_cue_point(time_val, name)

    @command("delete_cue_point", modifying=True, aliases=("delete_locator",))
    def cmd_delete_cue_point(self, params):
        cue_index = params.get("cue_index", params.get("locator_index", None))
        return self._delete_cue_point(params.get("time", None), cue_index)

    @command("jump_to_cue", modifying=True, aliases=("jump_to_cue_point",))
    def cmd_jump_to_cue(self, params):
        direction = params.get("direction", None)
        name = params.get("name", None)
        index = params.get("index", params.get("cue_index", None))
        if direction is None and not name and index is not None:
            cues = list(self._song.cue_points)
            if index < 0 or index >= len(cues):
                raise IndexError("Cue index {0} out of range (0-{1})".format(index, len(cues) - 1))
            cues[index].jump()
            return {"index": index, "name": cues[index].name, "time": cues[index].time}
        return self._jump_to_cue(direction, name)

    @command("jump_to_next_cue", modifying=True)
    def cmd_jump_to_next_cue(self, params):
        return self._jump_to_cue("next", None)

    @command("jump_to_prev_cue", modifying=True)
    def cmd_jump_to_prev_cue(self, params):
        return self._jump_to_cue("prev", None)
    # ---- command adapters (generated from the original dispatch chain) ----


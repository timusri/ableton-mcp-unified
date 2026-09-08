"""Generic Live Object Model commands: live_get / live_children / live_set / live_call."""
from ..registry import command
from .. import lom


class LomHandlers(object):

    def _lom_roots(self):
        return {"live_set": self._song, "live_app": self.application()}

    @command("live_get")
    def cmd_live_get(self, params):
        path = params.get("path", "live_set")
        props = params.get("props", None)
        obj = lom.resolve_path(self._lom_roots(), path)
        if props:
            if isinstance(props, str):
                props = [props]
            return {"path": path, "values": lom.get_props(obj, list(props), path)}
        return {"path": path, "value": lom.serialize(obj, path)}

    @command("live_children")
    def cmd_live_children(self, params):
        path = params.get("path", "live_set")
        obj = lom.resolve_path(self._lom_roots(), path)
        result = lom.children(obj, path)
        result["path"] = path
        result["type"] = type(obj).__name__
        return result

    @command("live_set", modifying=True)
    def cmd_live_set(self, params):
        path = params.get("path", "")
        prop = lom.check_attr_name(params.get("prop", ""))
        if "value" not in params:
            raise ValueError("value is required")
        obj = lom.resolve_path(self._lom_roots(), path)
        if not hasattr(obj, prop):
            raise AttributeError("%r has no property %r" % (type(obj).__name__, prop))
        current = getattr(obj, prop)
        value = params["value"]
        if lom.is_path_ref(value):
            # object-valued property, e.g. a rack view's selected_drum_pad
            new_value = lom.resolve_path(self._lom_roots(), value[lom.PATH_KEY])
            setattr(obj, prop, new_value)
            return {"path": path, "prop": prop, "value": lom.serialize(getattr(obj, prop))}
        new_value = lom.coerce_like(current, value)
        setattr(obj, prop, new_value)
        return {"path": path, "prop": prop, "old_value": current, "value": getattr(obj, prop)}

    @command("live_call", modifying=True)
    def cmd_live_call(self, params):
        path = params.get("path", "")
        method = lom.check_attr_name(params.get("method", ""))
        args = params.get("args", []) or []
        if not isinstance(args, (list, tuple)):
            raise ValueError("args must be a list")
        obj = lom.resolve_path(self._lom_roots(), path)
        fn = getattr(obj, method, None)
        if fn is None or not callable(fn):
            raise AttributeError("%r has no callable %r" % (type(obj).__name__, method))
        roots = self._lom_roots()
        call_args = lom.json_to_call_args(args, lambda p: lom.resolve_path(roots, p))
        result = fn(*call_args)
        return {"path": path, "method": method, "result": lom.serialize(result)}

"""Safe Live Object Model path walker.

Paths are space separated tokens rooted at ``live_app`` or ``live_set``::

    live_set tracks 0 devices 1 parameters 2
    live_set view selected_track
    live_set master_track mixer_device volume

Integer tokens index into list-like attributes. Attribute tokens must match
``^[a-z][a-z0-9_]*$`` so dunders and private names are unreachable. Nothing is
ever eval'd or exec'd; only ``getattr`` / ``setattr`` / bound-method calls.
"""
import re

ATTR_RE = re.compile(r"^[a-z][a-z0-9_]*$")
MAX_LIST = 500
PRIMITIVES = (bool, int, float, str)


def _is_int_token(tok):
    return re.match(r"^-?\d+$", tok) is not None


def check_attr_name(name):
    if not isinstance(name, str) or not ATTR_RE.match(name):
        raise ValueError("Illegal attribute name %r (must match ^[a-z][a-z0-9_]*$)" % (name,))
    return name


def resolve_path(roots, path):
    """Walk ``path`` starting from one of ``roots`` (dict name -> object)."""
    if not isinstance(path, str) or not path.strip():
        raise ValueError("path must be a non-empty string like 'live_set tracks 0'")
    tokens = path.split()
    root = tokens[0]
    if root not in roots:
        raise ValueError("Path must start with one of %s, got %r" % (sorted(roots), root))
    obj = roots[root]
    for tok in tokens[1:]:
        if _is_int_token(tok):
            idx = int(tok)
            try:
                seq = list(obj)
            except TypeError:
                raise ValueError("%r is not indexable (token %r)" % (type(obj).__name__, tok))
            if idx < 0 or idx >= len(seq):
                raise IndexError("Index %d out of range (0-%d)" % (idx, len(seq) - 1))
            obj = seq[idx]
        else:
            check_attr_name(tok)
            if not hasattr(obj, tok):
                raise AttributeError("%r has no attribute %r" % (type(obj).__name__, tok))
            obj = getattr(obj, tok)
    return obj


def _is_listlike(value):
    if isinstance(value, PRIMITIVES) or value is None:
        return False
    if isinstance(value, (list, tuple)):
        return True
    # Live vectors are iterable and have __len__ but are not str/dict
    return hasattr(value, "__len__") and hasattr(value, "__iter__") and not isinstance(value, dict)


def serialize(value, path=None, depth=0):
    """JSON-safe view of ``value``. Live objects become ``{type, name, path}``."""
    if value is None or isinstance(value, PRIMITIVES):
        return value
    if isinstance(value, dict):
        return dict((str(k), serialize(v, None, depth + 1)) for k, v in value.items())
    if _is_listlike(value):
        try:
            seq = list(value)
        except Exception:
            seq = []
        if depth >= 1:
            return {"type": "list", "length": len(seq), "path": path}
        out = []
        for i, item in enumerate(seq[:MAX_LIST]):
            child_path = ("%s %d" % (path, i)) if path else None
            out.append(serialize(item, child_path, depth + 1))
        if len(seq) > MAX_LIST:
            out.append({"truncated": True, "total": len(seq)})
        return out
    if callable(value) and not hasattr(value, "name"):
        return {"type": "method", "name": getattr(value, "__name__", "?")}
    info = {"type": type(value).__name__, "path": path}
    try:
        name = getattr(value, "name")
        if isinstance(name, str):
            info["name"] = name
    except Exception:
        pass
    return info


def get_props(obj, props, path=None):
    """Read the listed attribute names from ``obj``."""
    out = {}
    for prop in props:
        check_attr_name(prop)
        try:
            val = getattr(obj, prop)
        except Exception as e:
            out[prop] = {"error": str(e)}
            continue
        child_path = ("%s %s" % (path, prop)) if path else None
        out[prop] = serialize(val, child_path)
    return out


def children(obj, path=None):
    """Enumerate public attributes of ``obj`` grouped as properties / lists / methods / objects."""
    result = {"properties": {}, "lists": {}, "objects": {}, "methods": []}
    for attr in dir(obj):
        if not ATTR_RE.match(attr):
            continue
        try:
            val = getattr(obj, attr)
        except Exception:
            continue
        child_path = ("%s %s" % (path, attr)) if path else None
        if val is None or isinstance(val, PRIMITIVES):
            result["properties"][attr] = val
        elif callable(val) and not _is_listlike(val):
            result["methods"].append(attr)
        elif _is_listlike(val):
            try:
                result["lists"][attr] = len(list(val))
            except Exception:
                result["lists"][attr] = None
        else:
            result["objects"][attr] = serialize(val, child_path)
    result["methods"].sort()
    return result


def coerce_like(current, value):
    """Coerce a JSON value to the type of ``current`` (bool/int/float/str only)."""
    if isinstance(current, bool):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str) and value.lower() in ("true", "false", "1", "0"):
            return value.lower() in ("true", "1")
        raise ValueError("Expected a boolean, got %r" % (value,))
    if isinstance(current, int):
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            return int(float(value))
        raise ValueError("Expected an int, got %r" % (value,))
    if isinstance(current, float):
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            return float(value)
        raise ValueError("Expected a float, got %r" % (value,))
    if isinstance(current, str):
        return str(value)
    raise ValueError("Property holds a %s; only bool/int/float/str properties can be set via live_set"
                     % type(current).__name__)


PATH_KEY = "$path"


def is_path_ref(value):
    """True for ``{"$path": "live_set ..."}``, the JSON form of a Live object reference."""
    return isinstance(value, dict) and list(value.keys()) == [PATH_KEY] and isinstance(value[PATH_KEY], str)


def json_to_call_args(args, resolver=None):
    """Validate call arguments: JSON primitives, (nested) lists of primitives -> tuples,
    or ``{"$path": ...}`` references resolved to Live objects through ``resolver``.
    """
    out = []
    for a in args:
        if a is None or isinstance(a, PRIMITIVES):
            out.append(a)
        elif isinstance(a, (list, tuple)):
            out.append(tuple(json_to_call_args(a, resolver)))
        elif is_path_ref(a):
            if resolver is None:
                raise ValueError("Object references are not supported here")
            out.append(resolver(a[PATH_KEY]))
        else:
            raise ValueError("Unsupported argument %r; only JSON primitives, lists and {\"$path\": ...} are allowed" % (a,))
    return out

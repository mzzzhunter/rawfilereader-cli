import dataclasses
import json

try:
    import numpy as np
    _NUMPY = True
except ImportError:
    _NUMPY = False


def _default(obj):
    if _NUMPY:
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    return str(obj)


def to_json(data, indent=None) -> str:
    return json.dumps(data, default=_default, indent=indent)


def emit_json(data, indent=None):
    print(to_json(data, indent=indent))

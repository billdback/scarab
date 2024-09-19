"""
General utilities for the framework.
"""
import json
from types import SimpleNamespace
from typing import Any, Dict


def object_to_dict(obj: object) -> Dict[str, any]:
    """
    Converts the object to a dictionary of the public properties it contains.
    :param obj: The object to convert.  Only public properties (i.e. ones that don't start with _ will be added.
    """
    res = {}
    for k, v in obj.__dict__.items():
        if not k.startswith("_"):
            res[k] = v

    return res


def object_to_json(obj: object) -> str:
    """
    Converts an object to a JSON string.
    :param obj: The object to convert.  Only public properties (i.e. ones that don't start with _ will be added.
    """
    return json.dumps(object_to_dict(obj))


def serialize(obj: Any) -> Any:
    """Recursively converts SimpleNamespace objects to dictionaries."""
    if isinstance(obj, SimpleNamespace):
        return {k: serialize(v) for k, v in vars(obj).items()}
    elif isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize(v) for v in obj]
    elif isinstance(obj, tuple):
        return tuple(serialize(v) for v in obj)
    else:
        return obj

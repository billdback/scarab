"""
General utilities for the framework.
"""
import json
from typing import Dict


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

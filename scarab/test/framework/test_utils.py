"""
Copyright (c) 2024 William D Back

This file is part of Scarab licensed under the MIT License.
For full license text, see the LICENSE file in the project root.

Test the utilities functions.
"""
import json

from scarab.framework.utils import object_to_dict, object_to_json


class TestObject:
    def __init__(self):
        self.a = 'a'
        self.b = 3.14
        self.c = [1, 2, 3, 4]
        self.d = {'a': 0, 'b': 1}

        # make sure these aren't included.
        self._private = 'private'


def test_obj_to_dict():
    """Test converting an object to the properties."""
    to = TestObject()
    res = object_to_dict(to)

    assert res['a'] == 'a'
    assert res['b'] == 3.14
    assert res['c'] == [1, 2, 3, 4]
    assert res['d'] == {'a': 0, 'b': 1}

    assert not res.get('_private')


def test_obj_to_json():
    """Tests converting to json"""
    to = TestObject()
    res = object_to_json(to)

    r_obj = json.loads(res)
    assert r_obj['a'] == 'a'
    assert r_obj['b'] == 3.14
    assert r_obj['c'] == [1, 2, 3, 4]
    assert r_obj['d'] == {'a': 0, 'b': 1}

    assert not r_obj.get('_private')

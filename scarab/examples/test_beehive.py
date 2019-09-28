"""
Copyright (C) 2019 William D. Back

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

This module provides a simple example of a beehive.  The bees in the hive will buzz or fan to warm or cool the hive
and try to keep it in a given temperature range.

It also includes the test code to show how entities can be verified.
"""
import unittest

from .beehive import *
from scarab.entities import *


class TestBeeEntity(unittest.TestCase):

    def test_bee_creation(self):
        """Tests creating a bee with set values."""
        bee = Bee(buzz_temp=32, fan_temp=100)
        self.assertEqual(32, bee.buzz_temp)
        self.assertEqual(100, bee.fan_temp)
        self.assertFalse(bee.is_buzzing)
        self.assertFalse(bee.is_fanning)

    def test_bee_temp_change(self):
        """Tests temperature updates for the bee."""
        bee = Bee(buzz_temp=32, fan_temp=100)
        self.assertEqual(32, bee.buzz_temp)
        self.assertEqual(100, bee.fan_temp)

        self.assertFalse(bee.is_fanning)
        self.assertFalse(bee.is_buzzing)

        bee.handle_event(EntityChangedEvent(entity_name="outside-temperature", entity_guid="123",
                                            entity_properties={ "current_temp": 101 }))
        self.assertTrue(bee.is_fanning)
        self.assertFalse(bee.is_buzzing)

        bee.handle_event(EntityChangedEvent(entity_name="outside-temperature", entity_guid="123",
                                            entity_properties={ "current_temp": 15 }))
        self.assertFalse(bee.is_fanning)
        self.assertTrue(bee.is_buzzing)

        bee.handle_event(EntityChangedEvent(entity_name="outside-temperature", entity_guid="123",
                                            entity_properties={ "current_temp": 45 }))
        self.assertFalse(bee.is_fanning)
        self.assertFalse(bee.is_buzzing)


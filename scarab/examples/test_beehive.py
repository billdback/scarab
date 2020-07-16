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

from scarab.examples.beehive import *
from scarab.testing import EntityTestWrapper as etw


class TestBee(unittest.TestCase):

    def test_bee_creation(self):
        """Tests creating a bee with set values."""
        bee = etw(Bee(buzz_temp=32, fan_temp=100))
        self.assertEqual(32, bee.buzz_temp)
        self.assertEqual(100, bee.fan_temp)
        self.assertFalse(bee.is_buzzing)
        self.assertFalse(bee.is_fanning)

    def test_bee_temp_change(self):
        """Tests temperature updates for the bee."""
        bee = etw(Bee(buzz_temp=32, fan_temp=100))
        self.assertEqual(32, bee.buzz_temp)
        self.assertEqual(100, bee.fan_temp)

        self.assertFalse(bee.is_fanning)
        self.assertFalse(bee.is_buzzing)

        bee.send_entity_changed_event(entity_name=BEEHIVE_ENTITY_NAME, properties={"current_temp": 101})
        self.assertTrue(bee.is_fanning)
        self.assertFalse(bee.is_buzzing)

        bee.send_entity_changed_event(entity_name=BEEHIVE_ENTITY_NAME, properties={"current_temp": 15})
        self.assertFalse(bee.is_fanning)
        self.assertTrue(bee.is_buzzing)

        bee.send_entity_changed_event(entity_name=BEEHIVE_ENTITY_NAME, properties={"current_temp": 45})
        self.assertFalse(bee.is_fanning)
        self.assertFalse(bee.is_buzzing)


class TestBeehive(unittest.TestCase):

    def test_beehive_creation(self):
        """Tests creating a bee with set values."""
        beehive = etw(Beehive(start_temp=10, buzzing_impact=.25, fanning_impact=.25))
        self.assertEqual(10, beehive.current_temp)
        self.assertEqual(.25, beehive.buzzing_impact)
        self.assertEqual(.25, beehive.fanning_impact)

        self.assertEqual(0, beehive.number_bees_buzzing)
        self.assertEqual(0, beehive.number_bees_fanning)

    def test_adding_and_removing_bees(self):
        """Tests handling new bees."""
        beehive = etw(Beehive(start_temp=10, buzzing_impact=.25, fanning_impact=.25))

        beehive.send_entity_created_event(entity_name=BEE_ENTITY_NAME,
                                          properties={"guid": 1, "is_buzzing": True, "is_fanning": False})
        beehive.send_entity_created_event(entity_name=BEE_ENTITY_NAME,
                                          properties={"guid": 2, "is_buzzing": False, "is_fanning": True})
        beehive.send_entity_created_event(entity_name=BEE_ENTITY_NAME,
                                          properties={"guid": 3, "is_buzzing": False, "is_fanning": True})
        beehive.send_entity_created_event(entity_name=BEE_ENTITY_NAME,
                                          properties={"guid": 4, "is_buzzing": False, "is_fanning": False})

        self.assertEqual(1, beehive.number_bees_buzzing)
        self.assertEqual(2, beehive.number_bees_fanning)

        beehive.send_entity_destroyed_event(entity_name=BEE_ENTITY_NAME, entity_guid=1)
        beehive.send_entity_destroyed_event(entity_name=BEE_ENTITY_NAME, entity_guid=3)

        self.assertEqual(0, beehive.number_bees_buzzing)
        self.assertEqual(1, beehive.number_bees_fanning)

    def test_change_bees(self):
        """Tests handling changes in bees."""

        beehive = etw(Beehive(start_temp=10, buzzing_impact=1, fanning_impact=1))
        beehive.send_entity_created_event(entity_name=BEE_ENTITY_NAME,
                                          properties={"guid": 1, "is_buzzing": False, "is_fanning": False})

        self.assertEqual(0, beehive.number_bees_buzzing)
        self.assertEqual(0, beehive.number_bees_fanning)

        # the following is needed for testing since the framework sends copies.
        # TODO create testing support to replicate simulation behavior.
        beehive.send_entity_changed_event(entity_name=BEE_ENTITY_NAME,
                                          properties={"guid": 1, "is_buzzing": True, "is_fanning": False})
        self.assertEqual(1, beehive.number_bees_buzzing)
        self.assertEqual(0, beehive.number_bees_fanning)

        beehive.send_entity_changed_event(entity_name=BEE_ENTITY_NAME,
                                          properties={"guid": 1, "is_buzzing": False, "is_fanning": True})
        self.assertEqual(0, beehive.number_bees_buzzing)
        self.assertEqual(1, beehive.number_bees_fanning)

    def test_change_temp(self):
        """Tests changes in temperature."""
        beehive = etw(Beehive(start_temp=10, buzzing_impact=.5, fanning_impact=.25))
        self.assertEqual(beehive._outside_temp, beehive.current_temp)

        beehive.send_entity_changed_event(entity_name=OUTSIDE_TEMPERATURE_NAME, properties={"current_temp": 20})
        self.assertEqual(10, beehive.current_temp)
        self.assertEqual(20, beehive._outside_temp)

    def test_time_update(self):
        """Tests handling time updates."""
        beehive = etw(Beehive(start_temp=10, buzzing_impact=.5, fanning_impact=.25))

        # the fan and buzz temps don't matter since they are not used, but they are required.
        # three buzzing and one flapping, so net of two buzzing (warm up).  3*0.5 - 1*0.25 = 1.5-0.25 =  1.25 change.
        beehive.send_entity_created_event(entity_name=BEE_ENTITY_NAME,
                                          properties={"guid": 1, "is_buzzing": True, "is_fanning": False})
        beehive.send_entity_created_event(entity_name=BEE_ENTITY_NAME,
                                          properties={"guid": 2, "is_buzzing": True, "is_fanning": False})
        beehive.send_entity_created_event(entity_name=BEE_ENTITY_NAME,
                                          properties={"guid": 3, "is_buzzing": True, "is_fanning": False})
        beehive.send_entity_created_event(entity_name=BEE_ENTITY_NAME,
                                          properties={"guid": 4, "is_buzzing": False, "is_fanning": True})

        self.assertEqual(10, beehive.current_temp)
        beehive.send_new_time(new_time=1)
        self.assertEqual(11.25, beehive.current_temp)
        beehive.send_new_time(new_time=2)
        self.assertEqual(12.75, beehive.current_temp)


class TestOutsideTemp(unittest.TestCase):
    """Test the outside temp."""

    def test_temp_changes(self):
        """Tests changing temps during the day."""
        ot = etw(OutsideTemperature(min_temp=0, max_temp=720))  # one degree for each minute for easy testing.
        self.assertEqual(0, ot.current_temp)

        ot.send_new_time(new_time=720)
        self.assertEqual(720, ot.current_temp)

        ot.send_new_time(new_time=1440)
        self.assertEqual(0, ot.current_temp)

        ot.send_new_time(new_time=440)
        self.assertEqual(440, ot.current_temp)

        ot.send_new_time(new_time=820)
        self.assertEqual(620, ot.current_temp)


class TestBeehiveDisplayModel(unittest.TestCase):
    """Test the display class."""

    def test_display(self):
        """Tests the display."""
        display = etw(BeehiveDisplayModel())
        display.send_entity_created_event(entity_name=BEEHIVE_ENTITY_NAME, properties={"number_bees": 0})
        # beehive = Beehive(start_temp=50, buzzing_impact=.5, fanning_impact=.5)
        display.send_entity_created_event(entity_name=BEE_ENTITY_NAME,
                                          properties={"guid": 1, "is_buzzing": True, "is_fanning": False})
        display.send_entity_created_event(entity_name=BEE_ENTITY_NAME,
                                          properties={"guid": 2, "is_buzzing": True, "is_fanning": False})
        display.send_entity_created_event(entity_name=BEE_ENTITY_NAME,
                                          properties={"guid": 3, "is_buzzing": True, "is_fanning": False})
        display.send_entity_created_event(entity_name=BEE_ENTITY_NAME,
                                          properties={"guid": 4, "is_buzzing": False, "is_fanning": True})

        display.send_entity_changed_event(entity_name=BEEHIVE_ENTITY_NAME,
                                          properties={"current_temp": 50, "number_bees": 4,
                                                      "number_bees_fanning": 1, "number_bees_buzzing": 3})
        display.send_entity_changed_event(entity_name=OUTSIDE_TEMPERATURE_NAME, properties={"current_temp": 55.0})
        display.send_new_time(new_time=5)


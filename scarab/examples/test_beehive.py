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
from copy import deepcopy

from scarab.simulation import RemoteEntity
from scarab.examples.beehive import *


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

        beehive = Beehive(start_temp=10, buzzing_impact=.25, fanning_impact=.25)
        beehive.current_temp = 101
        bee.handle_event(EntityChangedEvent(entity=beehive, changed_properties=["current_temp"]))
        self.assertTrue(bee.is_fanning)
        self.assertFalse(bee.is_buzzing)

        beehive.current_temp = 15
        bee.handle_event(EntityChangedEvent(entity=beehive, changed_properties=["current_temp"]))
        self.assertFalse(bee.is_fanning)
        self.assertTrue(bee.is_buzzing)

        beehive.current_temp = 45
        bee.handle_event(EntityChangedEvent(entity=beehive, changed_properties=["current_temp"]))
        self.assertFalse(bee.is_fanning)
        self.assertFalse(bee.is_buzzing)


class TestBeehiveEntity(unittest.TestCase):

    def test_beehive_creation(self):
        """Tests creating a bee with set values."""
        beehive = Beehive(start_temp=10, buzzing_impact=.25, fanning_impact=.25)
        self.assertEqual(10, beehive.current_temp)
        self.assertEqual(.25, beehive.buzzing_impact)
        self.assertEqual(.25, beehive.fanning_impact)

        self.assertEqual(0, beehive.number_bees_buzzing)
        self.assertEqual(0, beehive.number_bees_fanning)

    def test_adding_and_removing_bees(self):
        """Tests handling new bees."""
        beehive = Beehive(start_temp=10, buzzing_impact=.25, fanning_impact=.25)

        # the fan and buzz temps don't matter since they are not used, but they are required.
        bee1 = Bee(buzz_temp=25, fan_temp=50)
        bee1.guid = "1"
        bee2 = Bee(buzz_temp=25, fan_temp=50)
        bee2.guid = "2"
        bee3 = Bee(buzz_temp=25, fan_temp=50)
        bee3.guid = "3"
        bee4 = Bee(buzz_temp=25, fan_temp=50)
        bee4.guid = "4"

        bee1.is_buzzing = True
        bee2.is_fanning = True
        bee3.is_fanning = True

        beehive.handle_new_bee(bee=bee1)
        beehive.handle_new_bee(bee=bee2)
        beehive.handle_new_bee(bee=bee3)
        beehive.handle_new_bee(bee=bee4)

        self.assertEqual(1, beehive.number_bees_buzzing)
        self.assertEqual(2, beehive.number_bees_fanning)

        beehive.handle_dead_bee(bee=bee1)
        beehive.handle_dead_bee(bee=bee3)

        self.assertEqual(0, beehive.number_bees_buzzing)
        self.assertEqual(1, beehive.number_bees_fanning)

    def test_change_bees(self):
        """Tests handling changes in bees."""
        bee = Bee(buzz_temp=25, fan_temp=50)
        bee.guid = "1"

        beehive = Beehive(start_temp=10, buzzing_impact=1, fanning_impact=1)
        beehive.handle_new_bee(bee=bee)

        self.assertEqual(0, beehive.number_bees_buzzing)
        self.assertEqual(0, beehive.number_bees_fanning)

        # the following is needed for testing since the framework sends copies.
        # TODO create testing support to replicate simulation behavior.
        bee = RemoteEntity(bee)
        bee.is_buzzing = True
        beehive.handle_bee_update(bee=bee, changed_properties=["is_buzzing"])
        self.assertEqual(1, beehive.number_bees_buzzing)
        self.assertEqual(0, beehive.number_bees_fanning)

        bee = deepcopy(bee)
        bee.is_fanning = True
        bee.is_buzzing = False
        beehive.handle_bee_update(bee=bee, changed_properties=["is_buzzing"])
        self.assertEqual(0, beehive.number_bees_buzzing)
        self.assertEqual(1, beehive.number_bees_fanning)

    def test_change_temp(self):
        """Tests changes in temperature."""
        beehive = Beehive(start_temp=10, buzzing_impact=.5, fanning_impact=.25)

        self.assertEqual(beehive._outside_temp, beehive.current_temp)
        ot = OutsideTemperature()
        ot.current_temp = 20
        beehive.handle_event(EntityChangedEvent(entity=ot, changed_properties=["current_temp"]))
        self.assertEqual(10, beehive.current_temp)
        self.assertEqual(20, beehive._outside_temp)

    def test_time_update(self):
        """Tests handling time updates."""
        beehive = Beehive(start_temp=10, buzzing_impact=.5, fanning_impact=.25)

        # the fan and buzz temps don't matter since they are not used, but they are required.
        # three buzzing and one flapping, so net of two buzzing (warm up).  3*0.5 - 1*0.25 = 1.5-0.25 =  1.25 change.
        bee1 = Bee(buzz_temp=25, fan_temp=50)
        bee1.guid = "1"
        bee1.is_buzzing = True
        beehive.handle_new_bee(bee1)

        bee2 = Bee(buzz_temp=25, fan_temp=50)
        bee2.guid = "2"
        bee2.is_buzzing = True
        beehive.handle_new_bee(bee2)

        bee3 = Bee(buzz_temp=25, fan_temp=50)
        bee3.guid = "3"
        bee3.is_buzzing = True
        beehive.handle_new_bee(bee3)

        bee4 = Bee(buzz_temp=25, fan_temp=50)
        bee4.guid = "4"
        bee4.is_fanning = True
        beehive.handle_new_bee(bee4)

        self.assertEqual(10, beehive.current_temp)
        beehive.handle_time_update(previous_time=0, new_time=1)
        self.assertEqual(11.25, beehive.current_temp)
        beehive.handle_time_update(previous_time=0, new_time=1)
        self.assertEqual(12.75, beehive.current_temp)


class TestOutsideTemp(unittest.TestCase):
    """Test the outside temp."""

    def test_temp_changes(self):
        """Tests changing temps during the day."""
        ot = OutsideTemperature(min_temp=0, max_temp=720)  # one degree for each minute for easy testing.
        self.assertEqual(0, ot.current_temp)
        ot.handle_time_update(previous_time=719, new_time=720)
        self.assertEqual(720, ot.current_temp)
        ot.handle_time_update(previous_time=1339, new_time=1440)
        self.assertEqual(0, ot.current_temp)
        ot.handle_time_update(previous_time=339, new_time=440)
        self.assertEqual(440, ot.current_temp)
        ot.handle_time_update(previous_time=819, new_time=820)
        self.assertEqual(620, ot.current_temp)


class TestBeehiveDisplayModel(unittest.TestCase):
    """Test the display class."""

    def test_display(self):
        """Tests the display."""
        display = BeehiveDisplayModel()
        beehive = Beehive(start_temp=50, buzzing_impact=.5, fanning_impact=.5)

        bee1 = Bee(buzz_temp=25, fan_temp=50)
        bee1.guid = "1"
        bee1.is_buzzing = True
        beehive.handle_new_bee(bee1)

        bee2 = Bee(buzz_temp=25, fan_temp=50)
        bee2.guid = "2"
        bee2.is_buzzing = True
        beehive.handle_new_bee(bee2)

        bee3 = Bee(buzz_temp=25, fan_temp=50)
        bee3.guid = "3"
        bee3.is_buzzing = True
        beehive.handle_new_bee(bee3)

        bee4 = Bee(buzz_temp=25, fan_temp=50)
        bee4.guid = "4"
        bee4.is_fanning = True
        beehive.handle_new_bee(bee4)

        display.handle_beehive_changed(beehive=beehive, changed_properties=["current_temp"])

        outside_temp = OutsideTemperature(min_temp=55.0, max_temp=75.5)
        display.handle_temp_changed(temp=outside_temp, changed_properties=["current_temp"])

        display.handle_time_update(previous_time=4, new_time=5)

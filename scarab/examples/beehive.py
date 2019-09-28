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

from scarab.entities import *


class Bee(Entity):
    """Represents an individual bee in the hive."""

    def __init__(self, buzz_temp, fan_temp):
        """
        Creates a new bee with a comfort range between buzz_temp and fan_temp.
        :param buzz_temp: The minimum temperature for the bee.  Below this level it starts buzzing.
        :type buzz_temp: float
        :param fan_temp: The maximum temperature for the bee.  Above this level the bee starts buzzing.
        :type fan_temp: float
        """
        assert buzz_temp
        assert fan_temp

        self.buzz_temp = buzz_temp
        self.fan_temp = fan_temp
        self.is_buzzing = False
        self.is_fanning = False
        Entity.__init__(self, name="bee")

    @entity_changed_event_handler
    def handle_temperature_change(self, temp_change_event):
        """
        Handles changes to the temperature.
        :param temp_event: The temperature change event.
        :type Event
        :return: None
        """
        new_temp = temp_change_event.current_temp
        if new_temp < self.buzz_temp:
            self.is_buzzing, self.is_fanning = True, False
        elif new_temp > self.fan_temp:
            self.is_buzzing, self.is_fanning = False, True
        else:
            self.is_buzzing, self.is_fanning = False, False


class Beehive(Entity):
    """Represents a beehive for which a range of temperatures is to be met."""

    def __init__(self, min_temp, max_temp):
        """
        Creates a beehive with a standard range of healthy temperatures.
        :param min_temp:  The minimum temperature of the beehive to maintain in degrees F.
        :type min_temp: float
        :param max_temp:  The maxiumum temperature of the beehive to maintain in degrees F.
        :type max_temp: float
        """
        assert min_temp and isinstance(min_temp, float)
        assert max_temp and isinstance(max_temp, float)

        self.min_temp = min_temp
        self.max_temp = min_temp

        Entity.__init__(self, name="beehive")


class OutsideTemperature(Entity):
    """Represents the outside temperature that varies throughout the day."""

    def __init__(self, min_temp=50.0, max_temp=80.0):
        """
        Creates a new outside temperature.  The range of temperatures is fixed and will vary throughout the day.
        :param min_temp:  The minimum temperature of the beehive to maintain in degrees F.  Default 50.0F
        :type min_temp: float
        :param max_temp:  The maxiumum temperature of the beehive to maintain in degrees F.  Default 80.0F
        :type max_temp: float
        """
        assert min_temp and isinstance(min_temp, float)
        assert max_temp and isinstance(max_temp, float)

        self.min_temp = min_temp
        self.max_temp = max_temp
        self.current_temp = (min_temp + max_temp)/2  # todo - figure out to set at the min for midnight (start time)

        Entity.__init__(self, name="outside_temperature")


class BeehiveDisplay(Entity):
    """Displays the results of the beehive."""

    def __init__(self):
        """
        Creates a new beehive display.
        """
        Entity.__init__(self, name="behive_display")
        self.beehive_temp = 0.0
        self.outside_temp = 0.0
        self.known_bees = {}   # keeps track of bees so we know their state.
        self.number_bees_buzzing = 0
        self.number_bees_flapping = 0

    @time_update_event_handler
    def handle_time_update(self, tue):
        """
        Write output on the stats every time an update occurs.
        :param tue: Time update event.
        :type tue: TimeUpdateEvent
        :return: None
        """
        print("=======================================")
        print(f"Update for time {tue.time}")
        print(f"Temperature status:")
        print(f"\toutside temp: {self.outside_temp}F")
        print(f"\thive temp: {self.beehive_temp}F")

        print(f"Bees:")
        print(f"\ttotal bees: {len(self.known_bees.values())}F")
        print(f"\tbees buzzing: {self.number_bees_buzzing}F")
        print(f"\tbees flapping: {self.number_bees_flapping}F")
        print("=======================================")

    @entity_created_event_handler(entity_name="bee")
    def handle_bee_created(self, bee):
        """
        Adds a new bee to be tracked.
        :param bee: The bee.
        :type bee: Bee
        :return: None
        """
        self.known_bees[bee.guid] = bee
        if bee.is_buzzing:
            self.number_bees_buzzing += 1
        elif bee.is_flapping:
            self.number_bees_flapping += 1

    @entity_destroyed_event_handler(entity_name="bee")
    def handle_bee_destruction(self, bee):
        """
        Handles a bee being destroyed.
        :param bee: The bee that was destroyed.
        :type bee: Bee
        :return: None
        """
        dead_bee = self.known_bees.pop(bee.guid)
        if dead_bee.is_buzzing:
            self.number_bees_buzzing -= 1
        elif dead_bee.is_flapping:
            self.number_bees_flapping -= 1

    @entity_changed_event_handler(entity_name="bee")
    def handle_bee_update(self, bee):
        # known_bee = self.known_bees[bee.guid]
        # TODO handle the status change of the bee.
        pass


if __name__ == "__main__":
    print("Running the beehive simulation.")


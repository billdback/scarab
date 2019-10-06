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

    @entity_changed_event_handler(entity_name="beehive")
    def handle_temperature_change(self, temp_change_event):
        """
        Handles changes to the temperature.
        :param temp_change_event: The temperature change event.
        :type temp_change_event: Event
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

    def __init__(self, start_temp, buzzing_impact, fanning_impact):
        """
        Creates a beehive with a standard range of healthy temperatures.
        :param start_temp: The starting temperature for the beehive.
        :type start_temp: float
        :param buzzing_impact: The impact on temperature for any given bee buzzing.
        :type buzzing_impact: float
        :param fanning_impact: The impact on temperature for any given bee fanning.
        :type fanning_impact: float
        :returns: None
        """
        self.current_temp = start_temp
        self.outside_temp = start_temp
        self.buzzing_impact = buzzing_impact
        self.fanning_impact = fanning_impact

        self.known_bees = {}  # keeps track of bees so we know their state.

        Entity.__init__(self, name="beehive")

    def number_bees_buzzing(self):
        """
        Returns the number of bees buzzing.
        :return: The number of bees buzzing.
        :rtype: int
        """
        return sum([1 for b in self.known_bees.values() if b.is_buzzing])

    def number_bees_fanning(self):
        """
        Returns the number of bees fanning.
        :return: The number of bees fanning.
        :rtype: int
        """
        return sum([1 for b in self.known_bees.values() if b.is_fanning])

    @entity_changed_event_handler(entity_name="outside_temperature")
    def handle_outside_temperature_update(self, outside_temperature):
        """
        Handles changes in the outside temperature.
        :param outside_temperature: The outside temperature that changes.
        :type outside_temperature: OutsideTemperature
        :return: None
        """
        self.outside_temp = outside_temperature.temperature

    @time_update_event_handler
    def handle_time_update(self, nte):
        """Handles the time changing to calculate the temp of the hive.
        :param nte: New time event.
        :type nte: NewTimeEvent
        """
        # NOTE that this assumes time stepped, so doesn't account for jumps in time.
        self.current_temp = self.current_temp + \
            (self.number_bees_buzzing() * self.buzzing_impact) - \
            (self.number_bees_fanning() * self.fanning_impact)

    @entity_created_event_handler(entity_name="bee")
    def handle_new_bee(self, bee):
        """
        Handle a new bee being created.
        :param bee: The bee that was created.
        :type bee: Bee
        :return: None
        """
        self.known_bees[bee.guid] = bee

    @entity_destroyed_event_handler(entity_name="bee")
    def handle_dead_bee(self, bee):
        """
        Handle a new bee being destroyed.
        :param bee: The bee that was destroyed.
        :type bee: Bee
        :return: None
        """
        self.known_bees.pop(bee.guid)

    @entity_changed_event_handler(entity_name="bee")
    def handle_bee_update(self, bee):
        """
        Handles bees changing.
        :param bee: The bee that changed.
        :type bee: Bee
        :return: None
        """
        # currently don't do anything for bee changes since have the bee already stored.
        # future versions will likely pass copies of entities for distributed sims, so changes will have to be
        # tracked.  Ideally this can be handled by wrapper classes.
        pass


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
        self.temperature = (min_temp + max_temp) / 2  # todo - figure out to set at the min for midnight (start time)

        Entity.__init__(self, name="outside_temperature")


class BeehiveDisplay(Entity):
    """Displays the results of the beehive."""

    def __init__(self):
        """
        Creates a new beehive display.
        """
        Entity.__init__(self, name="behive_display")
        self.beehive = None
        self.outside_temp = None

    @time_update_event_handler
    def handle_time_update(self, nte):
        """
        Write output on the stats every time an update occurs.
        :param nte: New time event.
        :type nte: NewTimeEvent
        :return: None
        """
        print("=======================================")
        print(f"Update for time {nte.time}")
        print(f"Temperature status:")
        print(f"\toutside temp: {self.outside_temp}F")
        print(f"\thive temp: {self.beehive_temp}F")

        print(f"Bees:")
        print(f"\ttotal bees: {len(self.known_bees.values())}F")
        print(f"\tbees buzzing: {self.beehive.number_bees_buzzing()}F")
        print(f"\tbees fanning: {self.beehive.number_bees_fanning()}F")
        print("=======================================")


if __name__ == "__main__":
    print("Running the beehive simulation.")

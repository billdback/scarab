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

BEE_ENTITY_NAME = "bee"
BEEHIVE_ENTITY_NAME = "beehive"
OUTSIDE_TEMPERATURE_NAME = "outside_temperature"
BEEHIVE_DISPLAY_MODEL_NAME = "beehive_display_model"


class Bee(Entity):
    """Represents an individual bee in the hive."""

    def __init__(self, buzz_temp, fan_temp):
        """
        Creates a new bee with a comfort range between buzz_temp and fan_temp.
        :param float buzz_temp: The minimum temperature for the bee.  Below this level it starts buzzing.
        :param float fan_temp: The maximum temperature for the bee.  Above this level the bee starts buzzing.
        """
        assert buzz_temp
        assert fan_temp

        self.buzz_temp = buzz_temp
        self.fan_temp = fan_temp
        self.is_buzzing = False
        self.is_fanning = False
        super().__init__(name=BEE_ENTITY_NAME)

    @entity_changed_event_handler(entity_name=BEEHIVE_ENTITY_NAME)
    def handle_temperature_change(self, beehive, changed_properties) -> None:
        """
        Handles changes to the temperature in the hive.
        :param Beehive beehive: The beehive that had a temp change.
        :param dict changed_properties: The properties that changed.  Only interested in temp changes.
        :return: None
        """
        if "current_temp" in changed_properties:
            new_temp = beehive.current_temp
            if new_temp < self.buzz_temp:
                self.is_buzzing, self.is_fanning = True, False
            elif new_temp > self.fan_temp:
                self.is_buzzing, self.is_fanning = False, True
            else:
                self.is_buzzing, self.is_fanning = False, False


class Beehive(Entity):
    """Represents a beehive for which a range of temperatures is to be met."""

    def __init__(self, start_temp, buzzing_impact, fanning_impact) -> None:
        """
        Creates a beehive with a standard range of healthy temperatures.
        :param float start_temp: The starting temperature for the beehive.
        :param float buzzing_impact: The impact on temperature for any given bee buzzing.
        :param float fanning_impact: The impact on temperature for any given bee fanning.
        :returns: None
        """
        self.current_temp = start_temp
        self._outside_temp = start_temp
        self.buzzing_impact = buzzing_impact
        self.fanning_impact = fanning_impact

        self.number_bees = 0
        self.number_bees_buzzing = 0
        self.number_bees_fanning = 0

        self.__known_bees = {}  # keeps track of bees so we know their state.

        super().__init__(name=BEEHIVE_ENTITY_NAME)

    def get_number_bees_buzzing(self) -> int:
        """
        Returns the number of bees buzzing.
        :return: The number of bees buzzing.
        """
        return sum([1 for b in self.__known_bees.values() if b.is_buzzing])

    def get_number_bees_fanning(self) -> int:
        """
        Returns the number of bees fanning.
        :return: The number of bees fanning.
        """
        return sum([1 for b in self.__known_bees.values() if b.is_fanning])

    @entity_changed_event_handler(entity_name=OUTSIDE_TEMPERATURE_NAME)
    def handle_outside_temperature_update(self, outside_temperature, changed_properties) -> None:
        """
        Handles changes in the outside temperature.
        :param RemoteEntity outside_temperature: The outside temperature that changes.
        :param list of str changed_properties: List of properties that changed.
        :return: None
        """
        assert changed_properties
        self._outside_temp = outside_temperature.current_temp

    @time_update_event_handler
    def handle_time_update(self, previous_time, new_time) -> None:
        """
        Handles the time changing to calculate the temp of the hive.
        :param int previous_time: The previous simulation time.
        :param int new_time: The new simulation time.
        """
        assert new_time > previous_time

        # Note that weird things might happen if there are jumps in time because the bees may have state changes that
        # were missed.
        bee_impact = (self.get_number_bees_buzzing() * self.buzzing_impact) - \
                     (self.get_number_bees_fanning() * self.fanning_impact)
        total_bee_impact = bee_impact * (new_time - previous_time)

        # The impact of the outside temp is 20% of the difference.  So the warmer it gets, the more the hive wants
        # to heat.  Reverse for cooler.
        if self._outside_temp > self.current_temp:
            outside_temp_impact = .2 * (self._outside_temp - self.current_temp)
        else:
            outside_temp_impact = .2 * (self.current_temp - self._outside_temp)

        self.current_temp = self.current_temp + outside_temp_impact + total_bee_impact

    @entity_created_event_handler(entity_name=BEE_ENTITY_NAME)
    def handle_new_bee(self, bee) -> None:
        """
        Handle a new bee being created.
        :param RemoteEntity bee: The bee that was created.
        :return: None
        """
        self.number_bees += 1
        self.__known_bees[bee.guid] = bee

        if bee.is_fanning:
            self.number_bees_fanning += 1
        if bee.is_buzzing:
            self.number_bees_buzzing += 1

    @entity_destroyed_event_handler(entity_name=BEE_ENTITY_NAME)
    def handle_dead_bee(self, bee) -> None:
        """
        Handle a new bee being destroyed.
        :param RemoteEntity bee: The bee that was destroyed.
        :return: None
        """
        self.number_bees -= 1
        bee = self.__known_bees.pop(bee.guid)

        if bee.is_fanning:
            self.number_bees_fanning -= 1
        if bee.is_buzzing:
            self.number_bees_buzzing -= 1

    @entity_changed_event_handler(entity_name=BEE_ENTITY_NAME)
    def handle_bee_update(self, bee, changed_properties) -> None:
        """
        Handles bees changing.
        :param RemoteEntity bee: The bee that changed.
        :param list of str changed_properties: The properties that changed.
        :return: None
        """
        assert bee and changed_properties

        prev_bee = self.__known_bees[bee.guid]  # gets the previous state of the bee.
        self.__known_bees[bee.guid] = bee

        if prev_bee.is_fanning and not bee.is_fanning:  # was fanning and isn't now.
            self.number_bees_fanning -= 1
        if bee.is_fanning and not prev_bee.is_fanning:  # wasn't fanning and is now.
            self.number_bees_fanning += 1

        if prev_bee.is_buzzing and not bee.is_buzzing:  # was buzzing and isn't now.
            self.number_bees_buzzing -= 1
        if bee.is_buzzing and not prev_bee.is_buzzing:  # wasn't buzzing and is now.
            self.number_bees_buzzing += 1


class OutsideTemperature(Entity):
    """Represents the outside temperature that varies throughout the day."""

    def __init__(self, min_temp=50.0, max_temp=80.0) -> None:
        """
        Creates a new outside temperature.  The range of temperatures is fixed and will vary throughout the day.
        :param float min_temp:  The minimum temperature of the beehive to maintain in degrees F.  Default 50.0F
        :param float max_temp:  The maximum temperature of the beehive to maintain in degrees F.  Default 80.0F
        """
        assert min_temp is not None
        assert max_temp is not None

        self.min_temp = float(min_temp)
        self.max_temp = float(max_temp)

        # Temp only varies by time of day, so just create a an array that pre-calculates the temps.
        self.__increment_change = (self.max_temp - self.min_temp) / (
                    24 * 60 / 2)  # increment over half days up and down.
        self.__minute_temps = []
        for minute in range(0, int(12 * 60)):  # calculate increasing temps
            self.__minute_temps.append(self.min_temp + self.__increment_change * minute)
        for minute in range(0, int(12 * 60)):  # calculate decreasing
            self.__minute_temps.append(self.max_temp - self.__increment_change * minute)

        self.current_temp = self.__minute_temps[0]

        super().__init__(name=OUTSIDE_TEMPERATURE_NAME)

    @time_update_event_handler
    def handle_time_update(self, previous_time, new_time) -> None:
        """Handles the time changing to calculate the temp of the hive.
        :param int previous_time: The previous simulation time.
        :param int new_time: The new simulation time.
        """
        assert previous_time is not None
        self.current_temp = self.__minute_temps[new_time % len(self.__minute_temps)]


class BeehiveDisplayModel(Entity):
    """Manages content for display by the application.  Used instead of the beehive display class."""

    def __init__(self):
        """
        Creates a new beehive display model.
        """
        super().__init__(name=BEEHIVE_DISPLAY_MODEL_NAME)

        self.beehive = None
        self.outside_temp = None

        # mins are set to a very large number so they will be properly set the next time.
        self.min_outside_temp = 1000000
        self.max_outside_temp = 0
        self.min_hive_temp = 1000000
        self.max_hive_temp = 0
        self.min_number_bees = 1000000
        self.max_number_bees = 0
        self.min_number_bees_buzzing = 1000000
        self.max_number_bees_buzzing = 0
        self.min_number_bees_fanning = 1000000
        self.max_number_bees_fanning = 0

        self.previous_time = -1
        self.new_time = 0

    @entity_changed_event_handler(entity_name=BEEHIVE_ENTITY_NAME)
    def handle_beehive_changed(self, beehive, changed_properties) -> None:
        """
        Handles the beehive changing.
        :param RemoteEntity beehive: The beehive that changed.
        :param list of str changed_properties: The properties that changed.
        """
        assert changed_properties is not None
        self.beehive = beehive

        self.min_hive_temp = min(self.min_hive_temp, beehive.current_temp)
        self.max_hive_temp = max(self.max_hive_temp, beehive.current_temp)

        self.min_number_bees = min(self.min_number_bees, beehive.number_bees)
        self.max_number_bees = max(self.max_number_bees, beehive.number_bees)
        self.min_number_bees_fanning = min(self.min_number_bees_fanning, beehive.number_bees_fanning)
        self.max_number_bees_fanning = max(self.max_number_bees_fanning, beehive.number_bees_fanning)
        self.min_number_bees_buzzing = min(self.min_number_bees_buzzing, beehive.number_bees_buzzing)
        self.max_number_bees_buzzing = max(self.max_number_bees_buzzing, beehive.number_bees_buzzing)

    @entity_changed_event_handler(entity_name=OUTSIDE_TEMPERATURE_NAME)
    def handle_temp_changed(self, temp, changed_properties) -> None:
        """Handles the outside temp changing.
        :param RemoteEntity temp: The temperature entity that changed.
        :param list of str changed_properties: The properties that changed.
        :return: None
        """
        assert changed_properties
        self.outside_temp = temp.current_temp
        self.min_outside_temp = min(self.min_outside_temp, self.outside_temp)
        self.max_outside_temp = max(self.max_outside_temp, self.outside_temp)

    @time_update_event_handler
    def handle_time_update(self, previous_time, new_time) -> None:
        """
        Handles the time changing to calculate the temp of the hive.
        :param int previous_time: The previous simulation time.
        :param int new_time: The new simulation time.
        """
        assert previous_time is not None
        self.previous_time = previous_time
        self.new_time = new_time

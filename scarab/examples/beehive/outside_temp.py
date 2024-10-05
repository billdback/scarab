"""
Copyright (c) 2024 William D Back

This file is part of Scarab licensed under the MIT License.
For full license text, see the LICENSE file in the project root.

Represents the outside temperature that will vary throughout the day.
"""

import math

from scarab.framework.entity import Entity, time_updated
from scarab.framework.events import TimeUpdatedEvent

from scarab.examples.beehive.beesim_types import OutsideTempType


class TimeConstants:
    MINUTES_IN_DAY = 1440  # Total minutes in a day
    TWO_AM_MINUTES = 120  # Minute for 2am, which we'll let be the coldest part of the day.
    TWO_PM_MINUTES = 840  # Minute for 2pm, which we'll let be the hottest part of the day.


@Entity(name="outside-temperature", conforms_to=OutsideTempType)
class OutsideTemp:
    """
    The outside temperature is the daily outside temperature.  The temperature varies linearly throughout the day,
    being hottest at 2pm and the coldest at 2am.

    NOTE: Time will advance in 10 minute intervals, so simtime 3 is 12:30am.
    """

    def __init__(self, min_temp: float, max_temp: float):
        """
        Creates a new outside temp class.
        :param min_temp: The minimum temperature to reach.
        :param max_temp: The maximum temperature to reach.
        """
        self.min_temp = min_temp
        self.max_temp = max_temp
        self.current_temp = self.min_temp
        self.time_of_day = 0  # minute of the day

    @time_updated()
    def time_updated(self, tue: TimeUpdatedEvent) -> None:
        """
        Called when simulation time updates to update the outside temperature.
        :param tue: TimeUpdatedEvent the new simulation time.
        """
        adj_sim_time = tue.sim_time * 10  # doing 10-minute intervals, so a day has 240 simtime increments.
        self.time_of_day = adj_sim_time % TimeConstants.MINUTES_IN_DAY  # Minute of the current day

        self.current_temp = round(self.temperature_by_time_of_day(adj_sim_time), 2)
        print(f"Current outside temperature: {self.current_temp}")

    def temperature_by_time_of_day(self, time_in_minutes):
        # Time of day in minutes: 0 minutes is midnight, 1440 minutes is the end of the day (midnight next day)
        # Normalized time based on 2 AM (120 min) to 2 PM (840 min)
        time_of_day = (time_in_minutes - 120) % 1440

        # Amplitude of temperature variation
        amplitude = (self.max_temp - self.min_temp) / 2

        # Average temperature is the midpoint between min and max
        avg_temp = (self.max_temp + self.min_temp) / 2

        # Use a cosine wave with a period of 1440 minutes (24 hours) and a phase shift
        temperature = avg_temp - amplitude * math.cos(2 * math.pi * time_of_day / 1440)

        return temperature

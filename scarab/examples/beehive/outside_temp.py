"""
Represents the outside temperature that will vary throughout the day.
"""

from scarab.framework.entity import Entity, time_updated
from scarab.framework.events import TimeUpdatedEvent

from .beesim_types import OutsideTempType


@Entity(name="outside-temperature", conforms_to=OutsideTempType)
class OutsideTemp:
    """
    The outside temperature is the daily outside temperature.  The temperature varies linearly throughout the day,
    being hottest at noon.
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
        self.time_of_date = 0  # minute of the day

    @time_updated()
    def time_updated(self, tue: TimeUpdatedEvent) -> None:
        """
        Called when simulation time updates to update the outside temperature.
        :param tue: TimeUpdatedEvent the new simulation time.
        """
        # tue.sim_time is in minutes and continues to grow indefinitely
        minutes_in_day = 1440  # Total minutes in a day
        self.time_of_date = tue.sim_time % minutes_in_day  # Minute of the current day

        # Calculate temperature based on time of day
        if self.time_of_date <= 840:  # From midnight to 2 PM (0 to 840 minutes)
            # Linear increase from min_temp to max_temp
            temp_range = self.max_temp - self.min_temp
            time_fraction = self.time_of_date / 840  # Fraction of time passed till 2 PM
            self.current_temp = self.min_temp + temp_range * time_fraction
        else:  # From 2 PM to midnight (840 to 1440 minutes)
            # Linear decrease from max_temp back to min_temp
            temp_range = self.max_temp - self.min_temp
            time_fraction = (self.time_of_date - 840) / 600  # 600 minutes from 2 PM to midnight
            self.current_temp = self.max_temp - temp_range * time_fraction

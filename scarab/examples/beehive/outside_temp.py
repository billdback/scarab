"""
Represents the outside temperature that will vary throughout the day.
"""

from . types import OutsideTempType
from scarab.framework.entity import Entity


@Entity(name="outside-temp", conforms_to=OutsideTempType)
class DailyTemperature:

    def __init__(self, max_temp: float, min_temp: float):
        """
        Creates a new outside temp entity.
        :param max_temp: The max temperature during the day.
        :param min_temp: The minimum temperature during the day.
        """
        self.current_temp = min_temp  # TODO figure out a better approach starting at start time of day.

        self.max_temp = max_temp
        self.min_temp = min_temp

"""
Copyright (c) 2024 William D Back

This file is part of Scarab licensed under the MIT License.
For full license text, see the LICENSE file in the project root.

Defines the types for the entities.

WARNING: Trying to name a file `types` can cause errors when importing.
"""
from dataclasses import dataclass


@dataclass
class BeeType:
    """
    A bee represents individual bees.  When it gets too hot, the bee will being flapping to cool the hive.
    When it gets too cool, the bee will begin buzzing to warm up the hive.
    Sim name: bee
    """
    isBuzzing: bool = False
    isFlapping: bool = False


@dataclass
class HiveType:
    """
    The hive has a number of bees that are flapping, buzzing, or being quiet at any given time.
    The number of bees along with the outside temp will cause the temperature of the hive to change.
    Sim name: hive
    """
    number_of_bees: int = 0
    number_of_bees_flapping: int = 0
    number_of_bees_buzzing: int = 0
    current_temp: float = 0.0


@dataclass
class OutsideTempType:
    """
    The outside temperature throughout the day.  This will vary, having an impact on the hive.
    Sim name: outside-temp
    """
    current_temp: float = 0.0
    time_of_day: int = 0.0 # minute of the day.


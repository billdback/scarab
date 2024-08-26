"""
The hive consist of the bees and has a temperature that the bees will attempt to keep within a certain bounds.
"""
import functools
from typing import Dict, List

from . types import BeeType, HiveType

# TODO make this more simple vs. importing everything.
from scarab.framework.entity import Entity, entity_created


@Entity(name="hive", conforms_to=HiveType)
class Hive:

    def __init__(self):
        """
        Creates a new hive.
        :param desired_temp: The desired temperature of the hive.
        """
        self.current_temp = 0.0
        self.bees: Dict[str, BeeType] = {}

    # Scarab Example: The following is a required type for a hive, but is declared as a property.
    @property
    def number_of_bees(self) -> int:
        """Returns the number of bees."""
        return len(self.bees)

    @property
    def number_buzzing(self) -> int:
        return functools.reduce(lambda a, b: a + 1 if b.isBuzzing else a, list(self.bees.values()),0)

    @property
    def number_flapping(self) -> int:
        return functools.reduce(lambda a, b: a + 1 if b.isFlapping else a, list(self.bees.values()),0)

    @entity_created('bee')
    def bee_created(self, bee):
        """Handle the new bee."""
        self.bees[bee.scarab_id] = bee

#     @entity_updated('bee')
#     def bee_updated(self, bee):
#         """Handle bee changes."""
#
#     @entity_destroyed('bee')
#     def bee_destroyed(self, bee):
#         """Handle bees being destroyed (dying or flying off)."""
#
#     @entity_updated('outside-temp')
#     def ouside_temp_changed(self, outside_temp):
#         """Handle changes to the outside temperature."""
#
#     @time_update
#     def time_changed(self, new_time):
#         """Handles time updates by updating the temp in the hive based on outside temp and bee behavior."""

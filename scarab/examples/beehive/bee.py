"""
Copyright (c) 2024 William D Back

This file is part of Scarab licensed under the MIT License.
For full license text, see the LICENSE file in the project root.

Represents the bee entity.
"""
from .beesim_types import BeeType, HiveType

from scarab.framework.entity import Entity, entity_created, entity_changed
from scarab.framework.events import EntityCreatedEvent, EntityChangedEvent


@Entity(name="bee", conforms_to=BeeType)
class Bee:
    """Description of Bee."""

    def __init__(self, low_temp: float, high_temp: float):
        """Creates an instance of Bee, setting low_temp and high_temp."""
        self.low_temp = low_temp
        self.high_temp = high_temp
        self.isBuzzing = False
        self.isFlapping = False

    @entity_created(entity_name='hive')
    def hive_created(self, ce: EntityCreatedEvent):
        """Called when a 'hive' entity is created."""
        self._set_state(hive=ce.entity)

    @entity_changed(entity_name='hive')
    def hive_changed(self, ue: EntityChangedEvent):
        """Called when a 'hive' entity is changed."""
        self._set_state(hive=ue.entity)

    def _set_state(self, hive: HiveType) -> None:
        """
        Sets the state of the bee depending on the hive temperature.
        :param hive: The hive entity.
        """
        if hive.current_temp < self.low_temp:
            self.isBuzzing = True
            self.isFlapping = False
        elif hive.current_temp > self.high_temp:
            self.isBuzzing = False
            self.isFlapping = True
        else:  # in case either was True before.
            self.isBuzzing = False
            self.isFlapping = False

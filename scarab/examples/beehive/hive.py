"""
The hive consist of the bees and has a temperature that the bees will attempt to keep within a certain bounds.
"""

import os

from scarab.framework.entity import Entity, entity_created, entity_changed
from scarab.framework.events import EntityCreatedEvent, EntityChangedEvent

from .beesim_types import HiveType

"""
This file contains the entity type Hive, which represents the hive in the simulation.
"""

from dataclasses import dataclass

from scarab.framework.entity import Entity, entity_created, entity_changed, entity_destroyed, time_updated
from scarab.framework.events import EntityCreatedEvent, EntityChangedEvent, EntityDestroyedEvent, TimeUpdatedEvent


@Entity(name="hive", conforms_to=HiveType)
class Hive:
    """
    The hive is the actual beehive.  The temperature of the hive will vary based on the outside temp and the
    behavior of the bees.
    """

    def __init__(self):
        """Initializes the Hive entity."""
        self.number_of_bees = 0
        self.number_of_bees_flapping = 0
        self.number_of_bees_buzzing = 0
        self.current_temp = 0.0
        self.bees = {}  # Dictionary to keep track of bees
        self.outside_temp = None  # Will hold the current outside temperature

        self.buzzing_impact = 0.1  # warm the hive
        self.flapping_impact = -0.1 # cool the hive

    @entity_created(entity_name='bee')
    def bee_created(self, ce: EntityCreatedEvent):
        """Called when a 'bee' entity is created."""
        self.number_of_bees += 1
        bee_id = ce.entity.scarab_id
        bee = ce.entity
        self.bees[bee_id] = ce.entity

        # Update counts if the bee is buzzing or flapping at creation
        if bee.isFlapping:
            self.number_of_bees_flapping += 1
        if bee.isBuzzing:
            self.number_of_bees_buzzing += 1

    @entity_changed(entity_name='bee')
    def bee_changed(self, ue: EntityChangedEvent):
        """Called when a 'bee' entity is changed."""
        bee_id = ue.entity.scarab_id
        old_bee = self.bees.get(bee_id)
        updated_bee = ue.entity
        self.bees[bee_id] = updated_bee

        # Update flapping count
        if old_bee.isFlapping != updated_bee.isFlapping:
            if updated_bee.isFlapping:
                self.number_of_bees_flapping += 1
            else:
                self.number_of_bees_flapping -= 1

        # Update buzzing count
        if old_bee.isBuzzing != updated_bee.isBuzzing:
            if updated_bee.isBuzzing:
                self.number_of_bees_buzzing += 1
            else:
                self.number_of_bees_buzzing -= 1

        # Update stored state
        self.bees[bee_id] = updated_bee

    @entity_destroyed(entity_name='bee')
    def bee_destroyed(self, de: EntityDestroyedEvent):
        """Called when a 'bee' entity is destroyed."""
        bee_id = de.entity.entity_id
        bee = self.bees.pop(bee_id, None)

        if bee:
            self.number_of_bees -= 1

            # Update flapping count
            if bee.isFlapping:
                self.number_of_bees_flapping -= 1

            # Update buzzing count
            if bee.isBuzzing:
                self.number_of_bees_buzzing -= 1

            # Optionally update the hive temperature
            self.update_hive_temperature()

    @entity_created(entity_name='outside-temperature')
    def outside_temp_created(self, ce: EntityCreatedEvent):
        """Called when the 'outside-temperature' entity is created."""
        self.outside_temp = ce.entity
        self.current_temp = ce.entity.current_temp

    @entity_changed(entity_name='outside-temperature')
    def outside_temp_changed(self, ue: EntityChangedEvent):
        """
        Called when the 'outside-temperature' entity is changed.
        :param ue: The outside temperature that varies throughout the day.
        """
        self.outside_temp = ue.entity.current_temp
        self.update_hive_temperature()

    def update_hive_temperature(self):
        """
        Updates the hive's current temperature based on outside temp and bee activities.
        """

        activity_effect = (self.number_of_bees_buzzing * self.buzzing_impact) + (self.number_of_bees_flapping * self.flapping_impact)
        # TODO have the current temp change based on the outside temp diff vs. current and activity.
        self.current_temp = self.outside_temp.current_temp + activity_effect

    @time_updated()
    def time_updated(self, tue: TimeUpdatedEvent) -> None:
        """
        Simple logger for the sim to show the temps and bee activities.
        :param tue: The time update event.
        """
        # Clears the screen.  For Windows use `os.system('cls').
        os.system('clear')

        print(f"Current time: {tue.sim_time}")

        print(f"Total number of bees: {self.number_of_bees}")
        print(f"Number of bees flapping: {self.number_of_bees_flapping}")
        print(f"Number of bees buzzing: {self.number_of_bees_buzzing}")

        print(f"\nCurrent hive temperature: {self.current_temp}")
        print(f"Outside temperature: {self.outside_temp}")


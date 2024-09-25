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
        self.bee_states = {}  # Dictionary to keep track of bee states
        self.outside_temp = None  # Will hold the current outside temperature

        self.buzzing_impact = 0.1  # warm the hive
        self.flapping_impact = -0.1 # cool the hive

    @entity_created(entity_name='bee')
    def bee_created(self, ce: EntityCreatedEvent):
        """Called when a 'bee' entity is created."""
        self.number_of_bees += 1
        bee_id = ce.scarab_id
        bee_state = ce.entity
        self.bee_states[bee_id] = bee_state

        # Update counts if the bee is buzzing or flapping at creation
        if bee_state.isFlapping:
            self.number_of_bees_flapping += 1
        if bee_state.isBuzzing:
            self.number_of_bees_buzzing += 1

    @entity_changed(entity_name='bee')
    def bee_changed(self, ue: EntityChangedEvent):
        """Called when a 'bee' entity is changed."""
        bee_id = ue.scarab_id
        old_state = self.bee_states.get(bee_id)
        new_state = ue.new_state

        # Update flapping count
        if old_state.isFlapping != new_state.isFlapping:
            if new_state.isFlapping:
                self.number_of_bees_flapping += 1
            else:
                self.number_of_bees_flapping -= 1

        # Update buzzing count
        if old_state.isBuzzing != new_state.isBuzzing:
            if new_state.isBuzzing:
                self.number_of_bees_buzzing += 1
            else:
                self.number_of_bees_buzzing -= 1

        # Update stored state
        self.bee_states[bee_id] = new_state

    @entity_destroyed(entity_name='bee')
    def bee_destroyed(self, de: EntityDestroyedEvent):
        """Called when a 'bee' entity is destroyed."""
        bee_id = de.entity_id
        bee_state = self.bee_states.pop(bee_id, None)
        if bee_state:
            self.number_of_bees -= 1

            # Update flapping count
            if bee_state.isFlapping:
                self.number_of_bees_flapping -= 1

            # Update buzzing count
            if bee_state.isBuzzing:
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


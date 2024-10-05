"""
Copyright (c) 2024 William D Back

This file is part of Scarab licensed under the MIT License.
For full license text, see the LICENSE file in the project root.
"""
from typing import Dict, List

from scarab.framework.entity import scarab_properties
from scarab.framework.events import EntityCreatedEvent, EntityChangedEvent, EntityDestroyedEvent, \
    SimulationStartEvent, SimulationPauseEvent, SimulationResumeEvent, SimulationShutdownEvent, \
    TimeUpdatedEvent, Event

from scarab.framework.simulation._event_router import EventRouter
from scarab.framework.simulation.simulation import new_sim_id
from scarab.framework.types import SimID


class Simulation:
    """
    This class is a simplified version of the Simulation class that allows for easy testing of entities.  All functions
    in this class are synchronous to make testing easier.

    What it does:

    * Can add entities
    * Can send events (and includes specific functions for each type of valid event).
    * Can step one time unit at a time.

    What is not supported:

    * Web socket.
    * Running for multiple steps.
    """

    def __init__(self):
        """
        Creates a new test simulation with the minimum needed to support testing.
        """
        # Technically has entities, but entities are simply objects with scarab_ properties.
        self._entities: Dict[SimID, object] = {}

        self._event_router = EventRouter()

    @staticmethod
    def add_id(entity: object) -> object:
        """
        Adds a sim ID to the entity and returns it.  This is needed because some entities won't be added to the sim and
        therefore never get an ID.  If the ID of the entity is important to other entities, then it needs to have one.
        :param entity: The entity to add the ID to.  A check will be made to ensure this is an entity.
        :return: The modified entity.
        """
        assert hasattr(entity, "scarab_id")  # basic check that this is an entity.

        entity.scarab_id = new_sim_id()
        return entity

    def add_entity(self, entity: object) -> None:
        """
        Adds the entity to the simulation.  An ID will be assigned to the entity, potentially overwriting an existing
        one.
        :param entity: The entity to add.  Entities can technically be any class, but will have the scarab attributes.
        """
        assert hasattr(entity, "scarab_id")  # basic check that this is an entity.

        entity.scarab_id = new_sim_id()
        self._entities[entity.scarab_id] = entity
        self._event_router.register(entity=entity)

        self.send_entity_created_event(entity=entity)

    def route(self, event) -> None:
        """
        Synchronously routes the given event.
        :param event: The event to route.
        """
        self._event_router.sync_route(event=event)

    # ####################### The following methods to make sending specific events easier. #######################

    def send_entity_created_event(self, entity: object) -> None:
        """
        Sends an entity created event for the given entity.
        :param entity: The entity to send.
        """

        assert hasattr(entity, "scarab_id")  # basic check that this is an entity.
        self.route(EntityCreatedEvent(entity_props=scarab_properties(entity)))

    def send_entity_changed_event(self, entity: object, changed_props: List[str]) -> None:
        """
        Sends an entity changed event for the given entity and specified props.
        :param entity: The entity to send.
        :param changed_props: The list of properties that changed.  The caller has to get these right.
        """

        assert hasattr(entity, "scarab_id")  # basic check that this is an entity.
        self.route(
            EntityChangedEvent(entity_props=scarab_properties(entity), changed_props=changed_props))

    def send_entity_destroyed_event(self, entity: object) -> None:
        """
        Sends an entity destroyed event for the given entity.
        :param entity: The entity to send.
        """

        assert hasattr(entity, "scarab_id")  # basic check that this is an entity.
        self.route(EntityDestroyedEvent(entity_props=scarab_properties(entity)))

    def send_simulation_start_event(self, sim_time: int = 0) -> None:
        """
        Sends a simulation start event.
        :param sim_time: The time for the start of the simulation.  Default: 0
        """
        self.route(SimulationStartEvent(sim_time=sim_time))

    def send_simulation_pause_event(self, sim_time: int = 2) -> None:
        """
        Sends a simulation pause event.
        :param sim_time: The time of the pause.  Default: 2
        """
        self.route(SimulationPauseEvent(sim_time=sim_time))

    def send_simulation_resume_event(self, sim_time: int = 3) -> None:
        """
        Sends a simulation pause event.
        :param sim_time: The time of the resume.  Default: 3
        """
        self.route(SimulationResumeEvent(sim_time=sim_time))

    def send_simulation_shutdown_event(self, sim_time: int = 4) -> None:
        """
        Sends a simulation shutdown event.
        :param sim_time: The time of the shutdown.  Default: 4
        """
        self.route(SimulationShutdownEvent(sim_time=sim_time))

    def send_simulation_time_updated(self, sim_time: int = 2, prev_time: int = None) -> None:
        """
        Sends a time updated event.  If no times are provided, then it will default to moving from 1 to 2.  The
        prev_time _must_ be earlier than the sim_time.
        :param sim_time: The new simulation time.  Default: 2
        :param prev_time: The previous simulation time.  Default: sim_time - 1
        """
        if prev_time is None:
            prev_time = sim_time - 1

        self.route(TimeUpdatedEvent(sim_time=sim_time, previous_time=prev_time))

    def send_event(self, event: Event) -> None:
        """
        Sends a generic event.
        :param event: The event to send.
        """
        self.route(event)

"""
Contains standard events for the simulation.
"""

from enum import StrEnum
import json
from typing import Any, Dict, List
from types import SimpleNamespace


# Names of standard events.
class ScarabEventType(StrEnum):
    NAMED_EVENT = "scarab.named-event"
    ENTITY_CREATED = "scarab.entity.created"
    ENTITY_DESTROYED = "scarab.entity.destroyed"
    ENTITY_CHANGED = "scarab.entity.changed"
    TIME_UPDATED = "scarab.time.updated"
    SIMULATION_START = "scarab.simulation.start"
    SIMULATION_PAUSE = "scarab.simulation.pause"
    SIMULATION_RESUME = "scarab.simulation.resume"
    SIMULATION_SHUTDOWN = "scarab.simulation.shutdown"


# convenience list to show the standard names.
standard_event_names = [en for en in ScarabEventType]


class Event:
    """
    Base event type.
    """

    def __init__(self, event_name: str, sim_time: int = None):
        """
        Creates a new event.
        :param event_name: Name of the event.
        :param sim_time: Time the event occurred.  If the time is None, then the current time is used.
        """
        self.event_name = event_name
        self.sim_time = sim_time

    def to_json(self) -> Dict[str, Any]:
        """Converts the event to JSON.  All public attributes will be returned."""
        # Use vars(self) to get the public attributes into a dictionary
        data_dict = {k: v for k, v in vars(self).items() if not k.startswith('_')}
        return data_dict

    def __str__(self):
        """Returns the string representation of the event as a JSON string."""
        return json.dumps(self.to_json(), sort_keys=True)


class EntityCreatedEvent(Event):
    """
    Event for new entities that got created.
    """

    def __init__(self, entity_props: Dict[str, Any], sim_time: int = None):
        """
        Event for new entities that were just created.
        :param entity_props: The entity properties (using the Scarab props).
        :param sim_time: The sim time for the event.
        """
        super().__init__(ScarabEventType.ENTITY_CREATED, sim_time)
        self.entity = SimpleNamespace(**entity_props)


class EntityChangedEvent(Event):
    """
    Event for entities that changed.
    """

    def __init__(self, entity_props: Dict[str, Any], changed_props: List[str], sim_time: int = None):
        """
        Event for new entities that changed an attribute property.
        :param entity_props: The entity properties (using the Scarab props).
        :param changed_props: The entity properties that changed.
        :param sim_time: The sim time for the event.
        """
        super().__init__(ScarabEventType.ENTITY_CHANGED, sim_time)
        self.entity = SimpleNamespace(**entity_props)
        self.changed_properties = changed_props


class EntityDestroyedEvent(Event):
    """
    Event for entities that got destroyed.
    """

    def __init__(self, entity_props: Dict[str, Any], sim_time: int = None):
        """
        Event for entities that were destroyed.
        :param entity_props: The entity properties (using the Scarab props).
        :param sim_time: The sim time for the event.
        """
        super().__init__(ScarabEventType.ENTITY_DESTROYED, sim_time)
        self.entity = SimpleNamespace(**entity_props)


class SimulationStartEvent(Event):
    """
    Event that indicates the simulation is starting for the first time.
    """

    def __init__(self, sim_time: int):
        """
        Event for new entities that were just created.
        :param sim_time: The sim time for the event.
        """
        super().__init__(ScarabEventType.SIMULATION_START, sim_time)


class SimulationPauseEvent(Event):
    """
    Event that indicates the simulation is pausing.
    """

    def __init__(self, sim_time: int):
        """
        Event for new entities that were just created.
        :param sim_time: The sim time for the event.
        """
        super().__init__(ScarabEventType.SIMULATION_PAUSE, sim_time)


class SimulationResumeEvent(Event):
    """
    Event that indicates the simulation is resuming from a paused state.
    """

    def __init__(self, sim_time: int = None):
        """
        Event for new entities that were just created.
        :param sim_time: The current sim time.
        """
        super().__init__(ScarabEventType.SIMULATION_RESUME, sim_time)


class SimulationShutdownEvent(Event):
    """
    Event that indicates the simulation is shutting down.  It allows for the cleanup of resources.
    """

    def __init__(self, sim_time: int = None):
        """
        Event for new entities that were just created.
        :param sim_time: The current sim time.
        """
        super().__init__(ScarabEventType.SIMULATION_SHUTDOWN, sim_time)


class TimeUpdatedEvent(Event):
    """
    Event for time updates.
    """

    def __init__(self, sim_time: int, previous_time: int = None):
        """
        Event for new entities that were just created.
        :param sim_time: Time the event was sent.
        :param previous_time: The previous time.  If not provided, then use time-1.
        """
        super().__init__(ScarabEventType.TIME_UPDATED, sim_time)
        if previous_time is not None:
            self.previous_time = previous_time
        else:
            self.previous_time = sim_time - 1

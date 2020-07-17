"""
Copyright (C) 2019 William D. Back

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

This module contains support for testing.
"""

from scarab.entities import Entity
from scarab.events import EntityChangedEvent, EntityCreatedEvent, EntityDestroyedEvent, Event
from scarab.events import NewTimeEvent, SimulationShutdownEvent, SimulationStartupEvent
from scarab.util import get_uuid
from scarab.simulation import EventMediator


class EntityTestWrapper:
    """
    Wraps an entity for ease of testing.  You can wrap an entity and then send events to it directly.  The advantage
    to wrapping is that the entity will be invoked the same way as it would in the simulation, rather than calling the
    handler methods directly.
    """

    class WrapperSimulation:
        """Simple wrapper that will capture events sent back to the simulation for testing."""

        def __init__(self):
            """Creates a new sim for testing."""
            self.queued_events = []
            self.queued_messages = []

        def queue_event(self, event) -> None:
            """
            Adds an event to the event queue.
            :param Event event:
            """
            self.queued_events.append(event)

        def queue_message(self, message) -> None:
            """
            Adds an message to the message queue.
            :param Message message:
            """
            self.queued_messages.append(message)

    # Using slots to distinguish between the wrapper and the entity.  This allows pass through to directly set and
    # get the entity attributes.
    __slots__ = ['entity', 'simulation', '__mediator']

    def __init__(self, entity):
        """
        Creates a new entity wrapper for testing.
        :param Entity entity: The entity to be tested.
        """
        self.entity = entity
        self.entity.guid = get_uuid()

        self.__mediator = EventMediator()  # used to route events.
        self.__mediator.register_entity(entity=entity)

        entity._simulation = EntityTestWrapper.WrapperSimulation()
        self.simulation = entity._simulation  # make easier to access for testing.

    def __setattr__(self, key, value) -> None:
        """
        Sets the attribute on the wrapped entity.
        :param str key:
        :param Any value:
        :return: None
        """
        if key in EntityTestWrapper.__dict__:  # Need a special test for slots vs. regular attributes.
            EntityTestWrapper.__dict__[key].__set__(self, value)
        else:
            self.entity.__dict__[key] = value

    def __getattr__(self, key):
        """
        Sets the attribute on the wrapped entity.
        :param str key: The key for the attribute to return.
        :return: The value for the attribute
        """
        if key in EntityTestWrapper.__dict__:
            return EntityTestWrapper.__dict__[key].__get__(self)
        else:
            return self.entity.__dict__[key]

    def send_event(self, event) -> None:
        """
        Sends a generic event to the entity.
        :param Event event: The event to send.
        """
        self.__mediator.send_event(event=event)

    def send_entity_changed_event(self, entity_name, properties=None) -> None:
        """
        Sends an entity changed event.
        :param str entity_name: The name of the entity that changed.
        :param dict properties: The properties for the entity.  Assumes that all have changed.
        :return: None
        """
        changed_properties = list(properties.keys()) if properties else None
        ent = Entity(name=entity_name)
        if properties:
            for k, v in properties.items():
                ent.__setattr__(k, v)
        self.send_event(EntityChangedEvent(ent, changed_properties=changed_properties))

    def send_entity_created_event(self, entity_name, properties=None) -> None:
        """
        Sends an entity created event.
        :param str entity_name: The name of the entity that changed.
        :param dict properties: The list of properties that changed.
        :return: None
        """
        entity = Entity(name=entity_name)
        if properties:
            for k, v in properties.items():
                entity.__setattr__(key=k, value=v)
        self.send_event(EntityCreatedEvent(entity=entity))

    def send_entity_destroyed_event(self, entity_name, entity_guid, properties=None) -> None:
        """
        Sends an entity destroyed event.
        :param str entity_name: Name of the entity.
        :param Any entity_guid: GUID for the entity.  Note that this should be the same if the
        :param dict properties: Needed properties for the entity.
        entity was originally assigned with create to make sure the reference matches.
        :return: None
        """
        entity = Entity(name=entity_name, guid=entity_guid)
        if properties:
            for k, v in properties.items():
                entity.__setattr__(key=k, value=v)
        self.send_event(EntityDestroyedEvent(entity=entity))

    def send_new_time(self, new_time) -> None:
        """
        Sends a new time event to the entity.  The old time will be one less than the new time.
        :param int new_time: The new time to send.
        :return: None
        """
        self.send_event(NewTimeEvent(previous_time=(new_time - 1), new_time=new_time))

    def send_simulation_shutdown(self) -> None:
        """
        Sends a simulation shutdown event.
        :return: None
        """
        self.send_event(SimulationShutdownEvent())

    def send_simulation_startup(self) -> None:
        """
        Sends a simulation startup event.
        :return: None
        """
        self.send_event(SimulationStartupEvent())

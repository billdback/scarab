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

This module contains base classes for Events and Commands as well as common Events and Commands used in the framework.
"""

from functools import wraps
import inspect

from scarab.events import *


class EventInterest:
    """
    Contains events that a handler container is interested in.
    """

    def __init__(self):
        """
        Creates a new event interest container.
        """
        self.named_events = []  # list of named events that an entity is interested in.
        self.entity_created_events = []  # list of entities who's creation an entity would be interested in.
        self.entity_changed_events = []  # list of entities who's changes an entity would be interested in.
        self.entity_destroyed_events = []  # list of entities who's destruction an entity would be interested in.


class EventHandlerContainer:
    """
    Holds and manages event handlers for classes.
    """

    def __init__(self):
        """
        Creates a new container for event handlers.
        """
        # contains event handlers for all events except entity events.  Key is the name and value is the handler.
        self._named_event_handlers = {}

        # contains event handlers for entity related events.  Entity event handlers are specific for types of entities.
        # key is the name of entity, not the handler.  Handler types are implied by the actual container.
        self._created_entity_event_handlers = {}
        self._changed_entity_event_handlers = {}
        self._destroyed_entity_event_handlers = {}

        self._event_interest = EventInterest()  # used to return the events this entity is interested in.

    def add_event_handler(self, event_name, handler):
        """
        Adds a handler for the given event.
        :param event_name: Name of the event to handle.
        :type event_name: str
        :param handler: Handler for an event.
        :return: Nothing
        """
        event_handlers = self._named_event_handlers.get(event_name, None)
        if not event_handlers:
            event_handlers = []

        event_handlers.append(handler)
        self._named_event_handlers[event_name] = event_handlers

        self._event_interest.named_events.append(event_name)

    def add_entity_created_event_handler(self, entity_name, handler):
        """
        Adds a handler for the creation of a given type of entity.
        :param entity_name: Name of the entity type to handle.
        :type entity_name: str
        :param handler: Handler for an entity creation.
        :return: Nothing
        """
        event_handlers = self._created_entity_event_handlers.get(entity_name, None)
        if not event_handlers:
            event_handlers = []

        event_handlers.append(handler)
        self._created_entity_event_handlers[entity_name] = event_handlers

        self._event_interest.entity_created_events.append(entity_name)

    def add_entity_changed_event_handler(self, entity_name, handler):
        """
        Adds a handler for the change of a given entity type.
        :param entity_name: Name of the entity type to handle.
        :type entity_name: str
        :param handler: Handler for an entity change.
        :return: Nothing
        """
        event_handlers = self._changed_entity_event_handlers.get(entity_name, None)
        if not event_handlers:
            event_handlers = []

        event_handlers.append(handler)
        self._changed_entity_event_handlers[entity_name] = event_handlers

        self._event_interest.entity_changed_events.append(entity_name)

    def add_entity_destroyed_event_handler(self, entity_name, handler):
        """
        Adds a handler for the destruction of a given entity type.
        :param entity_name: Name of the entity type to handle.
        :type entity_name: str
        :param handler: Handler for an entity destruction.
        :return: Nothing
        """
        event_handlers = self._destroyed_entity_event_handlers.get(entity_name, None)
        if not event_handlers:
            event_handlers = []

        event_handlers.append(handler)
        self._destroyed_entity_event_handlers[entity_name] = event_handlers

        self._event_interest.entity_destroyed_events.append(entity_name)

    def get_event_handlers(self, event_type):
        """
        Returns the list of handlers for a given type.
        :param event_type: The type of event to get the list for.
        :type event_type: str
        :return: A list of event handlers for a given event type.
        :rtype:  list | None
        """
        # If the type is an entity type, it probably won't be found.
        return self._named_event_handlers.get(event_type, None)

    def get_entity_created_handlers(self, entity_name):
        """
        Returns the list of handlers for a given entity type.
        :param entity_name: The type of entity to get the list for.
        :type entity_name: str
        :return: A list of event handlers for a given entity type.
        :rtype:  list | None
        """
        return self._created_entity_event_handlers.get(entity_name, None)

    def get_entity_changed_handlers(self, entity_name):
        """
        Returns the list of handlers for a given entity type.
        :param entity_name: The type of entity to get the list for.
        :type entity_name: str
        :return: A list of event handlers for a given entity type.
        :rtype:  list | None
        """
        return self._changed_entity_event_handlers.get(entity_name, None)

    def get_entity_destroyed_handlers(self, entity_name):
        """
        Returns the list of handlers for a given entity type.
        :param entity_name: The type of entity to get the list for.
        :type entity_name: str
        :return: A list of event handlers for a given entity type.
        :rtype:  list | None
        """
        return self._destroyed_entity_event_handlers.get(entity_name, None)

    def get_event_interest(self):
        """
        Returns the events that this container is interested in.
        :return:  The events that this container is interested in.
        :rtype: EventInterest
        """
        return self._event_interest


class Entity(PropertyWrapper):
    """
    Creates a base entity class for use by the simulation.  All simulation entities should extend this class.
    Using this base class eliminates the need to code for specific details of the simulation.
    """

    # holds the event handlers at the class level and calls when invoked in the program.
    _event_handlers = {}  # EventHandlerContainer()

    @classmethod
    def get_handler_container(cls, handler):
        handler_cls = handler.__qualname__.split(".")[0]  # assumes not in a subclass.
        handlers = Entity._event_handlers.get(handler_cls, None)
        if not handlers:
            handlers = EventHandlerContainer()
            Entity._event_handlers[handler_cls] = handlers

        return handlers

    def __init__(self, name, guid=None):
        """
        Creates a new entity.
        :param name: The name of the entity.  The name is used to connect to other entities that are intereted in this
        type of entity.
        :type name: str
        :param guid: Unique id for the entity
        :type guid: str
        """
        assert name

        self.name = name
        self.guid = guid
        self._simulation = None  # set by the simulation after adding.

        super().__init__()

    # def handle_event(self, event, *args, **kwargs):
    def handle_event(self, event):
        """
        Calls the event handler for the event with the given name.
        # TODO make this more flexible to handle patterns for handlers.
        :param event: Event to handle.
        :type event: Event
        :return:  Whatever is returned by the handler.
        """
        assert event

        # TODO this is slow.  May want to copy over during init.
        event_handlers_for_class = Entity._event_handlers.get(type(self).__name__, None)
        if not event_handlers_for_class:
            raise KeyError(f"No handlers implemented for class {type(self).__name__}")

        # Add the handling for special event types.
        if event.name == ENTITY_CREATED_EVENT:
            event_handlers = event_handlers_for_class.get_entity_created_handlers(entity_name=event.entity.name)
            if event_handlers:
                for eh in event_handlers:
                    eh(self, event.entity)
        elif event.name == ENTITY_CHANGED_EVENT:
            event_handlers = event_handlers_for_class.get_entity_changed_handlers(entity_name=event.entity.name)
            if event_handlers:
                for eh in event_handlers:
                    eh(self, event.entity, event.changed_properties)
        elif event.name == ENTITY_DESTROYED_EVENT:
            event_handlers = event_handlers_for_class.get_entity_destroyed_handlers(entity_name=event.entity.name)
            if event_handlers:
                for eh in event_handlers:
                    eh(self, event.entity)
        elif event.name == NEW_TIME_EVENT:
            event_handlers = event_handlers_for_class.get_event_handlers(event.name)
            if event_handlers:
                for eh in event_handlers:
                    eh(self, event.previous_time, event.new_time)
        else:
            event_handlers = event_handlers_for_class.get_event_handlers(event.name)
            if event_handlers:
                for eh in event_handlers:
                    eh(self, event)

        # Handle error scenarios where the event was delivered, but there are no handlers.
        if not event_handlers:
            if event.name in (ENTITY_CREATED_EVENT, ENTITY_CHANGED_EVENT, ENTITY_DESTROYED_EVENT):
                raise KeyError(f"No handler of type {event.name} for entity {event.entity.name} "
                               f"implemented for class {type(self).__name__}")
            else:
                raise KeyError(f"No handler for event {event.name} implemented for class {type(self).__name__}")

    def get_properties(self):
        """
        Returns the list of properties as a dictionary.
        :return: The properties for the entity.
        :rtype: dict
        """
        attrs = {}
        for (k, v) in self._complex_properties.items():
            attrs[k] = v

    def get_event_interest(self):
        """
        Returns the events this entity is interested in.
        :return: The events this entity is interested in.
        :rtype: EventInterest
        """
        return self.get_handler_container(self.__class__).get_event_interest()

# Decorators for entities to tie into the simulation framework. -------------------------------------------------------


def event_handler(event_name):
    """
    Handles events based on the event name.
    Expected signature: function_name (self, event)
    :param event_name:  Name of the event to handle.
    :return: Decorator function to call for a given event.
    """
    def decorator(handler):
        assert handler and len(inspect.signature(handler).parameters) == 2, "Incorrect number of handler arguments"
        Entity.get_handler_container(handler=handler).add_event_handler(event_name=event_name, handler=handler)

        @wraps(handler)
        def f(self, *args, **kwargs):
            result = handler(self, *args, **kwargs)
            return result
        return f
    return decorator


def entity_created_event_handler(entity_name):
    """
    Handles events for the creation of entities with a given type.
    Expected signature: function_name (self, entity)
    :param entity_name:  Type of the entity that was created.
    :return: Decorator function to call for the event.
    """
    def decorator(handler):
        assert handler and len(inspect.signature(handler).parameters) == 2, "Incorrect number of handler arguments"
        Entity.get_handler_container(handler=handler).\
            add_entity_created_event_handler(entity_name=entity_name, handler=handler)

        @wraps(handler)
        def f(self, *args, **kwargs):
            result = handler(self, *args, **kwargs)
            return result
        return f
    return decorator


def entity_changed_event_handler(entity_name):
    """
    Handles events for the changes of entities with a given type.
    Expected signature: function_name (self, entity, changed_properties)
    :param entity_name:  Type of the entity that was changed.
    :return: Decorator function to call for the event.
    """
    def decorator(handler):
        assert handler and len(inspect.signature(handler).parameters) == 3, "Incorrect number of handler arguments"
        Entity.get_handler_container(handler=handler).\
            add_entity_changed_event_handler(entity_name=entity_name, handler=handler)

        @wraps(handler)
        def f(self, *args, **kwargs):
            result = handler(self, *args, **kwargs)
            return result
        return f
    return decorator


def entity_destroyed_event_handler(entity_name):
    """
    Handles events for the destruction of entities with a given type.
    Expected signature: function_name (self, entity)
    :param entity_name:  Type of the entity that was destroyed.
    :return: Decorator function to call for the event.
    """

    def decorator(handler):
        assert handler and len(inspect.signature(handler).parameters) == 2, "Incorrect number of handler arguments"
        Entity.get_handler_container(handler=handler).\
            add_entity_destroyed_event_handler(entity_name=entity_name, handler=handler)

        @wraps(handler)
        def f(self, *args, **kwargs):
            result = handler(self, *args, **kwargs)
            return result
        return f
    return decorator


def simulation_shutdown_handler(handler):
    """
    Handles simulation shutdown.
    Expected signature: function_name (self, event)
    :param handler:  Method to call for simulation shutdown.
    :return: Decorator function to call for a simulation shutdown.
    """
    assert handler and len(inspect.signature(handler).parameters) == 2, "Incorrect number of handler arguments"
    Entity.get_handler_container(handler=handler).add_event_handler(SIMULATION_SHUTDOWN, handler)

    @wraps(handler)
    def f(self, *args, **kwargs):
        result = handler(self, *args, **kwargs)
        return result
    return f


def time_update_event_handler(handler):
    """
    Handles time update events.
    Expected signature: function_name (self, previous_time, new_time)
    :param handler:  Method to call for time updates.
    :return: Decorator function to call for a time update.
    """
    assert handler and len(inspect.signature(handler).parameters) == 3, "Incorrect number of handler arguments"
    Entity.get_handler_container(handler=handler).add_event_handler(NEW_TIME_EVENT, handler)

    @wraps(handler)
    def f(self, *args, **kwargs):
        result = handler(self, *args, **kwargs)
        return result
    return f

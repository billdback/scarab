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


class Property:
    """
    This class represents a single property that can be validated.
    """

    def __init__(self, name, default_value=None, validator=None):
        """
        Creates a new property.
        :param name: The name of the property (required).
        :type name: str
        :param default_value: The default value of the property.
        :type default_value: Object
        :param validator: A function to validate the value.  This function should return a bool.
        :type validator: callable[]: bool
        """
        self.name = name
        self.default_value = default_value
        self.value = default_value
        self._validator = validator

    def set_value(self, value):
        """
        Sets the value on the property, calling the validator if there is one.
        :param value: The value to set.
        :type value: Object
        :return: The value that was set.
        :rtype: Object
        """
        if self._validator and not self._validator(value):
            raise ValueError(f"{value} is an invalid value for {self.name}")

        self.value = value
        return self.value

    def get_value(self):
        """
        Returns the current value.
        :return: The current value.
        :rtype: Object
        """
        return self.value


class PropertyWrapper:
    """
    This class wraps the property list and allows calls to get and set the properties using traditional syntax,
    e.g. obj.property.  It supports both direct properties that are part of the class as well as ones that are
    added dynamically.
    """

    def __init__(self, **kwargs):
        """
        Creates a new instance of an property wrapper.
        :param kwargs Keyword arguments that are added as properties.
        """
        self._complex_properties = {}

        for k in kwargs:
            self.__setattr__(k, kwargs[k])

    def __setattr__(self, key, value):
        """
        Sets the value of an property.  It will first check the object's __dict__ and if present, set the value
        there.  If not, it will get added to the property list.
        :param key: The name of the property.
        :param value: The value of the property.
        :return:  Nothing
        """
        # set to a bad value.
        if isinstance(value, Property):
            self._complex_properties[key] = value
        else:
            # see if the value already exists and is an Property.  If so, just call set_value on it.
            if ("_complex_properties" in self.__dict__) and (key in self._complex_properties):
                self._complex_properties[key].set_value(value)
            else:
                super().__setattr__(key, value)

    def __getattr__(self, key):
        """
        Gets the value of an property.  It will first check the object's __dict__ and if present, return the value
        there.  If not, it will return from the property list.
        :param key: The name of the property.
        :return:  The value of the property.
        :raises AttributeError: Raised if there is no property with the given name.
        """
        if key != "_complex_properties" and key in self._complex_properties:
            attr = self._complex_properties[key]
        elif key in self.__dict__:
            attr = self.__dict__[key]
        elif key in super.__dict__:
            attr = super.__dict__[key]
        else:
            raise AttributeError(f"Unknown property {key} for class {self}")

        if isinstance(attr, Property):
            return attr.value

        return attr


class Event(PropertyWrapper):
    """
    Class that represents a basic event that can be sent to entities in the simulation.
    """

    def __init__(self, name, sim_id=None, created_by=None, sim_time=None, **kwargs):
        """
        Creates a new event to be sent to other entities.
        :param name: Name or logical type of the event.
        :type name: str
        :param sim_id: Unique ID for the event.
        :type sim_id: str
        :param created_by: Unique ID for the thing that created the event.
        :type created_by: str
        :param sim_time: Simulation time the event was created.
        :type sim_time: int
        :param kwargs: Keyword arguments that are added as parameters.
        """
        assert name

        self.name = name
        self.sim_id = sim_id
        self.sim_time = sim_time
        self.created_by = created_by

        PropertyWrapper.__init__(self, **kwargs)

    def is_complete(self):
        """
        Returns True if all of the values needed to send in the simulation have been populated.  These may not be
        populated by default.
        :return: True if complete, False otherwise.
        """
        return self.name is not None and self.sim_id is not None and self.created_by is not None

# Standard events for entity activities. ----------------------------------------------------------------------------


# Patterns for groups of events.
SIMULATION_EVENTS = "scarab.simulation.*"
ENTITY_EVENTS = "scarab.entity.*"
TIME_EVENTS = "scarab.time.*"

# Specific event names.
ENTITY_CREATED_EVENT = "scarab.entity.created"
ENTITY_DESTROYED_EVENT = "scarab.entity.destroyed"
ENTITY_CHANGED_EVENT = "scarab.entity.changed"
SIMULATION_SHUTDOWN = "scarab.simulation.simulation_shutdown"
NEW_TIME_EVENT = "scarab.time.new"


class EntityCreatedEvent(Event):
    """Creates an event to indicate that an entity was created."""

    def __init__(self, entity):
        """
        Indicates that an entity was created.
        :param entity: The entity that was created.
        :type entity: RemoteEntity
        """
        # Make sure some value has been provided.
        assert entity

        self.entity = entity
        Event.__init__(self, name=ENTITY_CREATED_EVENT)


class EntityDestroyedEvent(Event):
    """Creates an event to indicate that an entity was destroyed."""

    def __init__(self, entity):
        """
        Indicates that an entity was destroyed.
        :param entity: The entity that was created.
        :type entity: RemoteEntity
        """
        # Make sure some value has been provided.
        assert entity

        self.entity = entity
        Event.__init__(self, name=ENTITY_DESTROYED_EVENT)


class EntityChangedEvent(Event):
    """Creates an event to indicate that an entity was changed."""

    def __init__(self, entity, changed_properties):
        """
        Indicates that an entity was destroyed.
        :param entity: The entity that was created.
        :type entity: RemoteEntity
        :param changed_properties: List of properties that were changed.
        :type changed_properties: list of str
        """
        # Make sure some value has been provided.
        assert entity
        assert changed_properties

        self.entity = entity
        self.changed_properties = changed_properties
        Event.__init__(self, name=ENTITY_CHANGED_EVENT)


class SimulationShutdownEvent(Event):
    """Creates an event to indicate that the simulation is shutting down.  Allows cleanup of resources."""

    def __init__(self):
        """
        Indicates the simulation is shutting down.
        """
        Event.__init__(self, name=SIMULATION_SHUTDOWN)


class NewTimeEvent(Event):
    """Creates an event to indicate that time was updated."""

    def __init__(self, previous_time, new_time):
        """
        Indicates that time changed.
        :param previous_time: The new time in the simulation.
        :type previous_time: int
        :param new_time: The new time in the simulation.
        :type new_time: int
        """
        # Make sure some value has been provided.
        assert previous_time is not None, f"Unexpected previous_time of {previous_time}"
        assert new_time is not None, f"Unexpected new_time of {new_time}"

        self.previous_time = previous_time
        self.new_time = new_time
        Event.__init__(self, name=NEW_TIME_EVENT, sim_time=new_time)

# Commands. ----------------------------------------------------------------------------


class Message(Event):
    """
    Commands are events targeted at a specific simulation object.
    """

    def __init__(self, name, target_guid, sim_id=None, created_by=None, sim_time=None):
        """
        Creates a new command for a given target.
        :param name: Name of the command.
        :type name: str
        :param target_guid: The ID for the target to receive the command.
        :type target_guid: str
        :param sim_id: Unique ID for the event.
        :type sim_id: str
        :param created_by: Unique ID for the thing that created the event.
        :type created_by: str
        :param sim_time: Simulation time the event was created.
        :type sim_time: int
        """
        assert name
        assert target_guid

        self.target_guid = target_guid

        Event.__init__(self, name=name, sim_id=sim_id, created_by=created_by, sim_time=sim_time)

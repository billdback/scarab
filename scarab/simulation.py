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

This module contains the classes necessary for a simulation.
TODO None of this is set up to be thread safe.
TODO There may be opportunities for performance improvement in many of these classes.
"""

from copy import deepcopy
import re
import sys

from scarab.util import get_uuid
from scarab.events import *
from scarab.entities import Entity


class TimeEventQueue:
    """
    Class to allow entities to be added with a time and then returned in time order and order added.

    If an event is added with no sim time set, it will get added to occur at the next time.  If an event is added
    with a sim time that is before the next time, an Error is raised.
    """

    def __init__(self):
        """
        Creates a new TimeEventQueue
        """
        self._event_lists = {}  # maps sim time to list of events
        self._current_event_list = None  # list currently getting events from.
        self._current_time = 0  # The time for current events.  Others must be in the future.

    def add(self, event):
        """
        Adds a new event in the proper location based on simulation time to send.
        :param event: The event to add to the queue.
        :type event: Event
        :return: Nothing
        """
        assert event

        # set to next time if none provided.
        if not event.sim_time:
            event.sim_time = self._current_time + 1
        elif event.sim_time <= self._current_time:  # make sure not in the past.
            raise ValueError(f"Attempting to add an event with sim_time {event.sim_time} to a "
                             f"queue with current time {self._current_time}")

        if event.sim_time not in self._event_lists:
            self._event_lists[event.sim_time] = []
        self._event_lists[event.sim_time].append(event)

    def __len__(self):
        """
        Returns the number of events in the queue.
        :return: The number of events in the queue.
        :rtype: int
        """
        the_len = 0
        for v in self._event_lists.values():
            the_len += len(v)

        return the_len

    def is_empty(self):
        """
        Returns true if there are no events in the queue.
        :return: True if there are no events in the queue.
        :rtype: bool
        """
        return len(self._event_lists.keys()) == 0 and not self._current_event_list

    def next_time(self):
        """
        Returns the next time if no more events were to be called.  I.e. the time of the next event.
        :return: The time of the next event in the queue or None if the list is empty.
        """
        if self._current_event_list:
            return self._current_time
        elif self.is_empty():
            return None

        return sorted(self._event_lists.keys())[0]

    def advance(self, increment=1):
        """
        Advances the time to increase the minimum time.
        :param increment: The increment to advance by (must be >= 1)
        :type increment: int
        :return: The new current time.
        :rtype: int
        """
        assert increment > 0, f"Expected positive increment, but got {increment}"

        self._current_time += increment
        return self._current_time

    def next(self):
        """
        Returns the next event in the queue.
        :return:
        """
        if self.is_empty():
            return None

        if not self._current_event_list:  # empty list or not set.  Must be more to get here.
            self._current_time = self.next_time()
            self._current_event_list = self._event_lists.pop(self._current_time)

        # getting here means there is an event to return.
        return self._current_event_list.pop(0)


class PriorityEventQueue:
    """
    Creates a list that supports priorities of events.  This means that for a given time, the higher priority events
    are sent before the lower priority events.
    """
    def __init__(self, priorities=None):
        """
        Creates a new priority event queue.
        :param priorities: The order that events should be sent for a given time.  Match on patterns.
        :type priorities: list of str
        """
        self._queues = {}
        self._priorities = []

        if priorities:
            for p in priorities:
                self._priorities.append(re.compile(p))
        self._priorities.append(re.compile(".*"))

        for p in self._priorities:
            self._queues[p] = TimeEventQueue()

    def __len__(self):
        """
        Returns the total number of events in the list.
        :return:the total number of events in the list.
        :rtype: int
        """
        the_len = 0
        for teq in self._queues.values():
            the_len += len(teq)
        return the_len

    def is_empty(self):
        """
        Returns True if the queue is empty.
        :return: True if the queue is empty.
        :rtype: bool
        """
        return len(self) == 0

    def next_time(self):
        """
        Returns the time of the next event across all queues.  This is the minimum.
        :return: The time of the next event or None.
        :rtype: int | None
        """
        next_time = None
        for qv in self._queues.values():
            nt = qv.next_time()
            if not next_time:
                next_time = nt
            elif nt:
                next_time = min(next_time, nt)

        return next_time

    def add(self, event):
        """
        Adds an event to the queue based on priority and time.
        :param event: The event to add to the queue.
        :return: Nothing
        """
        for p in self._priorities:
            if p.fullmatch(event.name):
                q = self._queues[p]
                q.add(event)
                break

    def advance(self, increment=1):
        """
        Advances the time to increase the minimum time.
        :param increment: The increment to advance by (must be >= 1)
        :type increment: int
        :return: The new current time.
        :rtype: int
        """
        assert increment > 0, f"Expected positive increment, but got {increment}"

        min_time = sys.maxsize
        for q in self._queues.values():
            t = q.advance(increment)
            min_time = min(min_time, t)

        return min_time

    def next(self):
        """
        Returns the next event in the queue.
        :return: The next event in the queue or None if no events left.
        :rtype: Event | None
        """
        # first, make sure the current time and next time are set based on the queues.
        next_time = self.next_time()
        for p in self._priorities:
            q = self._queues[p]
            if not q.is_empty() and q.next_time() == next_time:
                return q.next()

        return None


class EventMediator:
    """
    Mediates the event interactions between entities.  Entities (or other objects) are registered with handlers for
    an event and then events are sent to the mediator.  The mediator then sends to all registered handlers.
    """

    def __init__(self):
        """
        Creates a new event mediator for distributing events.
        """
        self._named_event_interest = {}  # mapping of event names to entities.

        # maps the different types of interest that an entity has in other entities.
        self._entity_created_interest = {}
        self._entity_changed_interest = {}
        self._entity_destroyed_interest = {}

    def register_entity(self, entity):
        """
        Adds an entity to receive future events.
        :param entity: The entity interested.
        :type entity: Entity
        :return: None
        """
        interest = entity.get_event_interest()

        for event_name in interest.named_events:
            entity_list = self._named_event_interest.get(event_name, None)
            if not entity_list:
                entity_list = []
                self._named_event_interest[event_name] = entity_list
            entity_list.append(entity)

        for entity_name in interest.entity_created_events:
            entity_list = self._entity_created_interest.get(entity_name, None)
            if not entity_list:
                entity_list = []
                self._entity_created_interest[entity_name] = entity_list
            entity_list.append(entity)

        for entity_name in interest.entity_changed_events:
            entity_list = self._entity_changed_interest.get(entity_name, None)
            if not entity_list:
                entity_list = []
                self._entity_changed_interest[entity_name] = entity_list
            entity_list.append(entity)

        for entity_name in interest.entity_destroyed_events:
            entity_list = self._entity_destroyed_interest.get(entity_name, None)
            if not entity_list:
                entity_list = []
                self._entity_destroyed_interest[entity_name] = entity_list
            entity_list.append(entity)

        entity.simulation = self

    def deregister_entity(self, entity):
        """
        Removes all of the registrations for a given entity.
        TODO Create a faster way to do this.
        :param entity: The entity to remove.
        :type entity: Entity
        :return: None
        """
        interest = entity.get_event_interest()

        for event_name in interest.named_events:
            entity_list = self._named_event_interest.get(event_name, None)
            if entity_list:  # shouldn't happen, but just in case.
                entity_list.remove(entity)

        for entity_name in interest.entity_created_events:
            entity_list = self._entity_created_interest.get(entity_name, None)
            if entity_list:  # shouldn't happen, but just in case.
                entity_list.remove(entity)

        for entity_name in interest.entity_changed_events:
            entity_list = self._entity_changed_interest.get(entity_name, None)
            if entity_list:  # shouldn't happen, but just in case.
                entity_list.remove(entity)

        for entity_name in interest.entity_destroyed_events:
            entity_list = self._entity_destroyed_interest.get(entity_name, None)
            if entity_list:  # shouldn't happen, but just in case.
                entity_list.remove(entity)

        entity.simulation = None

    def send_event(self, event):
        """
        Handles the event by sending to all of the entities that registered it.
        :param event:  The event to handle.
        :type event: Event
        :return: None
        """
        if event.name == ENTITY_CREATED_EVENT:
            entity_list = self._entity_created_interest.get(event.entity_name, None)
            if entity_list:
                for e in entity_list:
                    e.handle_event(event=event)
        elif event.name == ENTITY_CHANGED_EVENT:
            entity_list = self._entity_changed_interest.get(event.entity_name, None)
            if entity_list:
                for e in entity_list:
                    e.handle_event(event=event)
        elif event.name == ENTITY_DESTROYED_EVENT:
            entity_list = self._entity_destroyed_interest.get(event.entity_name, None)
            if entity_list:
                for e in entity_list:
                    e.handle_event(event=event)
        else:
            entity_list = self._named_event_interest.get(event.name, None)
            if entity_list:
                for e in entity_list:
                    e.handle_event(event=event)


class EntityState:
    """
    Records the entity state as a set of key/value pairs and can compare to another entity for differences.
    """

    def __init__(self, entity):
        """
        Creates a new entity state object.
        :param entity: The entity to capture state from.
        :type entity: Entity
        """
        self.__entity_guid = entity.guid  # used to make sure changes are for the same entity.
        self.__state = self.__get_state_from_entity(entity=entity)

    def compare_and_update(self, entity):
        """
        Compares state to an entity, update state to the new state, and returns a dictionary of the changes.
        This code handles scenarios where properties are added or removed.  It's not envisioned that this will be
        a common scenario.
        :param entity:  The entity being compared to.
        :type entity: Entity
        :return: A dictionary of the changes.
        :rtype: dict
        """
        assert (entity.guid == self.__entity_guid)
        new_state = self.__get_state_from_entity(entity=entity)
        differences = {}

        # Any new properties will automatically get added as changed.
        new_properties = list(set(new_state.keys()) - set(self.__state.keys()))

        for prop in new_properties:
            differences[prop] = deepcopy(prop)  # copy in case of list or other mutable object.

        # Any old properties that no longer exist will get set to None.
        # It won't be obvious to the user if that means they are gone or just set to None.
        lost_properties = list(set(self.__state.keys()) - set(new_state.keys()))
        for prop in lost_properties:
            differences[prop] = None

        # Now check for the remaining properties.  These will be the ones in the new state that are not new props.
        for prop in new_state.keys():
            if prop not in new_properties:
                if new_state[prop] != self.__state[prop]:
                    differences[prop] = new_state[prop]

        self.__state = new_state  # set the new state for future comparisons.
        return differences

    @staticmethod
    def __get_state_from_entity(entity):
        """
        Returns the state from an entity.
        :param entity:  The entity to get state from.
        :type entity: Entity
        :return: A dictionary of the changes.
        :rtype: dict
        """
        state = {}
        for prop in entity.__dict__:
            if prop and not prop.startswith("_"):
                state[prop] = deepcopy(entity.__dict__[prop])

        return state


class Simulation:
    """
    Class that represents a simulation with entities.  It manages the time and lifecycle of entities, and routes
    events to the interested enties and other simulation objects.
    """

    def __init__(self, time_stepped=False, event_priorities=None):
        """
        Creates a new simulation.
        :param time_stepped: Indicates if the simulation is time stepped (i.e. one increment at a time) or not.  If
        False, then the next time sent out is the next time in the queue.
        :type time_stepped: bool
        :param event_priorities: Priorities of simulation events.  These fall *after* the standard events.
        :type event_priorities: list of str
        """
        self.time_stepped = time_stepped
        self._entities = {}        # entities in the simulation.
        self._previous_state = {}  # records the previous state of entities for comparison if they changed.
        all_event_priorities = [SIMULATION_EVENTS, ENTITY_EVENTS, TIME_EVENTS]
        if event_priorities:
            all_event_priorities.extend(event_priorities)

        self._event_queue = PriorityEventQueue(priorities=all_event_priorities)
        self._event_mediator = EventMediator()

        self._previous_time = -1

        self.license = [
            "Copyright (C) 2019 William D. Back",
            "",
            "This program is free software: you can redistribute it and/or modify",
            "it under the terms of the GNU General Public License as published by",
            "the Free Software Foundation, either version 3 of the License, or",
            "(at your option) any later version.",
            "",
            "This program is distributed in the hope that it will be useful,",
            "but WITHOUT ANY WARRANTY; without even the implied warranty of",
            "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the",
            "GNU General Public License for more details.",
            "",
            "You should have received a copy of the GNU General Public License",
            "along with this program.  If not, see <https://www.gnu.org/licenses/>."
        ]

    def print_license(self):
        """
        Prints the license for Scarab.
        """
        for line in self.license:
            print(line)

    def number_entities(self):
        """
        Returns the number of entities currently in the simulation.
        :return: The number of entities currently in the simulation.
        :rtype: int
        """
        return len(self._entities)

    def number_queued_events(self):
        """
        Return the number of queued events.
        :return: The number of queued events.
        """
        return len(self._event_queue)

    def next_time(self):
        """
        Returns the next simulation time.  This can change as events get added.
        :return: The next simulation time.
        """
        return self._event_queue.next_time()

    def queue_event(self, event):
        """
        Queues an event for sending.
        :param event: An event to send.
        :type event: Event
        :return: Nothing
        """
        if not event.sim_time or event.sim_time <= self._previous_time:
            event.sim_time = self._previous_time + 1  # always add in the future.
        self._event_queue.add(event=event)

    def add_entity(self, entity):
        """
        Adds a new entity to the simulation.  Note that this is not thread safe.
        :param entity: The entity to add.
        :type entity: Entity
        :return: Nothing
        """
        # Add the entity to the list along with the handlers and then generate an entity created event.

        # The simulation sets the guids.
        entity.guid = get_uuid()
        self._entities[entity.guid] = entity
        self.queue_event(EntityCreatedEvent(entity_name=entity.name, entity_guid=entity.guid,
                                            entity_properties=entity.get_properties()))

        self._event_mediator.register_entity(entity=entity)

        self._previous_state[entity.guid] = EntityState(entity=entity)

    def remove_entity(self, entity):
        """
        Removes and entity from the simulation and informs other entities.  Note that any entities
        holding a reference to this entity should remove the entity.
        :param entity: The entity to remove.
        :type entity: Entity
        :return: None
        """
        self._entities.pop(entity.guid)
        self._event_mediator.deregister_entity(entity=entity)
        self._previous_state.pop(entity.guid)

        self.__send_event(EntityDestroyedEvent(entity_name=entity.name, entity_guid=entity.guid))

    def advance(self, cycles=1):
        """
        Manually advances time by the number of cycles specified (default of one).
        :param cycles: The number of cycles to advance by.
        :type cycles: int
        :return: Nothing
        """
        assert cycles and cycles > 0, f"Invalid cycles amount of {cycles}"  # sanity check to avoid cycling to the past.

        nbr_cycles = 0

        while nbr_cycles < cycles:

            current_time = self._event_queue.next_time()

            # If there are no events in the queue, cycle one in any case.
            if not current_time:  # this causes the same behavior for time stepped and jumped simulations.
                current_time = self._previous_time + 1
            self._previous_time = current_time

            # send a time update event for the next time.
            self.__send_event(NewTimeEvent(sim_time=current_time))

            # send all of the events for the current time.
            while self._event_queue.next_time() == current_time:
                # send all events from the queue to interested simulation entities.
                self.__send_event(self._event_queue.next())

            self.__send_change_events()

            nbr_cycles += 1

    def __send_change_events(self):
        """
        Go through all the entities and send out change events.
        :return:  None
        """
        # All entities should be in the state list since it is added when the entity is added.
        for entity in self._entities.values():
            diffs = self._previous_state[entity.guid].compare_and_update(entity)
            if len(diffs):
                evt = EntityChangedEvent(entity_name=entity.name, entity_guid=entity.guid, entity_properties=diffs)
                self.__send_event(evt)  # Send out notification at the end of the cycle, so other entities can update.

    def __send_event(self, event):
        """
        Sends the given event to interested entities.
        :param event: The event to send.
        :return: Nothing
        """
        self._event_mediator.send_event(event=event)
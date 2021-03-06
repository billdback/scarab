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

from collections import namedtuple
from copy import deepcopy
from enum import Enum
import re
import sys
from threading import Thread
import time
from typing import Union, List

from scarab.entities import Entity
from scarab.events import *
from scarab.loggers import log
from scarab.util import get_uuid, eprint


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

    def add(self, event) -> None:
        """
        Adds a new event in the proper location based on simulation time to send.
        :param Event event: The event to add to the queue.
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

    def __len__(self) -> int:
        """
        Returns the number of events in the queue.
        :return: The number of events in the queue.
        """
        the_len = 0
        for v in self._event_lists.values():
            the_len += len(v)

        return the_len

    def is_empty(self) -> bool:
        """
        Returns true if there are no events in the queue.
        :return: True if there are no events in the queue.
        """
        return len(self._event_lists.keys()) == 0 and not self._current_event_list

    def next_time(self) -> Union[int, None]:
        """
        Returns the next time if no more events were to be called.  I.e. the time of the next event.
        :return: The time of the next event in the queue or None if the list is empty.
        """
        if self._current_event_list:
            return self._current_time
        elif self.is_empty():
            return None

        return sorted(self._event_lists.keys())[0]

    def advance(self, increment=1) -> int:
        """
        Advances the time to increase the minimum time.
        :param int increment: The increment to advance by (must be >= 1)
        :return: The new current time.
        """
        assert increment > 0, f"Expected positive increment, but got {increment}"

        self._current_time += increment
        return self._current_time

    def next(self) -> Union[Event, None]:
        """
        Returns the next event in the queue.
        :return: The next event in the queue.
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
        :param list of str priorities: The order that events should be sent for a given time.  Match on patterns.
        """
        self._queues = {}
        self._priorities = []

        if priorities:
            for p in priorities:
                self._priorities.append(re.compile(p))
        self._priorities.append(re.compile(".*"))

        for p in self._priorities:
            self._queues[p] = TimeEventQueue()

    def __len__(self) -> int:
        """
        Returns the total number of events in the list.
        :return:the total number of events in the list.
        """
        the_len = 0
        for teq in self._queues.values():
            the_len += len(teq)
        return the_len

    def is_empty(self) -> bool:
        """
        Returns True if the queue is empty.
        :return: True if the queue is empty.
        """
        return len(self) == 0

    def next_time(self) -> Union[int, None]:
        """
        Returns the time of the next event across all queues.  This is the minimum.
        :return: The time of the next event or None.
        """
        next_time = None
        for qv in self._queues.values():
            nt = qv.next_time()
            if not next_time:
                next_time = nt
            elif nt:
                next_time = min(next_time, nt)

        return next_time

    def add(self, event) -> None:
        """
        Adds an event to the queue based on priority and time.
        :param event: The event to add to the queue.
        """
        for p in self._priorities:
            if p.fullmatch(event.name):
                q = self._queues[p]
                q.add(event)
                break

    def advance(self, increment=1) -> int:
        """
        Advances the time to increase the minimum time.
        :param int increment: The increment to advance by (must be >= 1)
        :return: The new current time.
        """
        assert increment > 0, f"Expected positive increment, but got {increment}"

        min_time = sys.maxsize
        for q in self._queues.values():
            t = q.advance(increment)
            min_time = min(min_time, t)

        return min_time

    def next(self) -> Union[Event, None]:
        """
        Returns the next event in the queue.
        :return: The next event in the queue or None if no events left.
        """
        # first, make sure the current time and next time are set based on the queues.
        next_time = self.next_time()
        for p in self._priorities:
            q = self._queues[p]
            if not q.is_empty() and q.next_time() == next_time:
                return q.next()

        return None


# Defined a named tuple for interests by an entity.
EntityInterestList = namedtuple("EntityInterestList", ["entity_name", "entities", "events"])


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

    def register_entity(self, entity) -> None:
        """
        Adds an entity to receive future events.
        :param Entity entity: The entity interested.
        """
        interest = entity.get_event_interest()

        self.__add_entity_interest(entity=entity, entity_interest=interest.named_events,
                                   simulation_interest=self._named_event_interest)
        self.__add_entity_interest(entity=entity, entity_interest=interest.entity_created_events,
                                   simulation_interest=self._entity_created_interest)
        self.__add_entity_interest(entity=entity, entity_interest=interest.entity_changed_events,
                                   simulation_interest=self._entity_changed_interest)
        self.__add_entity_interest(entity=entity, entity_interest=interest.entity_destroyed_events,
                                   simulation_interest=self._entity_destroyed_interest)
        entity._simulation = self

    @staticmethod
    def __add_entity_interest(entity, entity_interest, simulation_interest) -> None:
        """
        Adds entities to the
        :param Entity entity: The entity to add interest for.
        :param list entity_interest: The list to check and add it to.
        :param simulation_interest: The list of entity interest mappings in the simulation.
        """
        for name in entity_interest:
            entity_list = simulation_interest.get(name, None)
            if not entity_list:
                entity_list = []
                simulation_interest[name] = entity_list
            entity_list.append(entity)

    def deregister_entity(self, entity) -> None:
        """
        Removes all of the registrations for a given entity.
        TODO Create a faster way to do this.
        :param Entity entity: The entity to remove.
        """
        interest = entity.get_event_interest()

        self.__deregister_entity(entity=entity, entity_interest=interest.named_events,
                                 simulation_interest=self._named_event_interest)
        self.__deregister_entity(entity=entity, entity_interest=interest.entity_created_events,
                                 simulation_interest=self._entity_created_interest)
        self.__deregister_entity(entity=entity, entity_interest=interest.entity_changed_events,
                                 simulation_interest=self._entity_changed_interest)
        self.__deregister_entity(entity=entity, entity_interest=interest.entity_destroyed_events,
                                 simulation_interest=self._entity_destroyed_interest)

        entity._simulation = None

    @staticmethod
    def __deregister_entity(entity, entity_interest, simulation_interest) -> None:
        """
        Unregisters the entity from the given list.
        :param Entity entity: The entity to remove interest for.
        :param list of str entity_interest: The list of entities the entity has interest for.
        :param dict simulation_interest: The list of entity interest mappings in the simulation.
        """
        for entity_name in entity_interest:
            try:
                simulation_interest[entity_name].remove(entity)
            except KeyError:
                eprint(f"Missing mappings for {entity_name}.")

    def get_interest_for_entity(self, entity) -> EntityInterestList:
        """
        Returns the list of entities and events that the entity has interest in.
        :param entity: The entity to check for.
        :return: A EntityInterestList tuple.
        """
        entity_interest_list = set()
        for entity_list in [self._entity_created_interest,
                            self._entity_changed_interest,
                            self._entity_destroyed_interest]:
            for other_entity in entity_list:
                entity_interest_list.add(other_entity)

        event_interest_list = set()
        for event_name in self._named_event_interest:
            event_interest_list.add(event_name)

        return EntityInterestList(entity_name=entity.name, entities=entity_interest_list, events=event_interest_list)

    def send_event(self, event) -> None:
        """
        Handles the event by sending to all of the entities that registered it.
        :param Event event:  The event to handle.
        """
        if event.name == ENTITY_CREATED_EVENT:
            entity_list = self._entity_created_interest.get(event.entity.name, None)
        elif event.name == ENTITY_CHANGED_EVENT:
            entity_list = self._entity_changed_interest.get(event.entity.name, None)
        elif event.name == ENTITY_DESTROYED_EVENT:
            entity_list = self._entity_destroyed_interest.get(event.entity.name, None)
        else:
            entity_list = self._named_event_interest.get(event.name, None)

        if entity_list:
            for e in entity_list:
                log(EVENT_LOGGING,
                    f"sending event {event.name} to {e.guid} at time {event.sim_time}:  {event.__dict__}")
                e.handle_event(event=event)


class EntityState:
    """
    Records the entity state as a set of key/value pairs and can compare to another entity for differences.
    """

    def __init__(self, entity):
        """
        Creates a new entity state object.
        :param Entity entity: The entity to capture state from.
        """
        self.__entity_guid = entity.guid  # used to make sure changes are for the same entity.
        self.__state = self.__get_state_from_entity(entity=entity)

    def compare_and_update(self, entity) -> dict:
        """
        Compares state to an entity, update state to the new state, and returns a dictionary of the changes.
        This code handles scenarios where properties are added or removed.  It's not envisioned that this will be
        a common scenario.
        :param Entity entity:  The entity being compared to.
        :return: A dictionary of the changes.
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
    def __get_state_from_entity(entity) -> dict:
        """
        Returns the state from an entity.
        :param Entity entity:  The entity to get state from.
        :return: A dictionary of the changes.
        """
        state = {}
        for prop in entity.__dict__:
            if prop and not prop.startswith("_"):
                state[prop] = deepcopy(entity.__dict__[prop])

        return state


ENTITY_LOGGING = "scarab.entities"
EVENT_LOGGING = "scarab.events"
SIMULATION_LOGGING = "scarab.simulations"


# TODO add testing for this class.
class RemoteEntity(PropertyWrapper):
    """
    Represents an external entity (maybe on a different system).  Operations cannot be performed on this entity, just
    querying the properties.  Note that __slot__ is not supported.
    """

    def __init__(self, entity):
        """
        Creates a new remote entity with the same properties as the source entity, but no methods.
        :param entity: The entity to copy.
        """
        assert entity and isinstance(entity, Entity)
        # copy all public attributes to the wrapper.
        for attr in entity.__dict__.keys():
            if not attr.startswith("_"):
                self.__dict__[attr] = deepcopy(entity.__dict__[attr])
        super().__init__()


class SimulationState(Enum):
    """Defines the various simulations states."""

    not_started = 0
    initialized = 1
    running = 2
    paused = 3
    shutting_down = 4


class Simulation(Thread):
    """
    Class that represents a simulation with entities.  It manages the time and lifecycle of entities, and routes
    events to the interested entities and other simulation objects.
    """
    ADVANCE_UNLIMITED = -10  # indicates that there is no limit to advancing, so just keep going.

    def __init__(self, name, time_stepped=False, max_time=-1, minimum_step_time=0, event_priorities=None,
                 hide_license=False):
        """
        Creates a new simulation.
        :param str name: Name of the simulation.
        :param bool time_stepped: Indicates if the simulation is time stepped (i.e. one increment at a time) or not.  If
        False, then the next time sent out is the next time in the queue.
        :param int max_time: Maximum time in the simulation.  Once this time is reached, the simulation shuts down.
        :param int minimum_step_time: Mininum length of a single step in seconds.
        :param list of str event_priorities: Priorities of simulation events.  These fall *after* the standard events.
        :param bool hide_license: Hides the license that gets printed.
        """
        assert name
        self.time_stepped = time_stepped
        self.max_time = max_time
        self.minimum_step_time = minimum_step_time
        self._entities = {}        # entities in the simulation.
        self._previous_state = {}  # records the previous state of entities for comparison if they changed.
        all_event_priorities = [SIMULATION_EVENTS, ENTITY_EVENTS, TIME_EVENTS]
        if event_priorities:
            all_event_priorities.extend(event_priorities)

        self.__steps_to_advance = Simulation.ADVANCE_UNLIMITED

        self._event_queue = PriorityEventQueue(priorities=all_event_priorities)
        self._event_mediator = EventMediator()

        self._current_time = -1
        self._previous_time = 0

        self.state = SimulationState.not_started
        self.license = [
            "--------------------------------------------------------------------------",
            "",
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
            "along with this program.  If not, see <https://www.gnu.org/licenses/>.",
            "",
            "--------------------------------------------------------------------------"
        ]
        if not hide_license:
            self.print_license()

        self._views = []

        super().__init__(name=name)

    def __del__(self) -> None:
        """Make sure the simulation shuts down."""
        if self.state != SimulationState.shutting_down:
            self.shutdown()

    def __enter__(self):
        """
        Provides support for with statement.
        :returns: The simulation object.
        """
        self.start()
        while self.state == SimulationState.not_started:
            # wait for thread to start
            time.sleep(0.05)

        return self

    def __exit__(self, exception_class, exception_value, exception_traceback) -> None:
        """
        Cleans up after the end of the with block.
        :param exception_class: The exception class or None
        :param exception_value: The value from the exception.
        :param exception_traceback: The exception traceback.
        """
        self.shutdown()

    def run(self) -> None:
        """
        Causes the simulation thread to run.  This could be called from Simulation.start().
        """
        # Make sure this doesn't get called if the simulation is shutting down.
        if self.state == SimulationState.shutting_down:
            return

        log(SIMULATION_LOGGING, f"Simulation {self.name} starting.")

        self.__send_event(SimulationStartupEvent())
        self.state = SimulationState.paused

        # Keep running until shutting down.  Note that this is not a deamon, so shutdowns can be abrupt.
        while self.state != SimulationState.shutting_down:
            # If the state is not running, then sleep for a second and see if that changes.
            if self.state != SimulationState.running:
                time.sleep(0.05)
            else:  # simulation is running, see if it should step.
                if self.max_time > 0 and (self._previous_time >= self.max_time):
                    self.shutdown()

                if self.__steps_to_advance == Simulation.ADVANCE_UNLIMITED:
                    self.step()
                elif self.__steps_to_advance > 0:
                    self.step()
                    self.__steps_to_advance -= 1
                else:  # no time to advance, so pause until time to advance.
                    time.sleep(0.05)

    def shutdown(self) -> None:
        """
        Shuts down the simulation.
        """
        log(SIMULATION_LOGGING, f"Simulation {self.name} shutting down.")
        self.__send_event(SimulationShutdownEvent())
        self.state = SimulationState.shutting_down

    def print_license(self) -> None:
        """
        Prints the license for Scarab.
        """
        for line in self.license:
            print(line)

    def number_entities(self) -> int:
        """
        Returns the number of entities currently in the simulation.
        :return: The number of entities currently in the simulation.
        """
        return len(self._entities)

    def number_queued_events(self) -> int:
        """
        Return the number of queued events.
        :return: The number of queued events.
        """
        return len(self._event_queue)

    def next_time(self) -> int:
        """
        Returns the next simulation time.  This can change as events get added.
        :return: The next simulation time.
        """
        return self._event_queue.next_time()

    def queue_event(self, event) -> None:
        """
        Queues an event for sending.
        :param Event event: An event to send.
        """
        if not event.sim_time or event.sim_time <= self._previous_time:
            event.sim_time = self._previous_time + 1  # always add in the future.
        self._event_queue.add(event=event)

    def queue_message(self, message) -> None:
        """
        Queues a message for sending.
        :param Message message: A message to send.
        """
        if not message.sim_time or message.sim_time <= self._previous_time:
            message.sim_time = self._previous_time + 1  # always add in the future.
        # TODO Add support for handling messages.
        # self._message_queue.add(message=message)

    def add_entity(self, entity) -> None:
        """
        Adds a new entity to the simulation.  Note that this is not thread safe.
        :param Entity entity: The entity to add.
        """
        # Add the entity to the list along with the handlers and then generate an entity created event.

        # The simulation sets the guids.
        entity.guid = get_uuid()
        log(ENTITY_LOGGING, f"Adding entity type {entity.name} with GUID {entity.guid}")

        self._entities[entity.guid] = entity
        self.queue_event(EntityCreatedEvent(entity=RemoteEntity(entity)))

        self._event_mediator.register_entity(entity=entity)

        self._previous_state[entity.guid] = EntityState(entity=entity)

    def remove_entity(self, entity) -> None:
        """
        Removes and entity from the simulation and informs other entities.  Note that any entities
        holding a reference to this entity should remove the entity.
        :param Entity entity: The entity to remove.
        """
        log(ENTITY_LOGGING, f"Removing entity type {entity.name} with GUID {entity.guid}")

        self._entities.pop(entity.guid)
        self._event_mediator.deregister_entity(entity=entity)
        self._previous_state.pop(entity.guid)

        self.__send_event(EntityDestroyedEvent(entity=RemoteEntity(entity)))

    def register_view(self, view) -> None:
        """
        Adds a new view to be called on time updates.
        :param ViewInterface view: The view interface to call.
        """
        assert isinstance(view, ViewInterface)
        self._views.append(view)

    def check_interests_for_warnings(self) -> List[str]:
        """
        Checks the interests that have been registered against the actual entities to look for gaps.  This check is
        helpful for identifying errors in names in improve model validation.
        :return: A list of possible issues.
        """
        # TODO when specific interest, such as attribute detail interest, is added, add checks.
        # For each type of interest, look at the names of the entities that there is interest for and then look to see
        # if there are entities of that type.
        entity_interest_lists = []

        # get all of the interest, by entity.
        for entity in self._entities.values():
            entity_interest_lists.append(self._event_mediator.get_interest_for_entity(entity))

        # For each entity, check the interest to see if the entity is known.  Currently doesn't check for events since
        # they are not registered.
        warnings = []
        for entity_interest in entity_interest_lists:
            for other_entity in entity_interest.entities:
                if other_entity not in self._entities.keys():  # no known entity
                    warnings.append(
                        f"Entity {entity_interest.entity_name} has interest in unknown entity {other_entity}.")

        return warnings

    def print_interest_warnings(self) -> None:
        """
        Will check for interest warnings and print any that occur.
        """
        warnings = self.check_interests_for_warnings()
        for w in warnings:
            print(f"WARNING: {w}")

    def step(self) -> None:
        """
        Causes the simulation to advance a single step.
        """
        start_cycle_clock_time = time.time()

        self._current_time = self._event_queue.next_time()

        # If there are no events in the queue, cycle one in any case.
        previous_time = self._previous_time
        if not self._current_time:  # this causes the same behavior for time stepped and jumped simulations.
            self._current_time = self._previous_time + 1
        self._previous_time = self._current_time

        log(SIMULATION_LOGGING, f"Advancing the simulation from {previous_time} to {self._current_time}.")

        # send a time update event for the next time.
        self.__send_event(NewTimeEvent(previous_time=previous_time, new_time=self._current_time))
        # also notify the views to update.
        self._update_views(previous_time=previous_time, new_time=self._current_time)

        # send all of the events for the current time.
        while self._event_queue.next_time() == self._current_time:
            # send all events from the queue to interested simulation entities.
            self.__send_event(self._event_queue.next())

        self.__send_change_events()

        elapsed_time = time.time() - start_cycle_clock_time
        while elapsed_time < self.minimum_step_time:
            time.sleep(0.05)
            elapsed_time = time.time() - start_cycle_clock_time

    def _update_views(self, previous_time, new_time) -> None:
        """
        Updates the views that have been registered with the simulation.  Only happens on time updates.
        :param int previous_time: The previous time the simulation is advancing from.
        :param int new_time: The new time the simulation is advancing to.
        """
        for view in self._views:
            view.update_view(previous_time=previous_time, new_time=new_time)

    def advance(self, steps=ADVANCE_UNLIMITED) -> None:
        """
        Manually advances time by the number of steps specified.
        :param int steps: The number of steps to advance by.  If not specified runs unlimited.
        """
        assert steps > 0 or steps == Simulation.ADVANCE_UNLIMITED

        if steps > 0:
            log(SIMULATION_LOGGING, f"Advancing the simulation {steps} times.")
        else:
            log(SIMULATION_LOGGING, f"Advancing the simulation until shutdown.")

        self.__steps_to_advance = steps
        self.state = SimulationState.running
        print(f"simulation state is {self.state}")

    def advance_and_wait(self, steps=1) -> None:
        """
        Manually advances time by the number of steps specified (default of one), waiting while the sim advances.
        Note that this is mostly to make the simulation synchronous for testing.
        TODO - have an alternate approach with callbacks to make this thread safe and more flexible.
        :param int steps: The number of steps to advance by.  Must be positive.  Default is 1.
        """
        assert steps > 0

        start_time = self._previous_time
        self.advance(steps=steps)

        # now just wait for the time to catch up.
        while self._previous_time < (start_time + steps):
            # possible race condition.  It's possible that this returns before the last cycle is complete.
            time.sleep(1)

    def pause(self) -> None:
        """
        Pauses the simulation if it's running.
        """
        assert self.state != SimulationState.not_started  # make sure the simulation has actually been started.
        self.state = SimulationState.paused
        log(SIMULATION_LOGGING, f"Pausing the simulation.")

    def __send_change_events(self) -> None:
        """
        Go through all the entities and send out change events.
        """
        # All entities should be in the state list since it is added when the entity is added.
        for entity in self._entities.values():
            diffs = self._previous_state[entity.guid].compare_and_update(entity)
            if len(diffs):
                evt = EntityChangedEvent(entity=RemoteEntity(entity), changed_properties=diffs)
                self.__send_event(evt)  # Send out notification at the end of the cycle, so other entities can update.

    def __send_event(self, event) -> None:
        """
        Sends the given event to interested entities.
        :param event: The event to send.
        """
        log(EVENT_LOGGING, f"sending event {event.name} at sim time {event.sim_time}: {event}")
        event.sim_time = self._current_time
        self._event_mediator.send_event(event=event)


class ViewInterface(Entity):
    """
    Defines the basics for a view that can be connected to the simulation for display.
    Additional attributes would likely be set by the child.
    """

    def __init__(self, name, callback=None):
        """
        Creates a new view interface.
        :param str name: The name of the view.
        :param callback: A method to call to update.  Currently this only occurs on time updates.
        """
        assert name

        super().__init__(name=name)  # might want a better naming convention.
        self._callbacks = []  # List of callbacks for updates.
        if callback:
            self.add_callback(callback)

    def add_callback(self, callback) -> None:
        """
        Adds a callback.  Currently only time updates are supported.
        TODO add the ability to add callbacks on specific events.
        """
        assert callback
        self._callbacks.append(callback)

    def update_view(self, previous_time, new_time) -> None:
        """
        Called when the time gets updated.
        :param int previous_time: The previous simulation time.
        :param int new_time: The new simulation time.
        """
        for callback in self._callbacks:
            callback(previous_time, new_time)

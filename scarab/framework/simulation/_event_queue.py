"""
Copyright (c) 2024 William D Back

This file is part of Scarab licensed under the MIT License.
For full license text, see the LICENSE file in the project root.

This module implements the EventQueues for ordering events in the right order.
"""
import logging
from sortedcontainers import SortedDict
from typing import Dict

from scarab.framework.events import Event, ScarabEventType, standard_event_names

logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class TimeEventQueue:
    """
    Allows events to be queued in time-based order, so they can be sent at the correct times.  Events are `put`
    into the queue and then sorted based on event times.  Then, when a `get` is called, the next, soonest event is
    returned.  Events for the same time are returned in the order they were added.

    The queue will not allow events to be entered that are before the most recently retrieved time.  For example, if
    an event is retried (`get`) that is at time 3, then an error will be added if an event is added that comes before 3.
    Also, event times much be non-negative, i.e. >= 0.
    """

    def __init__(self):
        """Creates a new time event queue."""
        self._event_queue = SortedDict()  # sim_time -> List[Event]
        self._current_queue = None  # refers to the current queue being used.  This can still have events added.

        # Minimum time at which events can be added.  This is updated as events are retrieved.  Once an event is
        # retrieved at a given time, the next time is the minimum.
        self._min_event_time = 0
        self._length = 0  # track the size as things are added and removed.

    @property
    def next_event_time(self) -> int:
        """Gets the minimum time of the next event in the queue."""
        # The _min_event_time may not accurately reflect the next actual event in the queue.  For example,
        # with an empty queue, you would have a _min_event_time of 0.  If you then add an event at time 5, this doesn't
        # change.  That works OK because you still want to be able to add events sooner until the queue retrieves events
        # at that time.  So for the property, we have to actually check the queue for the first event.
        for key, value in self._event_queue.items():
            if value:
                return value[0].sim_time

        return 0

    @property
    def min_add_time(self):
        """Gets the minimum time of the next event in the queue."""
        return self._min_event_time + 1

    def put(self, event: Event) -> None:
        """
        Puts an event in the queue based on the event time.
        :param event: The event to add.
        """
        evt_time = event.sim_time
        if evt_time < self.min_add_time:
            raise ValueError(f"Event time is less than the minimum add time for this queue: {self.min_add_time}")

        queue = self._event_queue.get(evt_time, [])
        queue.append(event)
        self._event_queue[evt_time] = queue  # add back to account for new lists.
        self._length += 1

    def next_event(self) -> Event | None:
        """
        Returns the next event in the queue. The events at the lowest time will be returned in the order they were
        added to the queue.
        :return: The next event.
        """
        # If the current queue is empty, fill it with the next available queue
        if self._current_queue is None or len(self._current_queue) == 0:

            # Note that we can't just pop the previous from the queue, because you are allowed to add new events at
            # the current min time.  Only when the current queue is empty, does it get removed.
            if self._current_queue is not None and len(self._current_queue) == 0:
                del self._event_queue[self._min_event_time]

            next_key = next(iter(self._event_queue), None)

            # If there are no more queues left, return None
            if next_key is None:
                return None

            self._min_event_time = next_key  # Time for next event.  Add time must be later.
            self._current_queue = self._event_queue.get(next_key)

        # Decrease the total length and return the next event
        self._length -= 1
        return self._current_queue.pop(0)

    def __len__(self):
        """
        Returns the number of events in the queue.
        :return: The number of events currently in the queue.
        """
        return self._length


class OrderedEventQueue:
    """
    The ordered event queue expands on the idea of time event queues to allow events to be returned in a pre-defined
    order. For Scarab, events will be returned as follows (for a given time):
    * Time updated event
    * Any simulation events (start, stop, pause, resume)
    * Entity events (create, update, destroy)
    * Other events

    As with time queues, events can be added at the current minimum time, but not prior.

    FUTURE: Allow other events to also be ordered by the user.
    """

    # define indexes for the events in the list.
    _ENTITY_CREATE_IDX = 0
    _ENTITY_UPDATE_IDX = 1
    _ENTITY_DESTROY_IDX = 2
    _EVENT_IDX = 3

    # Maps from the type to the index of the queues to add to.
    _event_name_to_idx_map: Dict[str, int] = {
        ScarabEventType.ENTITY_CREATED.value: _ENTITY_CREATE_IDX,
        ScarabEventType.ENTITY_CHANGED.value: _ENTITY_UPDATE_IDX,
        ScarabEventType.ENTITY_DESTROYED.value: _ENTITY_DESTROY_IDX,
        ScarabEventType.NAMED_EVENT.value: _EVENT_IDX
    }

    def __init__(self):
        """Creates a new, ordered event queue."""
        self._event_queues = [TimeEventQueue(),  # entity create events.
                              TimeEventQueue(),  # entity update events.
                              TimeEventQueue(),  # entity destroy events.
                              TimeEventQueue()]  # other events.

    @property
    def next_event_time(self) -> int:
        """Returns the min time based on the min times in the queues."""

        # Given that the numbers can't be zero (next is always >= 1), filter out 0
        evt_times = [q.next_event_time for q in self._event_queues if q.next_event_time != 0]

        return min(evt_times) if evt_times else 0

    @property
    def min_add_time(self) -> int:
        """
        Returns the min time based on the min times in the queues.  This has to be the max of the minimums because
        the events don't get retrieved at the same time.  So one queue could have an event retrieved, increasing the
        time before others did.
        """
        return max([q.min_add_time for q in self._event_queues])

    def put(self, event: Event) -> None:
        """
        Adds an event to the queue. The event name will determine the proper queue to add to.
        :param event: The event to add to the queues.
        """

        logger.debug(f"Adding event to queue: {event.to_json()}")

        # named events actually have different names, so they get put in the named event queue.
        if event.event_name not in standard_event_names:
            self._event_queues[OrderedEventQueue._EVENT_IDX].put(event)
        else:
            self._event_queues[OrderedEventQueue._event_name_to_idx_map[event.event_name]].put(event)

    def next_event(self) -> Event | None:
        """
        Returns the next event from the queue.  The next event is based on the time and the order of events.
        :return: The next event or None if there are no more events.
        """

        # algo:
        # Get the next time, which is the soonest event.  It may be in multiple queues.
        # Run through the queues in order and see if they have events for that time.  Get the first one from the indexed
        # set of queues because they have to be in order and return it.

        next_time = self.next_event_time  # this calculates, so get it once.
        for q_idx in range(0, len(self._event_queues)):
            next_q = self._event_queues[q_idx]
            if next_q.next_event_time == next_time:
                event = next_q.next_event()
                return event

        return None

    def __len__(self) -> int:
        """Returns the length of the queue, i.e. the number of events in the queue."""
        return sum(len(q) for q in self._event_queues)

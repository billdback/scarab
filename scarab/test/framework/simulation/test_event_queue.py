"""
Copyright (c) 2024 William D Back

This file is part of Scarab licensed under the MIT License.
For full license text, see the LICENSE file in the project root.

Tests the event queues.
"""
import pytest
import random
from sortedcontainers import SortedDict

# noinspection PyProtectedMember
from scarab.framework.simulation._event_queue import OrderedEventQueue, TimeEventQueue
from scarab.framework.entity import scarab_properties
from scarab.framework.events import Event, EntityCreatedEvent, EntityChangedEvent, EntityDestroyedEvent, ScarabEventType
from scarab.test.framework.test_items import TestEntity1


def test_time_event_queue_init():
    """Tests time-based event queue initialization."""
    teq = TimeEventQueue()
    assert teq._event_queue == SortedDict()
    assert teq._current_queue is None
    assert teq.next_event_time == 0
    assert teq.min_add_time == 1
    assert len(teq) == 0


def test_time_event_queue_put_and_next():
    """Tests time-based event queue put and next to make sure events come back out in time order."""
    teq = TimeEventQueue()

    assert teq.next_event() is None

    for i in range(100):  # should mix up the numbers.
        evt = Event(sim_time=random.randint(1, 50), event_name='some-event')
        teq.put(evt)

    assert len(teq) == 100

    # Create a previous event that's before the ones entered to get started.
    prev_evt = Event(sim_time=0, event_name='some-event')
    remaining = 100
    for i in range(100):
        evt = teq.next_event()
        assert evt  # should get 100 back, so never none.
        assert evt.sim_time >= prev_evt.sim_time

        # should go down.
        remaining = remaining - 1
        assert remaining == len(teq)

        prev_evt = evt

    evt = teq.next_event()
    assert not evt  # shouldn't be any left.


def test_time_event_queue_add_event_in_the_past():
    """Tests getting errors when trying to add an event in the past."""
    teq = TimeEventQueue()

    # Add an event at time.
    teq.put(Event(sim_time=2, event_name='some-event'))
    teq.next_event()

    with pytest.raises(ValueError):
        teq.put(Event(sim_time=1, event_name='some-event'))


def test_event_queue_init():
    """Tests initializing a new event queue."""
    eq = OrderedEventQueue()
    assert eq.min_add_time == 1
    assert eq.next_event_time == 0
    assert len(eq) == 0


def test_adding_events():
    """Tests adding events to the queue."""
    eq = OrderedEventQueue()
    eq.put(Event(sim_time=5, event_name='some-event'))

    assert eq.min_add_time == 1
    assert eq.next_event_time == 5
    assert len(eq) == 1

    eq.put(Event(sim_time=3, event_name='another-event'))

    assert eq.min_add_time == 1
    assert eq.next_event_time == 3
    assert len(eq) == 2

    # now try to put one with a bad time.
    with pytest.raises(ValueError):
        eq.put(Event(sim_time=-1, event_name='a-final-event'))


def test_getting_events():
    """Tests getting events in the right order."""

    eq = OrderedEventQueue()

    # entity and props to use, doesn't matter much what they are.
    entity = TestEntity1()
    entity_props = scarab_properties(entity)

    assert eq.min_add_time == 1

    # put events in order and make sure the queue updates appropriately.
    eq.put(Event(sim_time=5, event_name='some-event'))
    assert eq.next_event_time == 5
    assert len(eq) == 1

    eq.put(EntityCreatedEvent(sim_time=5, entity_props=entity_props))
    assert eq.next_event_time == 5
    assert len(eq) == 2

    eq.put(EntityChangedEvent(sim_time=7, entity_props=entity_props, changed_props=['prop3']))
    assert eq.next_event_time == 5
    assert len(eq) == 3

    eq.put(Event(sim_time=7, event_name='some-event'))
    assert eq.next_event_time == 5
    assert len(eq) == 4

    eq.put(EntityDestroyedEvent(sim_time=9, entity_props=entity_props))
    assert eq.next_event_time == 5
    assert len(eq) == 5

    # Now test getting events back out in the right order.

    evt = eq.next_event()
    assert evt.sim_time == 5
    assert evt.event_name == ScarabEventType.ENTITY_CREATED
    assert len(eq) == 4

    evt = eq.next_event()
    assert evt.sim_time == 5
    assert evt.event_name == "some-event"
    assert len(eq) == 3

    evt = eq.next_event()
    assert evt.sim_time == 7
    assert evt.event_name == ScarabEventType.ENTITY_CHANGED
    assert len(eq) == 2

    evt = eq.next_event()
    assert evt.sim_time == 7
    assert evt.event_name == "some-event"
    assert len(eq) == 1

    evt = eq.next_event()
    assert evt.sim_time == 9
    assert evt.event_name == ScarabEventType.ENTITY_DESTROYED
    assert len(eq) == 0

    evt = eq.next_event()
    assert evt is None
    assert len(eq) == 0

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
"""

import unittest

from scarab.entities import *
from scarab.events import *


class TestEntity(Entity):
    """Class to use for testing entities."""

    def __init__(self):
        """Creates a new test entity."""
        self.basic_event_handler_called = False
        self.simulation_shutdown_called = False
        self.time_event_handler_called = False
        self.sim_time = 0

        self.event2_handler1_called = False
        self.event2_handler2_called = False

        self.entity1_created = False
        self.entity1_changed = False
        self.entity1_destroyed = False

        Entity.__init__(self, name="testunit.test-entity")

    @event_handler(event_name="event1")
    def handle_event_one(self, event):
        assert(event is not None)
        self.basic_event_handler_called = True

    @event_handler(event_name="event2")
    def handle_event_two1(self, event):
        assert(event is not None)
        self.event2_handler1_called = True

    @event_handler(event_name="event2")
    def handle_event_two2(self, event):
        assert(event is not None)
        self.event2_handler2_called = True

    @simulation_shutdown_handler
    def handle_simulation_shutdown(self, shutdown_event):
        """Handles simulation shutting down events."""
        assert(shutdown_event is not None)
        self.simulation_shutdown_called = True

    @time_update_event_handler
    def handle_time_event(self, time_event):
        """Handles time events."""
        assert(time_event is not None)
        self.time_event_handler_called = True
        self.sim_time = time_event.sim_time

    @entity_created_event_handler("entity1")
    def handle_entity_one_created(self, entity_created_event):
        """Handles EntityCreatedEvent"""
        assert (entity_created_event is not None)
        self.entity1_created = True

    @entity_changed_event_handler("entity1")
    def handle_entity_one_changed(self, entity_changed_event):
        """Handles EntityCreatedEvent"""
        assert (entity_changed_event is not None)
        self.entity1_changed = True

    @entity_destroyed_event_handler("entity1")
    def handle_entity_one_destroyed(self, entity_destroyed_event):
        """Handles EntityCreatedEvent"""
        assert (entity_destroyed_event is not None)
        self.entity1_destroyed = True


class TestEntityCallMe(Entity):
    """Entity to be called by the handler.  Used to test calls to wrong entities."""

    def __init__(self):
        self.i_was_called = False
        Entity.__init__(self, name="testunit.test-entity-call")

    @event_handler(event_name="call_test_event")
    def handle_an_event(self, event):
        """Handles an event """
        assert(event is not None)
        self.i_was_called = True


class TestEntityDontCallMe(Entity):
    """Entity that shouldn't be called."""

    def __init__(self):
        self.i_was_called = False
        Entity.__init__(self, name="testunit.test-entity-dont-call")

    @entity_created_event_handler("testunit.test-entity-to-change")
    def handle_entity_changed(self, entity):
        """Called whe the entity changed."""
        self._other_entity = entity

    @entity_changed_event_handler("testunit.test-entity-to-change")
    def handle_entity_changed(self, entity_changed_event):
        """Called when the entity changed."""
        self._change_event = entity_changed_event


class TestEntities(unittest.TestCase):
    """Tests simulation entities."""

    def test_entity_interest(self):
        """Tests getting the events that an entity is interested in."""
        te = TestEntity()
        ei = te.get_event_interest()

        self.assertTrue("event1" in ei.named_events)
        self.assertTrue("event2" in ei.named_events)

        self.assertTrue("entity1" in ei.entity_created_events)
        self.assertTrue("entity1" in ei.entity_changed_events)
        self.assertTrue("entity1" in ei.entity_destroyed_events)

    def test_basic_event_handling(self):
        """Tests that basic events are handled properly."""
        te = TestEntity()

        # These would be called from the framework.
        te.handle_event(Event(name="event1"))
        self.assertTrue(te.basic_event_handler_called)

        with self.assertRaises(KeyError):
            te.handle_event(Event(name="unknown_event"))

    def test_multiple_handlers_for_same_event(self):
        """Tests that multiple handlers can be registered for a single event."""
        te = TestEntity()

        # These would be called from the framework.
        te.handle_event(Event(name="event2"))
        self.assertTrue(te.event2_handler1_called)
        self.assertTrue(te.event2_handler2_called)

    def test_simulation_shutdown_event_handling(self):
        """Tests that simulation shutdown events are handled properly."""
        te = TestEntity()

        # These would be called from the framework.
        te.handle_event(SimulationShutdownEvent())
        self.assertTrue(te.simulation_shutdown_called)

    def test_time_update_event_handling(self):
        """Tests that time update events are handled properly."""
        te = TestEntity()
        self.assertEqual(0, te.sim_time)

        # This would be called from the framework.
        te.handle_event(NewTimeEvent(sim_time=2))
        self.assertTrue(te.time_event_handler_called)
        self.assertEqual(2, te.sim_time)


    def test_entity_changes(self):
        """Tests creating, updating, and destroying and entity."""
        te = TestEntity()

        # This would be called from the framework.
        te.handle_event(EntityCreatedEvent(entity_name="entity1", entity_guid="123"))
        self.assertTrue(te.entity1_created)
        te.handle_event(EntityChangedEvent(entity_name="entity1", entity_guid="123"))
        self.assertTrue(te.entity1_changed)
        te.handle_event(EntityDestroyedEvent(entity_name="entity1", entity_guid="123"))
        self.assertTrue(te.entity1_destroyed)

    def test_calling_correct_entities(self):
        """Tests making sure only handlers on entities that registered them are called."""
        te1 = TestEntityCallMe()
        te2 = TestEntityDontCallMe()

        self.assertFalse(te1.i_was_called)
        self.assertFalse(te2.i_was_called)

        te1.handle_event(Event(name="call_test_event"))
        self.assertTrue(te1.i_was_called)
        self.assertFalse(te2.i_was_called)

        with self.assertRaises(KeyError):
            te2.handle_event(Event(name="call_test_event"))

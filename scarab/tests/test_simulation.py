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
from scarab.simulation import *

# Test classes to use for testing the simulation. --------------------------------------------------------------------


class TestEntityOne(Entity):
    """First entity to use for testing."""

    def __init__(self):
        self.event_one_handled = False
        self.event_two_handled = False

        self.entity2_created = False
        self.entity2_changed = False
        self.entity2_destroyed = False

        self.property_1 = "one"
        self.property_2 = 2
        Entity.__init__(self, name="test.entity.one")

    @event_handler(event_name="test.event.one")
    def event_one_handler(self, event):
        assert event.name == "test.event.one"
        self.event_one_handled = True

    @entity_created_event_handler("test.entity.two")
    def handle_entity_two_created(self, entity):
        """Handles EntityCreatedEvent"""
        assert entity.name == "test.entity.two"
        self.entity2_created = True

    @entity_changed_event_handler("test.entity.two")
    def handle_entity_two_changed(self, entity, changed_properties):
        """Handles EntityCreatedEvent"""
        assert entity.name == "test.entity.two"
        assert changed_properties
        self.entity2_changed = True

    @entity_destroyed_event_handler("test.entity.two")
    def handle_entity_two_destroyed(self, entity):
        """Handles EntityCreatedEvent"""
        assert entity.name == "test.entity.two"
        self.entity2_destroyed = True


class TestEntityTwo(Entity):
    """Second entity to use for testing."""

    def __init__(self):
        self.event_one_handled = False
        self.event_two_handled = False

        self.entity1_created = False
        self.entity1_changed = False
        self.entity1_destroyed = False

        self.property_3 = "three"
        self.property_4 = 4
        Entity.__init__(self, name="test.entity.two")

    @event_handler(event_name="test.event.two")
    def event_two_handler(self, entity):
        """This entity is only interested in the second event."""
        assert entity.name == "test.event.two"
        self.event_two_handled = True

    @entity_created_event_handler("test.entity.one")
    def handle_entity_one_created(self, entity):
        """Handles EntityCreatedEvent"""
        assert entity.name == "test.entity.one"
        self.entity1_created = True

    @entity_changed_event_handler("test.entity.one")
    def handle_entity_one_changed(self, entity, changed_properties):
        """Handles EntityCreatedEvent"""
        assert entity.name == "test.entity.one"
        assert changed_properties
        self.entity1_changed = True

    @entity_destroyed_event_handler("test.entity.one")
    def handle_entity_one_destroyed(self, entity):
        """Handles EntityCreatedEvent"""
        assert entity.name == "test.entity.one"
        self.entity1_destroyed = True


class TestEntityToChange(Entity):
    """Class that I will change for testing."""

    def __init__(self):
        """Creates a new test entity."""
        self.property1 = False
        self.property2 = True
        self._property3 = True

        Entity.__init__(self, name="testunit.test-entity-to-change")


class EntityChangeWatcher(Entity):
    """Watches the entity to change entity."""

    def __init__(self):
        """Create new change watcher."""
        self.change_entity = None
        self.other_entity = None

        Entity.__init__(self, name="testunit.watch-test-entity-to-change")

    @entity_created_event_handler(entity_name="testunit.watch-test-entity-to-change")
    def new_entity_to_watch(self, entity):
        """Remembers the other entity."""
        self.other_entity = entity

    @entity_changed_event_handler(entity_name="testunit.watch-test-entity-to-change")
    def watched_entity_changed(self, entity, changed_properties):
        """Gets called if the watched entity changes."""
        self.change_entity = entity


class EntityTimeEventCatcher(Entity):
    """Handles time events."""

    def __init__(self):
        self.times_updated = []
        self.current_time = 0
        Entity.__init__(self, name="testunit.time.event.catcher")

    @time_update_event_handler
    def handle_time_update(self, previous_time, new_time):
        self.times_updated.append(new_time)
        self.current_time = new_time

# Actual tests -------------------------------------------------------------------------------------------------------


class TestSimulation(unittest.TestCase):
    """Tests the simulation class."""

    def test_print_license(self):
        """Prints the license.  Visual test only."""
        sim = Simulation()
        sim.print_license()

    def test_create_simulation(self):
        """Tests creating a simulation."""
        sim = Simulation()
        self.assertFalse(sim.time_stepped)
        self.assertIsNone(sim.next_time())
        self.assertEqual(sim.number_entities(), 0)

        sim = Simulation(time_stepped=True)
        self.assertTrue(sim.time_stepped)
        self.assertIsNone(sim.next_time())

    def test_add_entity(self):
        """Tests adding entities to a simulation."""
        sim = Simulation()
        self.assertEqual(sim.number_entities(), 0)
        self.assertEqual(sim.next_time(), None)
        self.assertEqual(sim.number_queued_events(), 0)

        entity1 = TestEntityOne()
        sim.add_entity(entity1)
        entity2 = TestEntityTwo()
        sim.add_entity(entity2)

        self.assertEqual(sim.number_entities(), 2)
        self.assertEqual(sim.next_time(), 1)
        self.assertEqual(sim.number_queued_events(), 2)

        # increment the time one and make sure the entities were notified of time advance.
        sim.advance(1)

        # Make sure the entities received notification about the others.
        self.assertTrue(entity1.entity2_created)
        self.assertTrue(entity2.entity1_created)

    def test_recognize_entity_changes(self):
        """Test recognizing when entities change and sending change messages."""
        sim = Simulation()

        te_change = TestEntityToChange()
        sim.add_entity(te_change)
        te_watcher = EntityChangeWatcher()
        sim.add_entity(te_watcher)

        sim.advance(1)
        self.assertTrue(te_watcher.other_entity)

        te_change.property1 = 2
        te_change.property2 = "hi"
        te_change._property3 = "don't see me"
        te_change.__dict__["property4"] = "new_property"
        sim.advance(1)

        self.assertEqual(te_watcher.other_entity.guid, te_watcher.change_entity.guid)
        self.assertEqual(te_watcher.other_entity.name, te_watcher.change_entity.name)

    def test_destroy_entity(self):
        """Tests destroying an entity."""
        te1 = TestEntityOne()
        te2 = TestEntityTwo()

        sim = Simulation()
        sim.add_entity(te1)
        sim.add_entity(te2)
        sim.advance()

        self.assertTrue(te1.entity2_created)
        self.assertTrue(te2.entity1_created)

        sim.remove_entity(entity=te2)
        sim.advance()
        self.assertTrue(te1.entity2_destroyed)

        sim.queue_event(event=Event(name="test.event.two"))
        sim.advance()
        self.assertFalse(te2.event_two_handled)

    def test_advance_simulation_in_steps(self):
        """Tests advancing the simulation a step at a time."""
        sim = Simulation(time_stepped=True)
        te = EntityTimeEventCatcher()
        sim.add_entity(te)

        sim.advance(cycles=5)
        self.assertEqual(5, te.current_time)
        self.assertEqual(5, len(te.times_updated))
        self.assertEqual([1, 2, 3, 4, 5], te.times_updated)

    def test_advance_simulation_in_jumps(self):
        """Tests advancing the simulation multiple steps."""
        sim = Simulation(time_stepped=False)
        te = EntityTimeEventCatcher()
        sim.add_entity(te)

        sim.queue_event(Event(name="test-entity.some_event", sim_time=5))
        sim.queue_event(Event(name="test-entity.some_event", sim_time=10))
        sim.queue_event(Event(name="test-entity.some_event", sim_time=15))
        sim.queue_event(Event(name="test-entity.some_event", sim_time=20))
        sim.queue_event(Event(name="test-entity.some_event", sim_time=25))

        sim.advance(cycles=7)
        self.assertEqual(26, te.current_time)  # 1 (for event creation, 5-25 for events above, 26 for single time.
        self.assertEqual(7, len(te.times_updated))
        self.assertEqual([1, 5, 10, 15, 20, 25, 26], te.times_updated)

    def start_simulation(self):
        """Tests starting the simulation."""
        pass

    def test_stop_simulation(self):
        """Tests starting the simulation."""
        pass

    def test_pause_simulation(self):
        """Tests starting the simulation."""
        pass

    def test_resume_simulation(self):
        """Tests starting the simulation."""
        pass


if __name__ == '__main__':
    unittest.main()
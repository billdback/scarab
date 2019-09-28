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

import copy
import unittest
from scarab.events import Property, Event, Message
from scarab.events import EntityCreatedEvent, EntityDestroyedEvent, EntityChangedEvent, NewTimeEvent
from scarab.events import ENTITY_CREATED_EVENT, ENTITY_DESTROYED_EVENT, ENTITY_CHANGED_EVENT, NEW_TIME_EVENT


class TestEvent(Event):
    """Class that extends event."""

    def __init__(self):
        """Create a new event type with properties."""
        self.property_1 = "one"
        self.property_2 = 2
        self.property_3 = ["a", "b", "c"]
        super().__init__("test-event")


class TestEvents(unittest.TestCase):
    """Tests the Events class."""

    def test_event_creation(self):
        """Test creating events with different values."""
        evt = Event(name="evt1")
        self.assertEqual(evt.name, "evt1")
        self.assertEqual(evt.sim_id, None)
        self.assertEqual(evt.sim_time, None)
        self.assertEqual(evt.created_by, None)

        evt = Event(name="evt2", sim_id="1234", sim_time=0, created_by="4567")
        self.assertEqual(evt.name, "evt2")
        self.assertEqual(evt.sim_id, "1234")
        self.assertEqual(evt.sim_time, 0)
        self.assertEqual(evt.created_by, "4567")

    def test_event_creation_with_passed_properties(self):
        """Tests creating an event and passing in properties via the keyword."""
        evt = Event(name="kw_event", attr1="one", attr2=2, attr3=3.3, attr4=None)
        self.assertEqual(evt.name, "kw_event")
        self.assertEqual(evt.attr1, "one")
        self.assertEqual(evt.attr2, 2)
        self.assertEqual(evt.attr3, 3.3)
        self.assertIsNone(evt.attr4)

    def test_is_complete(self):
        """Tests that an event has all of the properties to make it complete.  Events can be created without certain
        properties, but then need to have those set before sending out."""
        evt = Event(name="evt1")
        self.assertFalse(evt.is_complete())

        evt.sim_id = "123"
        evt.created_by = "456"
        self.assertTrue(evt.is_complete())

    def test_copy(self):
        """Tests copying an event."""
        evt1 = Event(name="event", sim_time=1, sim_id="123", created_by="456")
        evt1.dynamic1 = "attr1"
        attr = Property(name="attr2", default_value=2, validator=lambda x: x < 10)
        evt1.attr2 = attr

        evt2 = copy.deepcopy(evt1)
        self.assertEqual(evt2.name, "event")
        self.assertEqual(evt2.sim_id, "123")
        self.assertEqual(evt2.sim_time, 1)
        self.assertEqual(evt2.created_by, "456")

        # make sure the validator got copied over.
        with self.assertRaises(ValueError):
            evt1.attr2 = 15

    def test_new_event_types_with_properties(self):
        """Tests creating and using new events based on Event."""
        te = TestEvent()
        self.assertEqual(te.name, "test-event")
        self.assertEqual(te.property_1, "one")
        self.assertEqual(te.property_2, 2)
        self.assertEqual(te.property_3, ["a", "b", "c"])

    def test_new_event_types_with_dynamic_properties(self):
        """Tests adding dynamic properties to a defined event."""
        te = TestEvent()
        te.property_4 = "property four"
        te.property_5 = Property(name="property_5", default_value=5, validator=lambda x: x < 10)

        self.assertEqual(te.property_4, "property four")
        self.assertEqual(te.property_5, 5)

        with self.assertRaises(ValueError):
            te.property_5 = 15

    def test_common_events(self):
        """Just tests creation of common events."""

        event = EntityCreatedEvent(entity_name="test.entity", entity_guid="abc123")
        self.assertEqual(event.name, ENTITY_CREATED_EVENT)
        self.assertEqual(event.entity_guid, "abc123")
        self.assertEqual(event.entity_name, "test.entity")

        event = EntityDestroyedEvent(entity_name="test.entity", entity_guid="abc123")
        self.assertEqual(event.name, ENTITY_DESTROYED_EVENT)
        self.assertEqual(event.entity_guid, "abc123")

        # TODO pass a wrapper that represents and entity with properties for ease of use.
        event = EntityChangedEvent(entity_name="test.entity", entity_guid="abc123",
                                   entity_properties={"property1": 1, "property2": "two"})
        self.assertEqual(event.name, ENTITY_CHANGED_EVENT)
        self.assertEqual(event.entity_guid, "abc123")
        self.assertEqual(event.entity_properties["property1"], 1)
        # self.assertEqual(event.entity_properties.property1, 1)
        self.assertEqual(event.entity_properties["property2"], "two")

        event = NewTimeEvent(sim_time=12)
        self.assertEqual(event.name, NEW_TIME_EVENT)
        self.assertEqual(event.sim_time, 12)


class TestCommands(unittest.TestCase):
    """Tests the Message class."""

    def test_command_creation(self):
        """Test creating commands with different values."""
        cmd = Message(name="cmd1", target_guid="abc123")
        self.assertEqual(cmd.name, "cmd1")
        self.assertEqual(cmd.target_guid, "abc123")
        self.assertEqual(cmd.sim_id, None)
        self.assertEqual(cmd.sim_time, None)
        self.assertEqual(cmd.created_by, None)

        cmd = Message(name="cmd2", target_guid="abc123", sim_id="1234", sim_time=0, created_by="4567")
        self.assertEqual(cmd.name, "cmd2")
        self.assertEqual(cmd.target_guid, "abc123")
        self.assertEqual(cmd.sim_id, "1234")
        self.assertEqual(cmd.sim_time, 0)
        self.assertEqual(cmd.created_by, "4567")


if __name__ == '__main__':
    unittest.main()

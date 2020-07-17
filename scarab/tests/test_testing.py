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
from scarab.testing import EntityTestWrapper as etw


class EntityForTesting(Entity):
    """An entity to use for testing the testing classes."""

    def __init__(self):
        self.handled_entity_created = False
        self.handled_entity_changed = False
        self.handled_entity_destroyed = False
        self.handled_event = False
        self.handled_time_update = False

        super().__init__(name="test.entity")

    @entity_created_event_handler(entity_name="other.entity")
    def handle_entity_created(self, entity):
        self.handled_entity_created = True

    @entity_changed_event_handler(entity_name="other.entity")
    def handle_entity_changed(self, entity, changed_properties):
        self.handled_entity_changed = True

    @entity_destroyed_event_handler(entity_name="other.entity")
    def handle_entity_destroyed(self, entity):
        self.handled_entity_destroyed = True

    @time_update_event_handler
    def handle_new_time(self, new_time, old_time):
        self.handled_time_update = True

    @event_handler(event_name="some.event")
    def handle_some_event(self, event):
        self.handled_event = True

    @event_handler(event_name="send.event")
    def handle_and_send_event(self, event):
        self._simulation.queue_event(Event("entity.sent.event"))

    @event_handler(event_name="send.message")
    def handle_and_send_message(self, event):
        self._simulation.queue_message(Message("entity.sent.message", target_guid="2"))


class TestTesting(unittest.TestCase):
    """Tests for the scarab.testing module."""

    def test_wrap_entities(self):
        """Tests """
        entity = etw(EntityForTesting())

        # verify all are false to start with.
        self.assertFalse(entity.handled_entity_created)
        self.assertFalse(entity.handled_entity_changed)
        self.assertFalse(entity.handled_entity_destroyed)
        self.assertFalse(entity.handled_event)
        self.assertFalse(entity.handled_time_update)

        entity.send_entity_created_event(entity_name="other.entity")
        self.assertTrue(entity.handled_entity_created)

        entity.send_entity_changed_event(entity_name="other.entity")
        self.assertTrue(entity.handled_entity_changed)

        entity.send_entity_destroyed_event(entity_name="other.entity", entity_guid=1)
        self.assertTrue(entity.handled_entity_destroyed)

        entity.send_new_time(new_time=1)
        self.assertTrue(entity.handled_time_update)

        entity.send_event(event=Event(name="some.event"))
        self.assertTrue(entity.handled_event)

        entity.send_event(event=Event(name="send.event"))
        events = entity.simulation.queued_events
        self.assertEqual(1, len(events))
        self.assertEqual("entity.sent.event", events[0].name)

        entity.send_event(event=Event(name="send.message"))
        messages = entity.simulation.queued_messages
        self.assertEqual(1, len(messages))
        self.assertEqual("entity.sent.message", messages[0].name)

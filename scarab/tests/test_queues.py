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

from scarab.events import Event
from scarab.simulation import TimeEventQueue, PriorityEventQueue


class TestTimeEventQueue(unittest.TestCase):
    """Tests the time event queues."""

    def test_add_event_with_too_low_time(self):
        """Tests trying to add an event without a sim time."""
        event = Event(name="event1", sim_time=-2)
        teq = TimeEventQueue()
        with self.assertRaises(ValueError):
            teq.add(event)

    def test_len(self):
        teq = TimeEventQueue()
        for cnt in range(1,4):  # add three events out of order.
            teq.add(Event(name="event_%d" % cnt, sim_time=10-cnt))

        self.assertEqual(len(teq), 3)

    def test_get_events(self):
        teq = TimeEventQueue()
        # add some events in various orders.
        teq.add(Event(name="event_3_1", sim_time=3))
        teq.add(Event(name="event_3_2", sim_time=3))
        teq.add(Event(name="event_2_1", sim_time=2))
        teq.add(Event(name="event_5_1", sim_time=5))
        teq.add(Event(name="event_1_1")) # no time given, so 1

        self.assertEqual(len(teq), 5)
        self.assertEqual(teq._current_time, 0)

        event = teq.next()
        self.assertEqual(event.name, "event_1_1")
        self.assertEqual(teq._current_time, 1)
        self.assertEqual(teq.next_time(), 2)

        event = teq.next()
        self.assertEqual(event.name, "event_2_1")
        self.assertEqual(teq._current_time, 2)
        self.assertEqual(teq.next_time(), 3)

        event = teq.next()
        self.assertEqual(event.name, "event_3_1")
        self.assertEqual(teq._current_time, 3)
        self.assertEqual(teq.next_time(), 3)
        event = teq.next()
        self.assertEqual(event.name, "event_3_2")
        self.assertEqual(teq._current_time, 3)
        self.assertEqual(teq.next_time(), 5)

        event = teq.next()
        self.assertEqual(event.name, "event_5_1")
        self.assertEqual(teq._current_time, 5)
        self.assertEqual(teq.next_time(), None)  # what *should* happen here?

        self.assertTrue(teq.is_empty())
        event = teq.next()
        self.assertIsNone(event)

    def test_add_old_event(self):
        """Test adding an event before current time."""
        teq = TimeEventQueue()
        teq.add(Event(name="event_5_1", sim_time=5))

        teq.next()
        self.assertEqual(teq._current_time, 5)

        with self.assertRaises(ValueError): # earlier time
            teq.add(Event(name="event_4_1", sim_time=4))

        with self.assertRaises(ValueError): # current time.
            teq.add(Event(name="event_5_1", sim_time=5))


class TestPriorityQueue(unittest.TestCase):
    """Tests the PriorityEventQueue"""

    def test_priority_queue(self):
        """Tests creating a priority event queue and adding events."""
        peq = PriorityEventQueue(priorities=["high.*", "medium.*"])
        self.assertEqual(peq.next_time(), None)
        self.assertTrue(peq.is_empty())

        peq.add(Event(name="high-1"))
        peq.add(Event(name="medium-1"))
        peq.add(Event(name="low-1"))

        self.assertFalse(peq.is_empty())

        peq.add(Event(name="high-5", sim_time=5))
        peq.add(Event(name="medium-3", sim_time=3))
        peq.add(Event(name="low-2", sim_time=2))
        peq.add(Event(name="low-4", sim_time=4))
        peq.add(Event(name="medium-4", sim_time=4))
        peq.add(Event(name="low-10", sim_time=10))

        self.assertEqual(peq.next_time(), 1)

        self.assertEqual(peq.next().name, "high-1")
        self.assertEqual(peq.next_time(), 1)
        self.assertEqual(peq.next().name, "medium-1")
        self.assertEqual(peq.next_time(), 1)
        self.assertEqual(peq.next().name, "low-1")
        self.assertEqual(peq.next_time(), 2)

        self.assertEqual(peq.next().name, "low-2")
        self.assertEqual(peq.next_time(), 3)

        self.assertEqual(peq.next().name, "medium-3")
        self.assertEqual(peq.next_time(), 4)

        self.assertEqual(peq.next().name, "medium-4")
        self.assertEqual(peq.next_time(), 4)
        self.assertEqual(peq.next().name, "low-4")
        self.assertEqual(peq.next_time(), 5)

        self.assertEqual(peq.next().name, "high-5")
        self.assertEqual(peq.next_time(), 10)

        self.assertEqual(peq.next().name, "low-10")
        self.assertIsNone(peq.next_time())


if __name__ == '__main__':
    unittest.main()

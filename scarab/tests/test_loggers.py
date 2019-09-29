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

import os
import unittest

from scarab.loggers import log, ListLogger, FileLogger


class TestLogging(unittest.TestCase):
    """Tests logging."""

    def test_list_logging(self):
        """Tests logging with the list logger."""
        ll1 = ListLogger(topics="topic1")
        ll2 = ListLogger(topics=["topic2", "topic3"])
        ll3 = ListLogger(topics="topic3")

        log(topic="topic1", message="message 1")
        log(topic="topic2", message="message 2")
        log(topic="topic3", message="message 3")
        log(topic="topic4", message="message 4")

        self.assertEqual(1, len(ll1))
        self.assertEqual(2, len(ll2))
        self.assertEqual(1, len(ll3))

        self.assertTrue("] topic1: message 1" in ll1.get_log_messages()[0])

        self.assertTrue("] topic2: message 2" in ll2.get_log_messages()[0])
        self.assertTrue("] topic3: message 3" in ll2.get_log_messages()[1])

        self.assertTrue("] topic3: message 3" in ll3.get_log_messages()[0])

        ll1.clear()
        self.assertEqual(0, len(ll1))
        self.assertEqual(2, len(ll2))

    def test_file_logger(self):
        """Tests logging to a file."""
        test_file = "test.log"
        fl = FileLogger(topics="topic1", filename=test_file)

        self.assertFalse(os.path.exists(test_file))

        log(topic="topic1", message="message 1")
        log(topic="topic1", message="message 2")

        self.assertTrue(os.path.exists(test_file))

        fl.close()

        with open(test_file, "r") as f:
            line = f.readline()
            self.assertTrue("] topic1: message 1" in line)
            line = f.readline()
            self.assertTrue("] topic1: message 2" in line)

        os.remove(test_file)


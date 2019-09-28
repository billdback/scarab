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

# from .context import scarab

import unittest
from scarab.util import get_uuid


class TestUUID(unittest.TestCase):
    """Tests the getting unique IDs"""

    def test_get_uuid(self):
        """Test getting unique IDs and making sure they are unique.  Not 100% sure this is comprehensive."""
        uuids = []
        for cnt in range(1000):
            uuid = get_uuid()
            self.assertTrue(uuid not in uuids)
            uuids.append(uuid)

if __name__ == '__main__':
    unittest.main()

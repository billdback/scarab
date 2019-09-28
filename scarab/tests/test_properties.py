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
from scarab.events import Property, PropertyWrapper


class TestProperties(unittest.TestCase):
    """Tests the property class."""

    def test_property_creation(self):
        """Test creating a basic property with just a name and default value."""

        # all defaults
        attr = Property(name="property1")
        self.assertEqual(attr.name, "property1")
        self.assertIsNone(attr.get_value())

        # specify default name.
        attr = Property(name="property2", default_value=0)
        self.assertEqual(attr.name, "property2")
        self.assertEqual(attr.get_value(), 0)

    def test_validation_with_lambda(self):
        """Tests adding a lambda validator."""
        attr = Property(name="property1", validator=lambda x: x < 100)

        # make sure successful.
        attr.set_value(50)
        self.assertEqual(attr.get_value(), 50)

        # make sure raises value error.
        self.assertRaises(ValueError, attr.set_value,100)

    def test_validation_with_function(self):
        """Tests adding a validator using a predefined function."""

        # validation function to use.
        def less_than_100(x):
            return x < 100

        attr = Property(name="property1", validator=less_than_100)

        # make sure successful.
        attr.set_value(50)
        self.assertEqual(attr.get_value(), 50)

        # make sure raises value error.
        self.assertRaises(ValueError, attr.set_value,100)


class TestPropertyWrapper(unittest.TestCase):
    """Tests the property wrapper class."""

    class TestWrapper(PropertyWrapper):
        """Class to use for testing the wrapper."""

        def __init__(self):
            """Create test wrapper."""
            self.native_attr = "hi"
            PropertyWrapper.__init__(self)

    def test_setting_and_getting_class_properties(self):
        aw = TestPropertyWrapper.TestWrapper()
        aw.native_attr = "hi, there"
        self.assertEqual(aw.native_attr, "hi, there")

        aw.dynamic_attr = 3
        self.assertEqual(aw.dynamic_attr, 3)

        attr = Property(name="ATT", default_value=3)
        aw.att_attr = 4
        self.assertEqual(aw.att_attr, 4)

    def test_creating_with_kwargs(self):
        aw = PropertyWrapper(one="one", two=2)
        self.assertEqual(aw.one, "one")
        self.assertEqual(aw.two, 2)

if __name__ == '__main__':
    unittest.main()

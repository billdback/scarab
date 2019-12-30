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

from scarab.rw import SimulationYAMLReader, SimulationWriter


TEST_SIMULATION_YAML = """
# Simulation YAML for testing IO.
simulation: test_sim
events:
  Event1:
    name: "event 1"
    attributes: [attr1_1, attr1_2]
  Event2:  # No interest in this event.
    name: "event 2"
    attributes: [attr2_1, attr2_2]
entities:
  Entity 1:  # bad class name.
    name: "entity-1"
    attributes:
      - size
      - width
      - height
    handlers:
      events: [time_update]
  Entity2:
    name: "entity-2"
    attributes: [color, location]
    # no handlers.
  Entity3:
    name: "entity-3"
    attributes: []
    handlers:
      events:
        - time_update
        - simulation_shutdown
        - "event 1"
        - "event3" # unknown event.
      entities:
        "entity-1": [created, changed]
        "entity-2": [updated, destroyed]  # bad state of updated - should be changed.
"""


class TestSimulationYAMLTranslator(unittest.TestCase):

    def test_read_yaml(self):
        """Reads the YAML from the test string and verifies it was parsed correctly."""
        sim_repr = SimulationYAMLReader().read_yaml_from_str(TEST_SIMULATION_YAML)
        self.assertIsNotNone(sim_repr)

        self.assertEqual("test_sim", sim_repr.name)
        self.assertEqual(3, len(sim_repr.entities.keys()))
        self.assertEqual(2, len(sim_repr.events.keys()))

        self.assertIn("Entity 1", sim_repr.entities.keys())
        entity = sim_repr.entities["Entity 1"]
        self.assertEqual("Entity 1", entity.class_name)
        self.assertEqual("entity-1", entity.entity_name)
        self.assertIsNotNone(entity)
        self.assertIn("size", entity.attributes)
        self.assertIn("width", entity.attributes)
        self.assertIn("height", entity.attributes)
        self.assertFalse(entity.entity_handlers)
        self.assertFalse(entity.event_handlers)
        self.assertTrue(entity.time_update_handler)
        self.assertFalse(entity.simulation_shutdown_handler)

        self.assertIn("Entity2", sim_repr.entities.keys())
        entity = sim_repr.entities["Entity2"]
        self.assertIsNotNone(entity)
        self.assertEqual("Entity2", entity.class_name)
        self.assertEqual("entity-2", entity.entity_name)
        self.assertIn("color", entity.attributes)
        self.assertIn("location", entity.attributes)
        self.assertFalse(entity.entity_handlers)
        self.assertFalse(entity.event_handlers)
        self.assertFalse(entity.time_update_handler)
        self.assertFalse(entity.simulation_shutdown_handler)

        self.assertIn("Entity3", sim_repr.entities.keys())
        entity = sim_repr.entities["Entity3"]
        self.assertIsNotNone(entity)
        self.assertEqual("Entity3", entity.class_name)
        self.assertEqual("entity-3", entity.entity_name)
        self.assertFalse(entity.attributes)
        self.assertIn("created", entity.entity_handlers["entity-1"])
        self.assertIn("changed", entity.entity_handlers["entity-1"])
        self.assertIn("updated", entity.entity_handlers["entity-2"])
        self.assertIn("destroyed", entity.entity_handlers["entity-2"])
        self.assertIn("event 1", entity.event_handlers)
        self.assertIn("event3", entity.event_handlers)
        self.assertTrue(entity.time_update_handler)
        self.assertTrue(entity.simulation_shutdown_handler)

        self.assertIn("Event1", sim_repr.events.keys())
        event = sim_repr.events["Event1"]
        self.assertIsNotNone(event)
        self.assertEqual("Event1", event.class_name)
        self.assertEqual("event 1", event.event_name)
        self.assertIn("attr1_1", event.attributes)
        self.assertIn("attr1_2", event.attributes)

        self.assertIn("Event2", sim_repr.events.keys())
        event = sim_repr.events["Event2"]
        self.assertIsNotNone(event)
        self.assertEqual("Event2", event.class_name)
        self.assertEqual("event 2", event.event_name)
        self.assertIn("attr2_1", event.attributes)
        self.assertIn("attr2_2", event.attributes)

    def test_read_yaml_from_file(self):
        """Tests reading from a file.  Parsing is tested elsewhere."""
        yaml_translator = SimulationYAMLReader()
        self.assertIsNone(yaml_translator.yaml)

        yaml_translator.read_yaml_from_file("../examples/beehive.yaml")
        self.assertIsNotNone(yaml_translator.yaml)

    def test_review_of_issues(self):
        """Tests that validation catches errors."""
        sim_repr = SimulationYAMLReader().read_yaml_from_str(TEST_SIMULATION_YAML)

        issues = sim_repr.check_for_issues()

        self.assertEqual(4, len(issues))


class TestSimulationWriter(unittest.TestCase):
    """Tests writing simulation representations to Python."""

    def test_writing_simulation(self):
        """Tests writing the simulation to a file."""
        sim_repr = SimulationYAMLReader().read_yaml_from_str(TEST_SIMULATION_YAML)

        # get rid of the badly named class.
        e1 = sim_repr.entities["Entity 1"]
        del(sim_repr.entities["Entity 1"])
        e1.class_name = "Entity1"
        sim_repr.add_entity(e1)

        sim_writer = SimulationWriter()
        sim_writer.write_simulation_module(simulation_repr=sim_repr)


if __name__ == '__main__':
    unittest.main()

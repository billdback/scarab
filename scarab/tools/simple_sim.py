"""
Copyright (c) 2024 William D Back

This file is part of Scarab licensed under the MIT License.
For full license text, see the LICENSE file in the project root.

This is a simple simulation that generates events for the controller to see.  It has entities that watch each other and
constantly update to cause events to be generated every cycle.
"""

import argparse
from scarab.framework.entity import Entity, entity_created, entity_changed
from scarab.framework.entity import EntityCreatedEvent, EntityChangedEvent
from scarab.framework.simulation.simulation import Simulation


@Entity(name="basic-entity")
class SimpleEntity:
    """Simple entity to monitor other entities of the same type."""

    def __init__(self, name):
        """Creates a new basic entity"""
        self.name = name
        self.number_entities = 0  # tracks the number of known entities.
        self.entity_changes = 0  # tracks the number of change events seen.

    # noinspection PyUnusedLocal
    @entity_created(entity_name="basic-entity")
    def basic_entity_create(self, evt: EntityCreatedEvent):
        """Just track the number of basic entities."""
        self.number_entities += 1

    # noinspection PyUnusedLocal
    @entity_changed(entity_name="basic-entity")
    def basic_entity_changed(self, evt: EntityChangedEvent):
        """Track the number of changes seen."""
        self.number_entities += 1


def main():
    """
    Main entry point for the simple simulation.
    Parses command line arguments and runs the simulation.
    """
    parser = argparse.ArgumentParser(description='Run a simple simulation with basic entities.')
    parser.add_argument('--host', default='localhost', help='WebSocket host (default: localhost)')
    parser.add_argument('--port', type=int, default=1234, help='WebSocket port (default: 1234)')
    parser.add_argument('--steps', type=int, default=10, help='Number of simulation steps (default: 10)')
    parser.add_argument('--step-length', type=int, default=5, help='Length of each step in milliseconds (default: 5)')
    parser.add_argument('--entities', type=int, default=10, help='Number of entities to create (default: 10)')
    args = parser.parse_args()

    with Simulation(ws_host=args.host, ws_port=args.port) as sim:
        for i in range(0, args.entities):
            sim.add_entity(SimpleEntity(name="basic-entity" + str(i)))

        sim.run(nbr_steps=args.steps, step_length=args.step_length)


if __name__ == "__main__":
    main()

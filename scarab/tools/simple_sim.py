"""
Copyright (c) 2024 William D Back

This file is part of Scarab licensed under the MIT License.
For full license text, see the LICENSE file in the project root.

This is a simple simulation that generates events for the controller to see.  It has entities that watch each other and
constantly update to cause events to be generated every cycle.
"""

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

    @entity_created(entity_name="basic-entity")
    def basic_entity_create(self, evt: EntityCreatedEvent):
        """Just track the number of basic entities."""
        self.number_entities += 1

    @entity_changed(entity_name="basic-entity")
    def basic_entity_changed(self, evt: EntityChangedEvent):
        """Track the number of changes seen."""
        self.number_entities += 1


with Simulation(ws_host='localhost', ws_port=1234) as sim:
    for i in range(0, 10):
        sim.add_entity(SimpleEntity(name="basic-entity" + str(i)))

    sim.run(nbr_steps=10, step_length=5)

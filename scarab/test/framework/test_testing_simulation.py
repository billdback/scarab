"""
Copyright (c) 2024 William D Back

This file is part of Scarab licensed under the MIT License.
For full license text, see the LICENSE file in the project root.

Tests for the testing simulation module.
"""
import pytest
from typing import Dict

from scarab.framework.entity import Entity, scarab_properties
from scarab.framework.entity import entity_created, entity_changed, entity_destroyed
from scarab.framework.entity import simulation_start, simulation_pause, simulation_resume, simulation_shutdown
from scarab.framework.entity import time_updated, event
from scarab.framework.events import Event, EntityCreatedEvent, EntityChangedEvent, EntityDestroyedEvent
from scarab.framework.events import SimulationStartEvent, SimulationPauseEvent, SimulationResumeEvent, SimulationShutdownEvent
from scarab.framework.events import TimeUpdatedEvent
from scarab.framework.testing.simulation import Simulation
from scarab.framework.types import SimID


# Test entity for use in tests
@Entity(name='test_entity')
class TestEntity:
    """A simple entity for testing."""

    def __init__(self):
        self.scarab_id = None
        self.scarab_name = 'test_entity'
        self.prop1 = 'initial_value'
        self.event_received = False
        self.time = 0
        self.simulation_running = False

    @entity_created(entity_name='test_entity')
    def entity_created(self, event: EntityCreatedEvent):
        """Handler for entity created events."""
        self.event_received = True

    @entity_changed(entity_name='test_entity')
    def entity_changed(self, event: EntityChangedEvent):
        """Handler for entity changed events."""
        self.event_received = True

    @entity_destroyed(entity_name='test_entity')
    def entity_destroyed(self, event: EntityDestroyedEvent):
        """Handler for entity destroyed events."""
        self.event_received = True

    @simulation_start()
    def sim_start(self, event: SimulationStartEvent):
        """Handler for simulation start events."""
        self.simulation_running = True
        self.start_received = True

    @simulation_pause()
    def sim_pause(self, event: SimulationPauseEvent):
        """Handler for simulation pause events."""
        self.simulation_running = False
        self.pause_received = True

    @simulation_resume()
    def sim_resume(self, event: SimulationResumeEvent):
        """Handler for simulation resume events."""
        self.simulation_running = True
        self.resume_received = True

    @simulation_shutdown()
    def sim_shutdown(self, event: SimulationShutdownEvent):
        """Handler for simulation shutdown events."""
        self.simulation_running = False
        self.shutdown_received = True

    @time_updated()
    def time_updated(self, event: TimeUpdatedEvent):
        """Handler for time update events."""
        self.time = event.sim_time

    @event(name='test_event')
    def handle_test_event(self, event: Event):
        """Handler for test events."""
        self.event_received = True


def test_simulation_init():
    """Test initializing the test simulation."""
    sim = Simulation()
    assert isinstance(sim._entities, Dict)
    assert len(sim._entities) == 0
    assert sim._event_router is not None


def test_add_id():
    """Test adding an ID to an entity."""
    entity = TestEntity()
    assert entity.scarab_id is None

    Simulation.add_id(entity)
    assert entity.scarab_id is not None


def test_add_entity():
    """Test adding an entity to the simulation."""
    sim = Simulation()
    entity = TestEntity()

    sim.add_entity(entity)
    assert entity.scarab_id is not None
    assert entity.scarab_id in sim._entities
    assert sim._entities[entity.scarab_id] == entity


def test_send_entity_created_event():
    """Test sending an entity created event."""
    sim = Simulation()
    entity = TestEntity()
    entity.event_received = False

    sim.add_entity(entity)

    # Create another entity and send an event for it
    entity2 = TestEntity()
    entity2.scarab_id = 'test_id'

    sim.send_entity_created_event(entity2)
    assert entity.event_received


def test_send_entity_changed_event():
    """Test sending an entity changed event."""
    sim = Simulation()
    entity = TestEntity()
    entity.event_received = False

    sim.add_entity(entity)

    # Create another entity and send a changed event for it
    entity2 = TestEntity()
    entity2.scarab_id = 'test_id'
    entity2.prop1 = 'changed_value'

    sim.send_entity_changed_event(entity2, ['prop1'])
    assert entity.event_received


def test_send_entity_destroyed_event():
    """Test sending an entity destroyed event."""
    sim = Simulation()
    entity = TestEntity()
    entity.event_received = False

    sim.add_entity(entity)

    # Create another entity and send a destroyed event for it
    entity2 = TestEntity()
    entity2.scarab_id = 'test_id'

    sim.send_entity_destroyed_event(entity2)
    assert entity.event_received


def test_send_simulation_events():
    """Test sending simulation events."""
    sim = Simulation()
    entity = TestEntity()

    sim.add_entity(entity)

    # Send simulation events
    sim.send_simulation_start_event()
    assert hasattr(entity, 'start_received') and entity.start_received

    sim.send_simulation_pause_event()
    assert hasattr(entity, 'pause_received') and entity.pause_received

    sim.send_simulation_resume_event()
    assert hasattr(entity, 'resume_received') and entity.resume_received

    sim.send_simulation_shutdown_event()
    assert hasattr(entity, 'shutdown_received') and entity.shutdown_received


def test_send_time_updated():
    """Test sending time updated events."""
    sim = Simulation()
    entity = TestEntity()
    entity.time = 0

    sim.add_entity(entity)

    # Send time updated event
    sim.send_simulation_time_updated(sim_time=10)
    assert entity.time == 10


def test_send_generic_event():
    """Test sending a generic event."""
    sim = Simulation()
    entity = TestEntity()
    entity.event_received = False

    sim.add_entity(entity)

    # Send a generic event
    test_event = Event(event_name='test_event')
    sim.send_event(test_event)
    assert entity.event_received

"""
Copyright (c) 2024 William D Back

This file is part of Scarab licensed under the MIT License.
For full license text, see the LICENSE file in the project root.

Test the Scarab events classes.
"""

from scarab.framework.events import *
from scarab.framework.entity import scarab_properties
from .test_items import TestEntity2


def test_event_names():
    """Simple test mostly to verify that the event constants are seen."""
    assert ScarabEventType.ENTITY_CREATED.value == "scarab.entity.created"
    assert ScarabEventType.ENTITY_CHANGED.value == "scarab.entity.changed"
    assert ScarabEventType.ENTITY_DESTROYED.value == "scarab.entity.destroyed"
    assert ScarabEventType.TIME_UPDATED.value == "scarab.time.updated"

    # and make sure the types get converted properly.
    assert "scarab.entity.created" in standard_event_names
    assert "scarab.simulation.start" in standard_event_names
    assert "scarab.named-event" in standard_event_names


def test_base_event():
    """Tests the base event."""
    evt = Event(event_name="test-event", sim_time=1)
    assert evt.event_name == 'test-event'
    assert evt.sim_time == 1


def test_entity_created_event():
    """Tests the event for creating entities."""
    test_entity = TestEntity2(prop3='prop3', prop4=4)
    evt = EntityCreatedEvent(sim_time=1, entity_props=scarab_properties(test_entity))

    assert evt.event_name == ScarabEventType.ENTITY_CREATED.value

    assert evt.sim_time == 1
    assert evt.entity.scarab_name == 'test2'
    assert evt.entity.prop3 == 'prop3'
    assert evt.entity.prop4 == 4


def test_entity_updated_event():
    """Tests the event for updating entities."""
    test_entity = TestEntity2(prop3='prop3', prop4=4)
    test_entity.prop3 = 'prop3-modified'

    evt = EntityChangedEvent(sim_time=1, entity_props=scarab_properties(test_entity), changed_props=['prop3'])
    assert evt.event_name == ScarabEventType.ENTITY_CHANGED.value

    assert evt.sim_time == 1
    assert evt.entity.scarab_name == 'test2'
    assert evt.entity.prop3 == 'prop3-modified'
    assert evt.entity.prop4 == 4

    assert evt.changed_properties == ['prop3']


def test_entity_destroyed_event():
    """Tests the event for updating destroying entities."""
    test_entity = TestEntity2(prop3='prop3', prop4=4)

    evt = EntityDestroyedEvent(sim_time=1, entity_props=scarab_properties(test_entity))
    assert evt.event_name == ScarabEventType.ENTITY_DESTROYED.value

    assert evt.sim_time == 1
    assert evt.entity.scarab_name == 'test2'
    assert evt.entity.prop3 == 'prop3'
    assert evt.entity.prop4 == 4


def test_simulation_start_event():
    """Tests the simulation start event."""
    evt = SimulationStartEvent(1)

    assert evt.event_name == ScarabEventType.SIMULATION_START.value
    assert evt.sim_time == 1


def test_simulation_pause_event():
    """Tests the simulation pause event."""
    evt = SimulationPauseEvent(1)

    assert evt.event_name == ScarabEventType.SIMULATION_PAUSE.value
    assert evt.sim_time == 1


def test_simulation_resume_event():
    """Tests the simulation resume event."""
    evt = SimulationResumeEvent(1)

    assert evt.event_name == ScarabEventType.SIMULATION_RESUME.value
    assert evt.sim_time == 1


def test_simulation_shutdown_event():
    """Tests the simulation shut down event."""
    evt = SimulationShutdownEvent(1)

    assert evt.event_name == ScarabEventType.SIMULATION_SHUTDOWN.value
    assert evt.sim_time == 1


def test_time_update_event():
    """Test time update event."""
    evt = TimeUpdatedEvent(sim_time=1, previous_time=0)
    assert evt.event_name == ScarabEventType.TIME_UPDATED.value
    assert evt.sim_time == 1
    assert evt.previous_time == 0

    # test with calculated previous time.
    evt = TimeUpdatedEvent(sim_time=4)
    assert evt.sim_time == 4
    assert evt.previous_time == 3


def test_convert_to_from_json():
    """Test converting to/from JSON."""
    # TODO add code to test.  The main issue is that SimpleNamespace can't be converted to JSON so the events that
    #  use it dont' work.
    entity = TestEntity2()

    # Base event
    evt = Event(event_name='test-event', sim_time=1)
    j = evt.to_json()
    assert j['event_name'] == 'test-event'
    assert j['sim_time'] == 1

    # Entity events
    evt = EntityCreatedEvent(entity_props=scarab_properties(entity))
    j = evt.to_json()
    assert j['event_name'] == ScarabEventType.ENTITY_CREATED.value
    assert j['entity']['scarab_name'] == 'test2'

    evt = EntityChangedEvent(entity_props=scarab_properties(entity), changed_props=['prop3'])
    j = evt.to_json()
    assert j['event_name'] == ScarabEventType.ENTITY_CHANGED.value
    assert j['entity']['scarab_name'] == 'test2'
    assert j['changed_properties'] == ['prop3']

    evt = EntityDestroyedEvent(entity_props=scarab_properties(entity))
    j = evt.to_json()
    assert j['event_name'] == ScarabEventType.ENTITY_DESTROYED.value
    assert j['entity']['scarab_name'] == 'test2'

    # Simulation events
    evt = SimulationStartEvent(sim_time=1)
    j = evt.to_json()
    assert j['event_name'] == ScarabEventType.SIMULATION_START.value
    assert j['sim_time'] == 1

    evt = SimulationPauseEvent(sim_time=2)
    j = evt.to_json()
    assert j['event_name'] == ScarabEventType.SIMULATION_PAUSE.value
    assert j['sim_time'] == 2

    evt = SimulationResumeEvent(sim_time=3)
    j = evt.to_json()
    assert j['event_name'] == ScarabEventType.SIMULATION_RESUME.value
    assert j['sim_time'] == 3

    evt = SimulationShutdownEvent(sim_time=4)
    j = evt.to_json()
    assert j['event_name'] == ScarabEventType.SIMULATION_SHUTDOWN.value
    assert j['sim_time'] == 4

    # Time update event
    evt = TimeUpdatedEvent(sim_time=2, previous_time=1)
    j = evt.to_json()
    assert j['event_name'] == ScarabEventType.TIME_UPDATED.value
    assert j['sim_time'] == 2
    assert j['previous_time'] == 1

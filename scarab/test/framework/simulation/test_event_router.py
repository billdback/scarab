"""
Copyright (c) 2024 William D Back

This file is part of Scarab licensed under the MIT License.
For full license text, see the LICENSE file in the project root.

Tests the event router module.
"""

from scarab.framework.entity import scarab_properties
# noinspection PyProtectedMember
from scarab.framework.simulation._event_router import EventRouter
from scarab.framework.events import EntityCreatedEvent, EntityDestroyedEvent, EntityChangedEvent, Event, \
    SimulationStartEvent, SimulationPauseEvent, SimulationResumeEvent, SimulationShutdownEvent, TimeUpdatedEvent

from scarab.test.framework.test_items import TestEntity1, TestEntity2


def test_event_router_entity_events():
    """Test event routing of handling entity create events."""

    router = EventRouter()

    entity1 = TestEntity1()
    assert entity1.nbr_test2_entities == 0

    router.register(entity=entity1)

    entity2 = TestEntity2()
    event = EntityCreatedEvent(sim_time=1, entity_props=scarab_properties(entity2))
    router.sync_route(event)

    assert entity1.nbr_test2_entities == 1

    entity2.prop3 = "prop3-updated"
    event = EntityChangedEvent(sim_time=2, entity_props=scarab_properties(entity2), changed_props=['prop3'])
    router.sync_route(event)
    assert entity1.nbr_test2_entities == 1
    assert entity1.test_entity_2.prop3 == "prop3-updated"

    event = EntityDestroyedEvent(sim_time=3, entity_props=scarab_properties(entity2))
    router.sync_route(event)
    assert entity1.nbr_test2_entities == 0


def test_event_router_simulation_events():
    """Tests routing of simulation events (start, pause, resume, stop, etc.)"""
    router = EventRouter()
    entity = TestEntity1()
    router.register(entity)

    assert not entity.simulation_running

    router.sync_route(SimulationStartEvent(sim_time=1))
    assert entity.simulation_running

    router.sync_route(SimulationPauseEvent(sim_time=1))
    assert not entity.simulation_running

    router.sync_route(SimulationResumeEvent(sim_time=1))
    assert entity.simulation_running

    router.sync_route(SimulationShutdownEvent(sim_time=1))
    assert not entity.simulation_running

    assert entity.simulation_time == 0
    router.sync_route(TimeUpdatedEvent(sim_time=3, previous_time=1))
    assert entity.simulation_time == 3


def test_event_router_generic_event():
    """Tests generic (named) event routing."""
    router = EventRouter()
    entity = TestEntity1()
    router.register(entity)

    assert entity.nbr_generic_events == 0
    router.sync_route(Event(sim_time=1, event_name='generic'))
    assert entity.nbr_generic_events == 1


def test_event_router_self_notification_filtering():
    """Tests that entities don't receive events about themselves."""
    router = EventRouter()

    # Create and register an entity
    entity1 = TestEntity1(prop1="test", prop2=42)
    entity1.scarab_id = "entity1-id"
    router.register(entity1)

    # Create another entity of the same type
    entity1b = TestEntity1(prop1="test-other", prop2=99)
    entity1b.scarab_id = "entity1b-id"

    # Send events about entity1 - these should be filtered out
    event = EntityCreatedEvent(sim_time=1, entity_props=scarab_properties(entity1))
    router.sync_route(event)
    assert entity1.nbr_self_created == 0, "Entity should not receive created events about itself"

    entity1.prop1 = "updated"
    event = EntityChangedEvent(sim_time=2, entity_props=scarab_properties(entity1), changed_props=['prop1'])
    router.sync_route(event)
    assert entity1.nbr_self_changed == 0, "Entity should not receive changed events about itself"

    event = EntityDestroyedEvent(sim_time=3, entity_props=scarab_properties(entity1))
    router.sync_route(event)
    assert entity1.nbr_self_destroyed == 0, "Entity should not receive destroyed events about itself"

    # Send events about entity1b - these should be received
    event = EntityCreatedEvent(sim_time=4, entity_props=scarab_properties(entity1b))
    router.sync_route(event)
    assert entity1.nbr_self_created == 1, "Entity should receive created events about other entities of same type"

    entity1b.prop1 = "updated-other"
    event = EntityChangedEvent(sim_time=5, entity_props=scarab_properties(entity1b), changed_props=['prop1'])
    router.sync_route(event)
    assert entity1.nbr_self_changed == 1, "Entity should receive changed events about other entities of same type"

    event = EntityDestroyedEvent(sim_time=6, entity_props=scarab_properties(entity1b))
    router.sync_route(event)
    assert entity1.nbr_self_destroyed == 1, "Entity should receive destroyed events about other entities of same type"


def test_event_router_unregister_entity():
    """Tests removing entities from the event router."""
    router = EventRouter()
    entity1 = TestEntity1()

    # by default the entities have no ID since it would be set by the simulation, but it's important for removing.
    entity1.scarab_id = "123"
    router.register(entity1)

    # route events and change state, then unregister, route events and make sure state doesn't change.
    entity2 = TestEntity2()
    event = EntityCreatedEvent(sim_time=1, entity_props=scarab_properties(entity2))
    router.sync_route(event)
    assert entity1.nbr_test2_entities == 1

    entity2.prop3 = "prop3-updated"
    event = EntityChangedEvent(sim_time=2, entity_props=scarab_properties(entity2), changed_props=['prop3'])
    router.sync_route(event)
    assert entity1.nbr_test2_entities == 1
    assert entity1.test_entity_2.prop3 == "prop3-updated"

    event = EntityDestroyedEvent(sim_time=3, entity_props=scarab_properties(entity2))
    router.sync_route(event)
    assert entity1.nbr_test2_entities == 0

    # Send simulation events.
    assert not entity1.simulation_running

    router.sync_route(SimulationStartEvent(sim_time=1))
    assert entity1.simulation_running

    router.sync_route(SimulationPauseEvent(sim_time=1))
    assert not entity1.simulation_running

    router.sync_route(SimulationResumeEvent(sim_time=1))
    assert entity1.simulation_running

    router.sync_route(SimulationShutdownEvent(sim_time=1))
    assert not entity1.simulation_running

    assert entity1.simulation_time == 0
    router.sync_route(TimeUpdatedEvent(sim_time=3, previous_time=1))
    assert entity1.simulation_time == 3

    assert entity1.nbr_generic_events == 0
    router.sync_route(Event(sim_time=1, event_name='generic'))
    assert entity1.nbr_generic_events == 1

    # now remove and re-send the same events and verify no changes.
    router.unregister(entity1)
    entity1.reset()

    event = EntityCreatedEvent(sim_time=1, entity_props=scarab_properties(entity2))
    router.sync_route(event)
    assert entity1.nbr_test2_entities == 0
    assert entity1.test_entity_2 is None

    entity2.prop3 = "prop3-updated"
    event = EntityChangedEvent(sim_time=2, entity_props=scarab_properties(entity2), changed_props=['prop3'])
    router.sync_route(event)
    assert entity1.nbr_test2_entities == 0
    assert entity1.test_entity_2 is None

    event = EntityDestroyedEvent(sim_time=3, entity_props=scarab_properties(entity2))
    router.sync_route(event)
    assert entity1.nbr_test2_entities == 0
    assert entity1.test_entity_2 is None

    assert not entity1.simulation_running

    router.sync_route(SimulationStartEvent(sim_time=1))
    assert not entity1.simulation_running

    router.sync_route(SimulationPauseEvent(sim_time=1))
    assert not entity1.simulation_running

    router.sync_route(SimulationResumeEvent(sim_time=1))
    assert not entity1.simulation_running

    router.sync_route(SimulationShutdownEvent(sim_time=1))
    assert not entity1.simulation_running

    assert entity1.simulation_time == 0
    router.sync_route(TimeUpdatedEvent(sim_time=3, previous_time=1))
    assert entity1.simulation_time == 0

    assert entity1.nbr_generic_events == 0
    router.sync_route(Event(sim_time=1, event_name='generic'))
    assert entity1.nbr_generic_events == 0

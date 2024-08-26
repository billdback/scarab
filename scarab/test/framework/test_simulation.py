"""
Tests the simulation and related functionality.
"""

from scarab.framework.entity import scarab_properties
from scarab.framework.simulation import EventRouter
from scarab.framework.events import EntityCreatedEvent, EntityDestroyedEvent, EntityUpdatedEvent, Event, \
    SimulationStartEvent, SimulationPauseEvent, SimulationResumeEvent, SimulationShutdownEvent, TimeUpdatedEvent

from .test_items import TestEntity1, TestEntity2


def test_event_router_entity_events():
    """Test event routing of handling entity create events."""

    router = EventRouter()

    entity1 = TestEntity1()
    assert entity1.nbr_test2_entities == 0

    router.register(entity=entity1)

    entity2 = TestEntity2()
    event = EntityCreatedEvent(sim_time=1, entity_props=scarab_properties(entity2))
    router.route(event)

    assert entity1.nbr_test2_entities == 1

    entity2.prop3 = "prop3-updated"
    event = EntityUpdatedEvent(sim_time=2, entity_props=scarab_properties(entity2), changed_props=['prop3'])
    router.route(event)
    assert entity1.nbr_test2_entities == 1
    assert entity1.test_entity_2.prop3 == "prop3-updated"

    event = EntityDestroyedEvent(sim_time=3, entity_props=scarab_properties(entity2))
    router.route(event)
    assert entity1.nbr_test2_entities == 0


def test_event_router_simulation_events():
    """Tests routing of simulation events (start, pause, resume, stop, etc."""
    router = EventRouter()
    entity = TestEntity1()
    router.register(entity)

    assert not entity.simulation_running

    router.route(SimulationStartEvent(sim_time=1))
    assert entity.simulation_running

    router.route(SimulationPauseEvent(sim_time=1))
    assert not entity.simulation_running

    router.route(SimulationResumeEvent(sim_time=1))
    assert entity.simulation_running

    router.route(SimulationShutdownEvent(sim_time=1))
    assert not entity.simulation_running

    assert entity.simulation_time == 0
    router.route(TimeUpdatedEvent(sim_time=3, previous_time=1))
    assert entity.simulation_time == 3


def test_event_router_generic_event():
    """Tests generic (named) event routing."""
    router = EventRouter()
    entity = TestEntity1()
    router.register(entity)

    assert entity.nbr_generic_events == 0
    router.route(Event(sim_time=1, event_name='generic'))
    assert entity.nbr_generic_events == 1

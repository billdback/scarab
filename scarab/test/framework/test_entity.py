"""
Tests the entity classes.
"""
import pytest

from scarab.framework.events import *

from scarab.framework.entity import scarab_properties, Entity
from scarab.framework.events import EntityCreatedEvent

from .test_items import TestEntity1, TestEntity2, Test2EntityType
from scarab.framework.types import ScarabException


def test_non_conforming_entity_create_with_defaults():
    """Tests creating an entity with default values."""

    entity = TestEntity1()

    assert entity.scarab_name == 'test1'
    assert entity.scarab_id is None
    assert entity.prop1 == ''
    assert entity.prop2 == 0


def test_non_conforming_entity_create():
    """Tests creating an entity."""

    @Entity(name='entity3', conforms_to=Test2EntityType)
    class TestEntity3:
        """Doesn't provide all the props."""

        def __init__(self):
            self.prop3 = "test-entity3"
            self.prop5 = 5

    with pytest.raises(ScarabException):
        entity = TestEntity3()


def test_conforming_entity_type():
    """Tests creating an entity that conforms to a type."""
    entity = TestEntity2(prop3='test str', prop4=16)

    assert entity.scarab_name == 'test2'
    assert entity.scarab_id is None
    assert entity.prop3 == 'test str'
    assert entity.prop4 == 16
    assert entity.prop5 == True


def test_conforming_entity_with_missing_properties():
    """Tests creating an entity that conforms to a type."""
    entity = TestEntity2(prop3='test str', prop4=16)

    assert entity.scarab_name == 'test2'
    assert entity.scarab_id is None
    assert entity.prop3 == 'test str'
    assert entity.prop4 == 16
    assert entity.prop5 == True


def test_scarab_props():
    """Tests creating an entity."""

    entity = TestEntity1(prop1='test str', prop2=16)

    props = scarab_properties(entity)

    assert props['scarab_name'] == 'test1'
    assert props['scarab_id'] is None
    assert props['prop1'] == 'test str'
    assert props['prop2'] == 16

    entity.prop1 = 'updated str'
    props = scarab_properties(entity)
    assert props['prop1'] == 'updated str'


def test_get_props():
    """Tests getting the scarab properties from an entity"""
    test2 = TestEntity2(prop3='prop3', prop4=4)
    props = scarab_properties(test2)
    ent = SimpleNamespace(**props)

    assert ent.scarab_name == 'test2'
    assert ent.prop3 == 'prop3'
    assert ent.prop4 == 4


def test_created_entity():
    """Test getting an entity created."""
    test1 = TestEntity1()
    test2 = TestEntity2(prop3="prop set")

    test1.entity_2_created(EntityCreatedEvent(sim_time=1, entity_props=scarab_properties(test2)))
    assert test1.nbr_test2_entities == 1
    assert test1.test_entity_2.prop3 == 'prop set'


def test_update_entity():
    """Test getting an entity updated."""
    test1 = TestEntity1()
    test2 = TestEntity2(prop3="prop updated")

    test1.entity_2_changed(
        EntityChangedEvent(sim_time=1, entity_props=scarab_properties(test2), changed_props=['prop3']))
    assert test1.test_entity_2.prop3 == 'prop updated'


def test_destroy_entity():
    """Test getting an entity destroyed."""
    test1 = TestEntity1()
    test2 = TestEntity2(prop3="prop")

    test1.entity_2_created(EntityCreatedEvent(sim_time=1, entity_props=scarab_properties(test2)))
    assert test1.nbr_test2_entities == 1
    assert test1.test_entity_2.prop3 == 'prop'

    test1.entity_2_destroyed(EntityDestroyedEvent(sim_time=1, entity_props=scarab_properties(test2)))
    assert test1.nbr_test2_entities == 0
    assert test1.test_entity_2 is None


def test_simulation_changes():
    """Tests getting simulation status changes."""
    test1 = TestEntity1()

    test1.simulation_start(SimulationStartEvent(sim_time=1))
    assert test1.simulation_running is True

    test1.simulation_pause(SimulationPauseEvent(sim_time=1))
    assert test1.simulation_running is False

    test1.simulation_resume(SimulationResumeEvent(sim_time=1))
    assert test1.simulation_running is True

    test1.simulation_shutdown(SimulationShutdownEvent(sim_time=1))
    assert test1.simulation_running is False


def test_time_update():
    """Tests calling time update."""
    test1 = TestEntity1()
    assert test1.simulation_time == 0

    test1.time_updated(TimeUpdatedEvent(sim_time=1))
    assert test1.simulation_time == 1


def test_generic_event():
    """Tests handling generic (named) events."""
    test1 = TestEntity1()
    assert test1.nbr_generic_events == 0

    test1.handle_generic(Event(event_name='generic', sim_time=1))
    assert test1.nbr_generic_events == 1

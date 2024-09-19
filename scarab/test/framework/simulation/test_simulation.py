"""
Tests the simulation and related functionality.
"""
import asyncio

import pytest

from scarab.framework.simulation.simulation import Simulation, SimulationState
from scarab.test.framework.test_items import TestEntity1, TestEntity2


def test_basic_simulation_events():
    """Tests simulation events for start, pause, resume, shutting down."""
    with Simulation() as sim:
        entity = TestEntity1()
        sim.add_entity(entity)

        sim.run(10)
        assert sim.state == SimulationState.paused
        assert entity.simulation_has_started is True
        assert entity.simulation_has_paused is True
        assert entity.simulation_time == 10

        sim.run(5)  # could also call simulation resume, but that's called by calling run again.
        assert entity.simulation_has_resumed is True
        assert entity.simulation_time == 15

        sim.shutdown()
        assert entity.simulation_time == 15

        with pytest.raises(RuntimeError):
            sim.run(3)


def test_entity_state_change_events():
    """Tests entities changing state during simulation execution."""
    with Simulation() as sim:
        entity1 = TestEntity1()
        sim.add_entity(entity1)
        entity2 = TestEntity2()
        sim.add_entity(entity2)

        sim.run(2)  # should be sufficient to get updates sent.

        assert "test_entity_2" in entity2.entity1_changed_props
        assert "nbr_test2_entities" in entity2.entity1_changed_props

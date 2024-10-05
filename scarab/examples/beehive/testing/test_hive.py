"""
Copyright (c) 2024 William D Back

This file is part of Scarab licensed under the MIT License.
For full license text, see the LICENSE file in the project root.

This file tests the hive entity.
"""
from typing import List

from scarab.framework.testing.simulation import Simulation

from scarab.examples.beehive.bee import Bee
from scarab.examples.beehive.hive import Hive
from scarab.examples.beehive.outside_temp import OutsideTemp


def create_test_bees(sim: Simulation) -> List[object]:
    """
    Create bees for testing.
    :param sim: The simulation to use for getting IDsThe simulation to use for getting IDs.
    :return: Nine bees total:
    * 3 are doing nothing
    * 2 are buzzing
    * 4 are flapping
    """

    # actual temps don't matter for this test, so just pick a couple for all bees.
    low_temp = 32  # F freezing
    high_temp = 85  # F warm

    # Create 9 bees
    bees = [
        sim.add_id(Bee(low_temp, high_temp)),
        sim.add_id(Bee(low_temp, high_temp)),
        sim.add_id(Bee(low_temp, high_temp)),
        sim.add_id(Bee(low_temp, high_temp)),
        sim.add_id(Bee(low_temp, high_temp)),
        sim.add_id(Bee(low_temp, high_temp)),
        sim.add_id(Bee(low_temp, high_temp)),
        sim.add_id(Bee(low_temp, high_temp)),
        sim.add_id(Bee(low_temp, high_temp)),
    ]

    # set the state of each of the bees with three in each state.
    # three have no changes.

    # two are buzzing
    for bee_cnt in range(4, 6):
        bees[bee_cnt - 1].isBuzzing = True

    # four are flapping
    for bee_cnt in range(6, 10):
        bees[bee_cnt - 1].isFlapping = True

    return bees


def test_bee_states():
    """Test adding bees in different states."""

    sim = Simulation()
    bees = create_test_bees(sim)

    hive = Hive()
    sim.add_entity(hive)
    for bee in bees:
        sim.send_entity_created_event(entity=bee)

    assert hive.number_of_bees == len(bees)
    assert hive.number_of_bees_buzzing == 2
    assert hive.number_of_bees_flapping == 4

    # now change some bee states and verify.
    bees[0].isBuzzing = True
    sim.send_entity_changed_event(entity=bees[0], changed_props=["isBuzzing"])
    bees[1].isFlapping = True
    sim.send_entity_changed_event(entity=bees[1], changed_props=["isFlapping"])

    assert hive.number_of_bees == len(bees)
    assert hive.number_of_bees_buzzing == 3
    assert hive.number_of_bees_flapping == 5

    # now change them back and verify.
    bees[0].isBuzzing = False
    sim.send_entity_changed_event(entity=bees[0], changed_props=["isBuzzing"])
    bees[1].isFlapping = False
    sim.send_entity_changed_event(entity=bees[1], changed_props=["isFlapping"])

    assert hive.number_of_bees == len(bees)
    assert hive.number_of_bees_buzzing == 2
    assert hive.number_of_bees_flapping == 4

    # now remove a few bees and verify that the state is still good.
    sim.send_entity_destroyed_event(bees[0])  # doing nothing
    sim.send_entity_destroyed_event(bees[5])  # buzzing
    sim.send_entity_destroyed_event(bees[8])  # flapping

    assert hive.number_of_bees == len(bees)
    assert hive.number_of_bees_buzzing == 2
    assert hive.number_of_bees_flapping == 4


def test_hive_without_bees():
    """Tests the hive entity with no bees.  The hive temp will change only based on the outside temp."""
    sim = Simulation()
    hive = Hive()
    sim.add_entity(hive)

    # first add a new outside temp and verify that the hive adopts that as the starter temp.
    outside_temp = sim.add_id(OutsideTemp(min_temp=50, max_temp=100))

    # outside_temp starts at the minimum and the hive them will get the current temp from the outside.
    sim.send_entity_created_event(entity=outside_temp)
    assert hive.current_temp == 50

    # when the outside temp changes, the hive temp will change to match, but be adjusted by bees.  Since there
    # are no bees, that means it always matches the outside temp.
    outside_temp.current_temp = 75
    sim.send_entity_changed_event(entity=outside_temp, changed_props=["current_temp"])
    assert hive.current_temp == 75

    outside_temp.current_temp = 95
    sim.send_entity_changed_event(entity=outside_temp, changed_props=["current_temp"])
    assert hive.current_temp == 95


def test_hive_with_bees():
    """Tests the hive entity with bees in different states and getting temp updates."""

    sim = Simulation()
    bees = create_test_bees(sim)

    hive = Hive()
    sim.add_entity(hive)
    for bee in bees:
        sim.send_entity_created_event(entity=bee)

    # outside_temp starts at the minimum and the hive them will get the current temp from the outside.
    outside_temp = sim.add_id(OutsideTemp(min_temp=50, max_temp=100))
    sim.send_entity_created_event(entity=outside_temp)
    assert hive.current_temp == 50

    # when the outside temp is updated, the hive temp will move to the outside temp and be adjust for the bee behavior.
    # the bee effect for flapping and buzzing will be included.
    outside_temp.current_temp = 60
    sim.send_entity_changed_event(entity=outside_temp, changed_props=["current_temp"])

    calculated_temp = 60 + (hive.buzzing_impact * hive.number_of_bees_buzzing) + (
            hive.flapping_impact * hive.number_of_bees_flapping)
    assert hive.current_temp == round(calculated_temp, 1)

"""
Copyright (c) 2024 William D Back

This file is part of Scarab licensed under the MIT License.
For full license text, see the LICENSE file in the project root.

This file tests the bee entity.
"""

from scarab.framework.testing.simulation import Simulation

from scarab.examples.beehive.bee import Bee
from scarab.examples.beehive.hive import Hive


def test_hive_created() -> None:
    """
    Tests when a hive is created to see changes in Bee state.
    """
    bee1 = Bee(low_temp=0, high_temp=10)
    bee2 = Bee(low_temp=6, high_temp=10)
    bee3 = Bee(low_temp=0, high_temp=4)

    test_sim = Simulation()

    test_sim.add_entity(bee1)
    test_sim.add_entity(bee2)
    test_sim.add_entity(bee3)

    # verify that bees aren't buzzing or flapping.
    assert not bee1.isBuzzing
    assert not bee1.isFlapping

    assert not bee2.isBuzzing
    assert not bee2.isFlapping

    assert not bee3.isBuzzing
    assert not bee3.isFlapping

    # now create a hive and see how bees respond.
    hive = Hive()
    hive.current_temp = 5

    test_sim.send_entity_created_event(hive)

    # now see what happened to the bees.
    assert not bee1.isBuzzing
    assert not bee1.isFlapping

    assert bee2.isBuzzing
    assert not bee2.isFlapping

    assert not bee3.isBuzzing
    assert bee3.isFlapping


def test_hive_changed() -> None:
    """
    Tests when a hive is updated to see changes in Bee state.
    """
    bee1 = Bee(low_temp=0, high_temp=10)
    bee2 = Bee(low_temp=6, high_temp=10)
    bee3 = Bee(low_temp=0, high_temp=4)

    test_sim = Simulation()

    test_sim.add_entity(bee1)
    test_sim.add_entity(bee2)
    test_sim.add_entity(bee3)

    # verify that bees aren't buzzing or flapping.
    assert not bee1.isBuzzing
    assert not bee1.isFlapping

    assert not bee2.isBuzzing
    assert not bee2.isFlapping

    assert not bee3.isBuzzing
    assert not bee3.isFlapping

    # now create a hive and see how bees respond.
    hive = Hive()
    hive.current_temp = 5

    test_sim.send_entity_changed_event(hive, changed_props=['temperature'])

    # now see what happened to the bees.
    assert not bee1.isBuzzing
    assert not bee1.isFlapping

    assert bee2.isBuzzing
    assert not bee2.isFlapping

    assert not bee3.isBuzzing
    assert bee3.isFlapping

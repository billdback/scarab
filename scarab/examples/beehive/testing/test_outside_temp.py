"""
Copyright (c) 2024 William D Back

This file is part of Scarab licensed under the MIT License.
For full license text, see the LICENSE file in the project root.

This file tests the outside temperature entity.
"""

from scarab.framework.testing.simulation import Simulation

from scarab.examples.beehive.outside_temp import OutsideTemp, TimeConstants


def test_outside_temp():
    """Just logs the temps at different times for visual viewing."""
    min_temp = 10
    max_temp = 80

    sim = Simulation()
    outside_temp = OutsideTemp(min_temp, max_temp)
    sim.add_entity(outside_temp)

    for t in range(144):
        sim.send_simulation_time_updated(sim_time=t)
        print(f'({t * 10}) Temperature: {outside_temp.current_temp}')


def test_outside_temp_from_time_updates():
    """Tests updating the outside temperature when time changes."""

    # make the min and max match the minutes for easy calculations.
    min_temp = 10
    max_temp = 80

    sim = Simulation()
    outside_temp = OutsideTemp(min_temp, max_temp)
    sim.add_entity(outside_temp)

    # send 2am and the temp should be at the minimum.
    sim.send_simulation_time_updated(sim_time=TimeConstants.TWO_AM_MINUTES/10)
    assert outside_temp.current_temp == min_temp

    # send two pm and make sure it's at the max.
    sim.send_simulation_time_updated(sim_time=TimeConstants.TWO_PM_MINUTES/10)
    assert outside_temp.current_temp == max_temp

"""
The beehive simulator represents a very simplistic view of bees warming and cooling the hive.
As the temperature heats up, the bees will start to get warm and start flapping to cool.  As the
hive gets cool, the bees will start to buzz and warm the hive.  The goal is to keep the hive in a
comfortable range.

Of importance, there are two ways to have the bees respond. The first is to have all bees flap or
buzz at the same temperature.  As you will see, this leads to sudden increase and decreate in the temperatures.
The second way is for bees to vary like most populations do, meaning that they will start buzzing or flapping at
different temperatures.  What you will see is a more leveled temperature.

FUTURE: allow the settings to come from a config file.
"""

import numpy as np

from scarab.framework.simulation.simulation import Simulation

from scarab.examples.beehive.bee import Bee
from scarab.examples.beehive.hive import Hive
from scarab.examples.beehive.outside_temp import OutsideTemp


def run_sim() -> None:
    """
    Runs the simulation.
    """

    with Simulation() as sim:
        sim.add_entity(OutsideTemp(min_temp=50.0, max_temp=80.0))
        sim.add_entity(Hive())

        nbr_bees = 100

        # get random numbers in a normal distribution and set the be values.
        # for normal dist, loc == stddev, scale == stddev, size == number of values
        min_temps = np.random.normal(loc=60, scale=6, size=nbr_bees)
        max_temps = np.random.normal(loc=60, scale=6, size=nbr_bees)

        for _ in range(nbr_bees):
            bee = Bee(low_temp=min_temps[_], high_temp=max_temps[_])
            sim.add_entity(bee)

        sim.run(nbr_steps=100, step_length=3)


if __name__ == "__main__":
    run_sim()

"""
Copyright (c) 2024 William D Back

This file is part of Scarab licensed under the MIT License.
For full license text, see the LICENSE file in the project root.

The beehive simulator represents a very simplistic view of bees warming and cooling the hive.
As the temperature heats up, the bees will start to get warm and start flapping to cool.  As the
hive gets cool, the bees will start to buzz and warm the hive.  The goal is to keep the hive in a
comfortable range.

Of importance, there are two ways to have the bees respond. The first is to have all bees flap or
buzz at the same temperature.  As you will see, this leads to sudden increase and decreate in the temperatures.
The second way is for bees to vary like most populations do, meaning that they will start buzzing or flapping at
different temperatures.  What you will see is a more leveled temperature.
"""

import argparse
import numpy as np
import toml
from typing import Dict

from scarab.framework.simulation.simulation import Simulation

from scarab.examples.beehive.bee import Bee
from scarab.examples.beehive.hive import Hive
from scarab.examples.beehive.outside_temp import OutsideTemp


def parse_toml(toml_file_path) -> Dict:
    """
    Parses the toml file to extract the arguments for the sim.
    See the example.toml file for the settings that are expected.
    :param toml_file_path: The path to the TOML file.
    """
    with open(toml_file_path, 'r') as f:
        data = toml.loads(f.read())
    return data


def run_sim(params: Dict) -> None:
    """
    Runs the simulation.
    """

    with Simulation() as sim:
        try:
            sim.add_entity(OutsideTemp(min_temp=params['outside_temp']['min_temperature'],
                                       max_temp=params['outside_temp']['max_temperature']))
            sim.add_entity(Hive())

            nbr_bees = params['bees']['number_bees']
            vary = params['bees']['vary_tolerance']
            temp_average = params['bees']['temp_average']
            temp_std_dev = params['bees']['temp_std_dev']

            if vary:
                # get random numbers in a normal distribution and set the be values.
                # for normal dist, loc == stddev, scale == stddev, size == number of values
                min_temps = np.random.normal(loc=60, scale=6, size=nbr_bees)
                max_temps = np.random.normal(loc=60, scale=6, size=nbr_bees)
            else: # all the same values.
                min_temps = [temp_average - temp_std_dev] * nbr_bees
                max_temps = [temp_average + temp_std_dev] * nbr_bees

            for _ in range(nbr_bees):
                bee = Bee(low_temp=min_temps[_], high_temp=max_temps[_])
                sim.add_entity(bee)

            sim.run(nbr_steps=params['sim']['number_steps'], step_length=params['sim']['step_length'])
        except KeyError as ke:
            print(f"Parameter key error: {ke}.  Fix the config file and try again.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BeeHive simulation parameters")
    parser.add_argument('config', metavar='TOML file',
                        type=str, help='TOML file with behive configuration.')
    args = parser.parse_args()

    params = parse_toml(toml_file_path=args.config)

    run_sim(params=params)

"""
Copyright (C) 2019 William D. Back

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Command line version of beehive that writes the output to the terminal.
"""

import argparse
import random

from scarab.examples.beehive import *
from scarab.loggers import StdOutLogger
from scarab.simulation import Simulation, SIMULATION_LOGGING, EVENT_LOGGING, ENTITY_LOGGING

StdOutLogger(topics=SIMULATION_LOGGING)
# StdOutLogger(topics=EVENT_LOGGING)
# StdOutLogger(topics=ENTITY_LOGGING)


class BeehiveApp:
    """Controls the command line version of the beehive simulation."""

    def __init__(self):
        """
        Creates a new beehive display.
        """
        self.display_model = None

    def main(self):
        """Runs the application."""
        args = BeehiveApp.get_args()

        print("Running the beehive simulation.")
        print(args)

        with Simulation(name="beehive", time_stepped=True, minimum_step_time=args.step_length) as simulation:

            # pick some arbitrary values.
            buzzing_impact = 0.5
            fanning_impact = 0.5
            min_outside_temp = 50.0
            max_outside_temp = 90.0
            target_bee_buzzing = 60.0  # warm up
            target_bee_fanning = 65.0  # cool down

            simulation.add_entity(Beehive(start_temp=target_bee_buzzing,
                                          buzzing_impact=buzzing_impact, fanning_impact=fanning_impact))
            simulation.add_entity(OutsideTemperature(min_temp=min_outside_temp, max_temp=max_outside_temp))
            self.display_model = BeehiveDisplayModel()
            simulation.add_entity(self.display_model)

            # create and add the bees
            for bee_number in range(0, args.number_bees):
                # if the variance is "same", then all bees get the same fan and flap temps.  If not, vary randomly.
                if args.bee_variance == "vary":
                    bee_fan = random.uniform(target_bee_fanning * .9, target_bee_fanning * 1.1)
                    bee_buzz = random.uniform(target_bee_buzzing * .9, target_bee_buzzing * 1.1)
                    simulation.add_entity(Bee(fan_temp=bee_fan, buzz_temp=bee_buzz))
                else:
                    simulation.add_entity(Bee(fan_temp=target_bee_fanning, buzz_temp=target_bee_buzzing))

            step_size = 100
            for step in range(1, args.max_steps, step_size):
                simulation.advance_and_wait(steps=step_size)
                self.update_display()

    @staticmethod
    def get_args():
        """
        Returns command line arguments.
        :return: The command line arguments for the simulation run.
        :rtype: argparse.Namespace
        """
        parser = argparse.ArgumentParser(description="Beehive simulation where bees respond to varying temperatures "
                                         "during the day to keep the hive in a particular range.  The goal of this "
                                         "simulation is to show how variations in populations lead to more "
                                         "graceful changes (temp regulation) vs. set values that cause extreme "
                                         "changes.")

        parser.add_argument("--step_length", type=int, default=0, help="length of simulation step in seconds")
        parser.add_argument("--number_bees", type=int, default=10, help="number of bees in the hive")
        parser.add_argument("--bee_variance", default="vary",
                            choices=["vary", "same"],
                            help="vary: bees have different temps for buzz and fan.\n"
                                 "same: bees have same temp for buzz and fan.")
        parser.add_argument("--max_steps", type=int, default=10080, help="Number of steps as minutes.")

        return parser.parse_args()

    def update_display(self):
        """
        Write output on the stats every update call.
        """

        print("=======================================")
        print(f"Update from time {self.display_model.previous_time} to {self.display_model.new_time}")

        print(f"Temperature status:")
        if not self.display_model or not self.display_model.outside_temp:
            print("\tunknown")
        else:
            print(f"\toutside temp: {self.display_model.outside_temp:.1f}"
                  f" (min: {self.display_model.min_outside_temp:.1f}"
                  f" max: {self.display_model.max_outside_temp:.1f})")
            print(f"\thive temp: {self.display_model.beehive.current_temp:.1f}"
                  f" (min: {self.display_model.min_hive_temp:.1f} max: {self.display_model.max_hive_temp:.1f})")

        print(f"Bees:")
        if not self.display_model or not self.display_model.beehive:
            print("\tunknown")
        else:
            print(f"\ttotal bees: {self.display_model.beehive.number_bees}"
                  f" (min: {self.display_model.min_number_bees} max: {self.display_model.max_number_bees})")
            print(f"\tbees buzzing: {self.display_model.beehive.number_bees_buzzing}"
                  f" (min: {self.display_model.min_number_bees_buzzing}"
                  f" max: {self.display_model.max_number_bees_buzzing})")
            print(f"\tbees fanning: {self.display_model.beehive.number_bees_fanning}"
                  f" (min: {self.display_model.min_number_bees_fanning}"
                  f" max: {self.display_model.max_number_bees_fanning})")
        print("")


if __name__ == "__main__":
    beehive_app = BeehiveApp()
    beehive_app.main()


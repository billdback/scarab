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

Simple benchmark to see how the simulation changes impact performance over time.  This should be rerun and documented
after any major updates to the system.
"""

import time

from scarab.simulation import Simulation
from scarab.entities import *


class BenchmarkEntity(Entity):
    """Simple entity that requests updates on other entities.  The entities will express interest in number of
    changes for other entities.  Since this value increases with each entity, the results will grow exponentially.
    """

    def __init__(self):
        """Creates a new benchmark entitiy."""
        self.number_known_entities = 0
        self.number_entity_updates = 0
        super().__init__(name="benchmark-entity")

    @entity_created_event_handler(entity_name="benchmark-entity")
    def handle_other_entity(self, entity):
        """
        Handles another entity being created.
        :param entity: The entity that was created.
        :type entity: BenchmarkEntity
        :return: None
        """
        assert entity
        self.number_known_entities += 1

    @entity_changed_event_handler(entity_name="benchmark-entity")
    def handle_other_entity(self, entity, props):
        """
        Handles another entity being created.
        :param entity: The entity that was created.
        :type entity: BenchmarkEntity
        :param props: Properties that changed.
        :type props: dict[str: str]
        :return: None
        """
        assert entity
        self.number_entity_updates += 1


class StopwatchEntity(Entity):
    """Simple entity to print out the simulation time in increments."""

    def __init__(self, show_frequency):
        self.show_frequency = show_frequency
        super().__init__(name="benchmark-stopwatch")

    @time_update_event_handler
    def handle_new_time(self, prev_time, new_time):
        if not (new_time % self.show_frequency):
            print(f"{new_time}")


if __name__ == "__main__":
    """Run the benchmark test."""
    number_entities = 100
    number_cycles = 1000

    start_time = time.time()

    simulation = Simulation(name="simple benchmark", time_stepped=True)
    print(f"Benchmarking scarab ...")
    simulation.add_entity(StopwatchEntity(show_frequency=number_cycles/10))

    print(f"... creating entities")
    for nbr in range(0, number_entities):
        simulation.add_entity(BenchmarkEntity())

    print(f"... advancing simulation {number_cycles} cycles")
    simulation.advance(number_cycles)

    end_time = time.time()
    print(f"The benchmark simulation took {(end_time - start_time):.2f} seconds for {number_entities} entities "
          f"running for {number_cycles} cycles.")


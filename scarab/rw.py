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

This modules contains I/O classes for reading and writing simulations (including source and saves).
"""

from copy import copy
import re
from typing import List, Union
import yaml

from scarab.util import ind


class EventRepr:
    """Represents an event."""

    def __init__(self, class_name, event_name, attributes):
        """
        Creates new event representation.
        :param str class_name: Name of the event.
        :param str event_name: Name of the event.
        :param list of str attributes: List of attribute names.
        """
        assert class_name
        assert event_name

        self.class_name = class_name
        self.event_name = event_name
        self.attributes = list()
        if attributes:  # attributes are optional
            assert isinstance(attributes, list)
            self.attributes = copy(attributes)


class EntityRepr:
    """Represents an entity."""

    def __init__(self, class_name, entity_name, attributes):
        """
        Creates new entity representation.
        :param str class_name: Name of the entity.
        :param str entity_name: Name of the entity.
        :param list of str attributes: List of attribute names.
        """
        assert class_name
        assert entity_name

        self.class_name = class_name
        self.entity_name = entity_name
        self.attributes = list()
        if attributes:  # note that attributes are optional.
            assert isinstance(attributes, list)
            self.attributes = copy(attributes)

        self.entity_handlers = {}  # entity specific handlers.
        self.event_handlers = []  # list of events that are handled.

        # Special events.
        self.time_update_handler = False  # True if handles time updates.
        self.simulation_shutdown_handler = False  # True if handles simulation shutdown events.


class SimulationRepr:
    """Represents a simulation."""

    def __init__(self, name):
        """
        Creates a new simulation representation.
        :param str name:  The name of the simulation.
        """
        assert name

        self.name = name
        self.events = {}  # event.class_name: EventRepr
        self.entities = {}  # entity.class_name: EntityRepr

    def add_event(self, event) -> None:
        """
        Adds an event to the simulation.  Overwrites if there is an event with the given class name already.
        :param EventRepr event: The event to add.
        """
        self.events[event.class_name] = copy(event)

    def add_entity(self, entity) -> None:
        """
        Adds an entity to the simulation.  Overwrites if there is an event with the given class name already.
        :param EntityRepr entity: The event to add.
        """
        self.entities[entity.class_name] = copy(entity)

    def check_for_issues(self) -> List[str]:
        """
        Looks for any issues that exist in the representation, e.g. bad name, unknown references, etc.
        :return: List of any issues found.
        """
        issues = list()
        issues.extend(self._check_simulation_for_issues())
        issues.extend(self._check_entities_for_issues())
        issues.extend(self._check_events_for_issues())
        return issues

    def _check_simulation_for_issues(self) -> List[str]:
        """
        Looks for issues at the simulation level.
        :return: List of any issues found.
        """
        issues = list()
        if not self.name:  # might want to check for spaces, etc. since this is the file name.
            issues.append("ERROR:  No simulation name provided.  One is needed to generate the simulation file.")

        return issues

    def _check_entities_for_issues(self) -> List[str]:
        """
        Looks for issues at the entity level.
        :return: List of any issues found.
        """
        # TODO check the entities.
        issues = list()

        # Get all of the event and entity names for easy checking.
        event_names = [event.event_name for event in self.events.values()]
        entity_names = [entity.entity_name for entity in self.entities.values()]

        for entity in self.entities.values():
            if not SimulationRepr.__valid_class_name(entity.class_name):
                issues.append(f"ERROR: '{entity.class_name}' is not a recommended event class name.")
            if entity.entity_name not in entity_names:
                issues.append(f"WARNING: No other entities have interest in '{entity.entity_name}'.")
            for event_name in entity.event_handlers:
                if event_name not in event_names:
                    issues.append(f"ERROR: '{entity.class_name}' has a handler for unknown event '{event_name}'.")
            for entity_name in entity.entity_handlers.keys():
                if entity_name not in entity_names:
                    issues.append(f"ERROR: '{entity.class_name}' has a handler for unknown entity '{entity_name}'.")
                # Just check the states no matter if the name was good.
                entity_states = entity.entity_handlers[entity_name]
                for state_change in entity_states:
                    if state_change not in ["created", "changed", "destroyed"]:
                        issues.append(f"ERROR: '{entity.class_name}' has invalid state interest '{state_change}' "
                                      f"for '{entity.entity_name}")

        return issues

    def _get_entity_with_name(self, entity_name) -> Union[EntityRepr, None]:
        """
        Returns the entity with the given name.  This is O(n), so might be open to speeding up.
        :param str entity_name: Name of the entity to find.
        :returns: The entity of the given name or None.
        """
        assert entity_name
        for entity in self.entities.values():
            if entity_name == entity.entity_name:
                return entity
        return None

    def _check_events_for_issues(self) -> List[str]:
        """
        Looks for issues at the event level.
        :return: List of any issues found.
        """
        issues = list()

        # Get all of the events that entities are interested in.
        entity_event_interest = set()
        for entity in self.entities.values():
            entity_event_interest.update(entity.event_handlers)

        for event in self.events.values():
            if not SimulationRepr.__valid_class_name(name=event.class_name):
                issues.append(f"ERROR: {event.class_name} is not a recommended event class name.")
            if event.event_name not in entity_event_interest:
                issues.append(f"WARNING:  No entity has interest in event named {event.event_name}.")

        return issues

    @staticmethod
    def __valid_class_name(name) -> bool:
        """
        Checks to see if the name is a "valid" class name in Python.  The convention is camel case.  The first
        letter is checked to make sure it's alpha and capital.  Other than that, check for whitespace, undersocres, and
        dashes.
        :param str name: The name to check.
        :returns: True if it looks like it's probably a valid name.
        """
        if not re.match(r"^[A-Z]", name):
            return False
        elif re.search(r"\s", name):
            return False
        elif re.search(r"[_|-]", name):
            return False

        return True


class SimulationYAMLReader:
    """
    Reads a simulation description from YAML, then validate, and then parse.
    """

    def __init__(self):
        """
        Creates a new YAML translator.
        """
        self.yaml = None

    def read_yaml_from_file(self, yaml_file) -> SimulationRepr:
        """
        Reads a YAML description from a string.
        :param str yaml_file: The file to read from.
        :return: The simulation representation.
        """
        with open(yaml_file, "r") as yf:
            self.yaml = yaml.full_load(yf)
        return self._parse_yaml()

    def read_yaml_from_str(self, yaml_str) -> SimulationRepr:
        """
        Reads a YAML description from a string.
        :param str yaml_str: The string containing the YAML.
        :return: The simulation representation.
        """
        self.yaml = yaml.full_load(yaml_str)
        return self._parse_yaml()

    def _parse_yaml(self) -> SimulationRepr:
        """
        Parses the YAML into a
        :return: A simulation representation.
        """
        if not self.yaml:
            raise ValueError(f"Invalid state for YAML reader.  No YAML to parse.")

        sr = SimulationRepr(name=self.yaml["simulation"])

        if "events" in self.yaml.keys():
            events = self.yaml["events"]

            for event_class in events:

                event = events[event_class]
                event_name = event.get("name", None)
                event_attributes = event.get("attributes", [])
                sr.add_event(EventRepr(class_name=event_class, event_name=event_name, attributes=event_attributes))

        if "entities" in self.yaml.keys():
            entities = self.yaml["entities"]

            for entity_class in entities:

                entity = entities[entity_class]
                entity_name = entity.get("name", None)
                entity_attributes = entity.get("attributes", [])
                entity_repr = EntityRepr(class_name=entity_class, entity_name=entity_name, attributes=entity_attributes)

                handlers = entity.get("handlers", None)
                if handlers:

                    if "entities" in handlers.keys():
                        entity_handlers = handlers["entities"]
                        for entity_to_handle in entity_handlers.keys():
                            entity_repr.entity_handlers[entity_to_handle] = entity_handlers[entity_to_handle]

                    if "events" in handlers.keys():
                        for event_name in handlers["events"]:
                            # special case events first.
                            if event_name == "time_update":
                                entity_repr.time_update_handler = True
                            elif event_name == "simulation_shutdown":
                                entity_repr.simulation_shutdown_handler = True
                            else:
                                entity_repr.event_handlers.append(event_name)

                sr.add_entity(entity=entity_repr)

        return sr


class SimulationWriter:
    """Writes a simulation module based on a SimulationRepr"""

    def __init__(self):
        """
        Creates a new simulation writer.
        """
        pass

    @staticmethod
    def write_simulation_module(simulation_repr, filename=None) -> None:
        """
        Writes the simulation representation to an actual simulation in a single module.
        :param SimulationRepr simulation_repr: The representation of the simulation to write.
        :param str filename: The name of the file to write the simulation to.  If not provided, will use the
        simulation name.
        """
        assert simulation_repr
        if not filename:
            filename = simulation_repr.name + ".py"

        with open(filename, "w") as outfile:
            SimulationWriter.__write_header(outfile=outfile, simulation_repr=simulation_repr)
            SimulationWriter.__write_events(outfile=outfile, simulation_repr=simulation_repr)
            SimulationWriter.__write_entities(outfile=outfile, simulation_repr=simulation_repr)
            SimulationWriter.__write_main(outfile=outfile, simulation_repr=simulation_repr)

    @staticmethod
    def __write_header(outfile, simulation_repr) -> None:
        """
        Writes the header of the file.
        :param file outfile: The file stream to write to.
        :param SimulationRepr simulation_repr: The simulation representation.
        """

        outfile.write(f"""\
\"\"\"
Generated simulation {simulation_repr.name}
\"\"\"

# TODO adjust for the simulation needs.
from scarab.entities import *
from scarab.events import *
from scarab.simulation import Simulation, SIMULATION_LOGGING
from scarab.loggers import global_loggers, StdOutLogger

StdOutLogger(topics=SIMULATION_LOGGING)

""")

    @staticmethod
    def __write_events(outfile, simulation_repr) -> None:
        """
        Writes the event classes to the file.
        :param file outfile: The file stream to write to.
        :param SimulationRepr simulation_repr: The simulation representation.
        """
        for event_repr in simulation_repr.events.values():
            attribute_list = [attribute + "=None" for attribute in event_repr.attributes]
            attribute_list = ", ".join(attribute_list)

            outfile.write("\n")
            outfile.write(ind(0) + f'class {event_repr.class_name}(Event):\n')
            outfile.write(ind(1) + f'"""Represents an {event_repr.event_name} event."""\n')
            outfile.write("\n")
            outfile.write(ind(1) + f'def __init__(self, {attribute_list}):\n')
            outfile.write(ind(2) + '"""\n')
            outfile.write(ind(2) + f'Creates a new {event_repr.event_name} event.\n')

            for attribute in event_repr.attributes:
                outfile.write(ind(2) + f':param str {attribute}: {attribute}\n')

            outfile.write(ind(2) + f':returns: None\n')
            outfile.write(ind(2) + '"""\n')

            for attribute in event_repr.attributes:
                outfile.write(ind(2) + f'self.{attribute} = {attribute}\n')
            outfile.write("\n")
            outfile.write(ind(2) + f'super().__init__(name="{event_repr.event_name}")\n')
            outfile.write("\n")

    @staticmethod
    def __write_entities(outfile, simulation_repr) -> None:
        """
        Writes the entity classes to the file.
        :param file outfile: The file stream to write to.
        :param SimulationRepr simulation_repr: The simulation representation.
        """
        for entity_repr in simulation_repr.entities.values():
            attribute_list = [attribute + "=None" for attribute in entity_repr.attributes]
            attribute_list = ", ".join(attribute_list)

            # class definition
            outfile.write('\n')
            outfile.write(ind(0) + f'class {entity_repr.class_name}(Entity):\n')
            outfile.write(ind(1) + f'"""Represents an {entity_repr.entity_name} entity."""\n')
            outfile.write('\n')

            # __init__ method
            outfile.write(ind(1) + f'def __init__(self, {attribute_list}):\n')
            outfile.write(ind(2) + '"""\n')
            outfile.write(ind(2) + f'Creates a new {entity_repr.entity_name} entity.\n')

            for attribute in entity_repr.attributes:
                outfile.write(ind(2) + f':param str {attribute}: {attribute}\n')

            outfile.write(ind(2) + '"""\n')

            for attribute in entity_repr.attributes:
                outfile.write(ind(2) + f'self.{attribute} = {attribute}\n')
            outfile.write('\n')
            outfile.write(ind(2) + f'super().__init__(name="{entity_repr.entity_name}")\n')
            outfile.write('\n')

            # Add the event handlers.
            for event_name in entity_repr.event_handlers:
                outfile.write(ind(1) + f'@event_handler(event_name="{event_name}")\n')
                outfile.write(ind(1) +
                              f'def handle_{SimulationWriter.__clean_name(event_name)}_event(self, event) -> None:\n')
                outfile.write(ind(2) + f'"""\n')
                outfile.write(ind(2) + f'Handles a {event_name} event.\n')
                outfile.write(ind(2) + f':param Event event: {event_name} event.\n')
                outfile.write(ind(2) + f'"""\n')
                outfile.write(ind(2) + f'pass\n')
                outfile.write('\n')

            if entity_repr.time_update_handler:
                outfile.write(ind(1) + f'@time_update_event_handler\n')
                outfile.write(ind(1) + f'def handle_time_event(self, previous_time, new_time) -> None:\n')
                outfile.write(ind(2) + f'"""\n')
                outfile.write(ind(2) + f'Handles a time change.\n')
                outfile.write(ind(2) + f':param int previous_time: The previous simulation time.\n')
                outfile.write(ind(2) + f':param int new_time: The new simulation time.\n')
                outfile.write(ind(2) + f'"""\n')
                outfile.write(ind(2) + f'pass\n')
                outfile.write('\n')

            if entity_repr.simulation_shutdown_handler:
                outfile.write(ind(1) + f'@simulation_shutdown_handler\n')
                outfile.write(ind(1) + f'def handle_simulation_shutdown(self, shutdown_event) -> None:\n')
                outfile.write(ind(2) + f'"""\n')
                outfile.write(ind(2) + f'Handles any activities related to shutting down of the simulation.\n')
                outfile.write(ind(2) + f':param Event shutdown_event: The shutdown event.\n')
                outfile.write(ind(2) + f'"""\n')
                outfile.write(ind(2) + f'pass\n')
                outfile.write('\n')

            for entity_name in entity_repr.entity_handlers.keys():
                for state in entity_repr.entity_handlers[entity_name]:
                    if state == "created":
                        outfile.write(ind(1) + f'@entity_created_event_handler(entity_name="{entity_name}")\n')
                        outfile.write(ind(1) + f'def handle_{SimulationWriter.__clean_name(entity_name)}'
                                               f'_created(self, entity):\n')
                        outfile.write(ind(2) + f'"""\n')
                        outfile.write(ind(2) + f'Handles a {entity_name} created event.\n')
                        outfile.write(ind(2) + f':param RemoteEntity entity: {entity_name} entity.\n')
                        outfile.write(ind(2) + f':returns: None\n')
                        outfile.write(ind(2) + f'"""\n')
                        outfile.write(ind(2) + f'pass\n')
                        outfile.write('\n')
                    elif state == "destroyed":
                        outfile.write(ind(1) + f'@entity_destroyed_event_handler(entity_name="{entity_name}")\n')
                        outfile.write(ind(1) + f'def handle_{SimulationWriter.__clean_name(entity_name)}'
                                               f'_destroyed(self, entity):\n')
                        outfile.write(ind(2) + f'"""\n')
                        outfile.write(ind(2) + f'Handles a {entity_name} destroyed event.\n')
                        outfile.write(ind(2) + f':param RemoteEntity entity: {entity_name} entity.\n')
                        outfile.write(ind(2) + f':returns: None\n')
                        outfile.write(ind(2) + f'"""\n')
                        outfile.write(ind(2) + f'pass\n')
                        outfile.write('\n')
                    elif state == "changed":
                        outfile.write(ind(1) + f'@entity_changed_event_handler(entity_name="{entity_name}")\n')
                        outfile.write(ind(1) + f'def handle_{SimulationWriter.__clean_name(entity_name)}'
                                               f'_changed(self, entity, changed_properties):\n')
                        outfile.write(ind(2) + f'"""\n')
                        outfile.write(ind(2) + f'Handles a {entity_name} changed event.\n')
                        outfile.write(ind(2) + f':param RemoteEntity entity: {entity_name} entity.\n')
                        outfile.write(ind(2) + f':param list of str changed_properties: list of changed properties.\n')
                        outfile.write(ind(2) + f':returns: None\n')
                        outfile.write(ind(2) + f'"""\n')
                        outfile.write(ind(2) + f'pass\n')
                        outfile.write('\n')

    @staticmethod
    def __clean_name(name) -> str:
        """
        Cleans a name so it can be used as a variable.
        :param str name: The name to clean.
        :returns: The clean name that can be used.
        """
        new_name = \
            name.replace(" ", "")\
            .replace("-", "_")
        return new_name

    @staticmethod
    def __write_main(outfile, simulation_repr) -> None:
        """
        Writes the stub for the main section.
        :param file outfile: The file stream to write to.
        :param SimulationRepr simulation_repr: The simulation representation.
        """
        outfile.write(f'\n')
        outfile.write(ind(0) + f'def main():\n')
        outfile.write(ind(1) + f'"""\n')
        outfile.write(ind(1) + f'Main driver for simulation {simulation_repr.name}\n')
        outfile.write(ind(1) + f'"""\n')
        outfile.write(ind(1) + f'sim = Simulation(name="{simulation_repr.name}")\n')
        outfile.write(f'\n')

        outfile.write(f'\n')
        outfile.write(ind(0) + f'if __name__ == "__main__":\n')
        outfile.write(ind(1) + f'main()\n')

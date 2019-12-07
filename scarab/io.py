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
import yaml


class EventRepr:
    """Represents an event."""

    def __init__(self, class_name, event_name, attributes):
        """
        Creates new event representation.
        :param class_name: Name of the event.
        :type class_name: str
        :param event_name: Name of the event.
        :type event_name: str
        :param attributes: List of attribute names.
        :type attributes: list of str
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
        :param class_name: Name of the entity.
        :type class_name: str
        :param entity_name: Name of the entity.
        :type entity_name: str
        :param attributes: List of attribute names.
        :type attributes: list of str
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
        self.time_update_handler = False  # True if handles time updates.
        self.event_handlers = []  # list of events that are handled.


class SimulationRepr:
    """Represents a simulation."""

    def __init__(self, name):
        """
        Creates a new simulation representation.
        :param name:  The name of the simulation.
        :type name: str
        """
        assert name

        self.name = name
        self.events = {}  # event.class_name: EventRepr
        self.entities = {}  # entity.class_name: EntityRepr

    def add_event(self, event):
        """
        Adds an event to the simulation.  Overwrites if there is an event with the given class name already.
        :param event: The event to add.
        :type event: EventRepr
        :return: None
        """
        self.events[event.class_name] = copy(event)

    def add_entity(self, entity):
        """
        Adds an entity to the simulation.  Overwrites if there is an event with the given class name already.
        :param entity: The event to add.
        :type entity: EntityRepr
        :return: None
        """
        self.entities[entity.class_name] = copy(entity)

    def check_for_issues(self):
        """
        Looks for any issues that exist in the representation, e.g. bad name, unknown references, etc.
        :return: List of any issues found.
        :rtype: list of str
        """
        issues = list()
        issues.extend(self._check_simulation_for_issues())
        issues.extend(self._check_entities_for_issues())
        issues.extend(self._check_events_for_issues())
        return issues

    def _check_simulation_for_issues(self):
        """
        Looks for issues at the simulation level.
        :return: List of any issues found.
        :rtype: list of str
        """
        issues = list()
        if not self.name:  # might want to check for spaces, etc. since this is the file name.
            issues.append("ERROR:  No simulation name provided.  One is needed to generate the simulation file.")

        return issues

    def _check_entities_for_issues(self):
        """
        Looks for issues at the entity level.
        :return: List of any issues found.
        :rtype: list of str
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

    def _get_entity_with_name(self, entity_name):
        """
        Returns the entity with the given name.  This is O(n), so might be open to speeding up.
        :param entity_name: Name of the entity to find.
        :type entity_name: str
        :returns: The entity of the given name or None.
        :rtype: EntityRepr | None
        """
        assert entity_name
        for entity in self.entities.values():
            if entity_name == entity.entity_name:
                return entity
        return None

    def _check_events_for_issues(self):
        """
        Looks for issues at the event level.
        :return: List of any issues found.
        :rtype: list of str
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
    def __valid_class_name(name):
        """
        Checks to see if the name is a "valid" class name in Python.  The convention is camel case.  The first
        letter is checked to make sure it's alpha and capital.  Other than that, check for whitespace, undersocres, and
        dashes.
        :param name: The name to check.
        :type name: str
        :returns: True if it looks like it's probably a valid name.
        :rtype: bool
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

    def read_yaml_from_file(self, yaml_file):
        """
        Reads a YAML description from a string.
        :param yaml_file: The file to read from.
        :type yaml_file: str
        :return: SimulationRepr
        """
        with open(yaml_file, "r") as yf:
            self.yaml = yaml.full_load(yf)
        return self._parse_yaml()

    def read_yaml_from_str(self, yaml_str):
        """
        Reads a YAML description from a string.
        :param yaml_str: The string containing the YAML.
        :type yaml_str: str
        :return: SimulationRepr
        """
        self.yaml = yaml.full_load(yaml_str)
        return self._parse_yaml()

    def _parse_yaml(self):
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
                            else:
                                entity_repr.event_handlers.append(event_name)

                sr.add_entity(entity=entity_repr)

        return sr

"""
Copyright (c) 2024 William D Back

This file is part of Scarab licensed under the MIT License.
For full license text, see the LICENSE file in the project root.

Loggers to log simulation events.
"""
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import List

from scarab.framework.events import Event, ScarabEventType


class LogEventType(Enum):
    """
    Specifies the event types that can be logged, so that all or only some types can be logged.
    """
    ALL = 0
    SimulationEvents = 1  # simulation events, such as run, pause, etc. and time events.
    EntityEvents = 2  # events related to entities, e.g. create, update, destroy
    Events = 3  # general events not covered by simulation and entity events.


# groupings of event types to each of the log event types.
SimulationEvents = [ScarabEventType.SIMULATION_START, ScarabEventType.SIMULATION_PAUSE,
                    ScarabEventType.SIMULATION_RESUME, ScarabEventType.SIMULATION_SHUTDOWN,
                    ScarabEventType.TIME_UPDATED]
EntityEvents = [ScarabEventType.ENTITY_CREATED, ScarabEventType.ENTITY_CHANGED, ScarabEventType.ENTITY_DESTROYED]


class BaseLogger(ABC):
    """
    Base logging class that should be defined for all classes that log events.
    """

    def __init__(self, types: List[LogEventType] = None):
        """
        Creates a new base logger and optionally sets the types.  If the types are not specified use ALL.
        :param types:  The types of events to log.
        """
        self._log_types = types.copy() if types else [LogEventType.ALL]

    @property
    def log_type(self) -> List[LogEventType]:
        """
        Returns the log types for the logger.
        """
        return self._log_types.copy()

    @log_type.setter
    def log_type(self, types: List[LogEventType]):
        """
        Sets the log types overriding previous.
        :param types:  The types to log.  raises a value exception if the types are not specified.
        """
        if not types:
            raise ValueError("Must specify at least one event type to log.")

        self._log_types = types.copy()

    @abstractmethod
    def _log(self, message: str) -> None:
        """
        Logs the message.  All loggers will have the same format, which is controlled by the base class.
        :param message: The message to log.
        """
        pass

    def log_event(self, event: Event, sent_to: str) -> None:
        """
        This event will call the _log_event method after seeing if the event is a type to be logged.
        :param event: The event to log.
        :param sent_to: The target of the event.  This could be an entity or external.
        """

        if not isinstance(event, Event):
            raise ValueError("Attempt to log something other than an event.")

        if not self._log_types:
            return  # not logging anything.

        should_log = False

        if LogEventType.ALL in self._log_types:
            should_log = True
        elif LogEventType.SimulationEvents in self._log_types and event.event_name in SimulationEvents:
            should_log = True
        elif LogEventType.EntityEvents in self._log_types and event.event_name in EntityEvents:
            should_log = True
        else:
            should_log = True  # must be an event that's not in the previous.

        if should_log:
            t = time.localtime(time.time())
            message = f"{time.strftime('%Y.%m.%d-%H:%M', t)}|{sent_to}|{str(event)}"
            self._log(message)


class FileLogger(BaseLogger):
    """
    Event logger that logs to a file..
    """

    def __init__(self, filename: str, types: List[LogEventType] = None) -> None:
        """
        Creates a new file logger to the given file.
        :param filename: Full path of the file to log to.
        :param types: The types of events to log.
        """
        super().__init__(types=types)
        self._file = open(filename, 'w')

    def _log(self, message: str) -> None:
        """
        Logs the message to the file.
        :param message: The message to log.  This is formatted by the base logger.
        """
        self._file.write(message + '\n')

    def __del__(self) -> None:
        """
        Close the file.  Note that this may not be called in some scenarios.
        """
        try:
            self._file.close()
        except IOError as ioe:
            print(f"Error closing the log file: {self._file.name}")

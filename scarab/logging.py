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

This module contains base classes for Events and Commands as well as common Events and Commands used in the framework.
"""

from abc import ABC, abstractmethod
import datetime
import re
from typing import List

now = datetime.datetime.now()  # shortcut for getting the current time.


class BaseLogger(ABC):
    """
    Base class for all loggers.
    """

    def __init__(self, topics, date_format="%d-%m-%Y %H:%M:%S"):
        """
        Creates a new logger and registers the logger for logging messages.
        :param topics: One or more strings that define the topics to be handled by this logger.
        :type topics: str or list of str
        :return: None
        """
        assert topics  # don't allow to be None.
        assert date_format  # don'e allow to be None.  Doesn't check for valid format.

        self._topics = []
        if isinstance(topics, list):
            for t in topics:
                assert isinstance(t, str)
                self._topics.append(t)
        else:
            assert isinstance(topics, str)
            self._topics.append(topics)

        self._date_format = date_format

        super().__init__()
        _add_logger(self)

    @abstractmethod
    def log(self, topic, message):
        """
        Logs a message for a given topic.
        :param topic: The topic to log to.
        :type topic: str
        :param message:  The message to log.
        :type message: str
        :return:  None
        """
        pass

    @staticmethod
    def format_message(topic, message):
        """
        Formats the log message with the given message and topic.  Note that the time in the message is the time it was
        finally logged, not the exact time of the log message.  They should be very close.
        Format is:  [dd-mmm-yyyy hh:mm:ss] topic: message
        TODO Add the option to pass a time.
        :param topic: The topic for the message.
        :type topic: str
        :param message: The message to format.
        :type message: str
        :return: The formatted log message.
        :rtype: str
        """
        return "[{0}] {1}: {2}".format(now.strftime("%d-%m-%Y %H:%M:%S"), topic, message)


loggers = list()  # list of loggers.  TODO determine if this should be a dictionary to speed things up.


def _add_logger(logger):
    """
    Adds a logger to the list of loggers.
    :param logger:  A message logger.
    :type logger: BaseLogger
    :return: None
    """
    assert (isinstance(logger, BaseLogger))
    loggers.append(logger)


def log(topic, message):
    """
    Logs a message for a given topic based on registered loggers.
    :param topic:  The topic to log to.
    :type topic: str
    :param message:  The message to log for the given topic.
    :type message: str
    :return: None
    """
    for l in loggers:
        for t in l._topics:
            if re.match(t, topic):
                l.log(t, message)


class ListLogger(BaseLogger):
    """
    Logs the messages to a list of strings.  Note that this buffers unless clear() is called, so it can use up an
    unlimited amount of memory.
    """

    def __init__(self, topics):
        """
        Creates a logger that logs to all messages to a list for later retrieval.
        """
        self._logs = []
        super().__init__(topics=topics)

    def log(self, topic, message):
        """
        Logs a message for a given topic.
        :param topic: The topic to log to.
        :type topic: str
        :param message:  The message to log.
        :type message: str
        :return:  None
        """
        self._logs.append(BaseLogger.format_message(topic=topic, message=message))

    def get_log_messages(self):
        """
        Returns a copy of the list of the log messages.
        :return:  The list of messages.
        :rtype: list of str
        """
        return list(self._logs)

    def clear(self):
        """
        Clears the list to free up memory (assuming it wasn't copied).
        :return: None
        """
        self._logs = []

    def __len__(self):
        """
        Returns the length of the list of log messages, e.g. len(log)
        :return: The length of the list of log messages, e.g. len(log)
        :rtype: int
        """
        return len(self._logs)


class StdOutLogger(BaseLogger):
    """
    Logs the messages to standard out.
    """

    def __init__(self, topics):
        """
        Creates a logger that logs to all messages to a list for later retrieval.
        """
        self._logs = []
        super().__init__(topics=topics)

    def log(self, topic, message):
        """
        Logs a message for a given topic.
        :param topic: The topic to log to.
        :type topic: str
        :param message:  The message to log.
        :type message: str
        :return:  None
        """
        print(BaseLogger.format_message(topic=topic, message=message))


class FileLogger(BaseLogger):
    """
    Logs the messages to a file.
    TODO add rollover support for large file handling.
    """

    def __init__(self, topics, filename):
        """
        Creates a logger that logs to all messages to a list for later retrieval.
        :param topics: The topic or topics to log to.
        :type topics: str or list of str
        :param filename: The name (path) of the file to log to.
        :type filename: str
        :return: None
        """
        self._logs = []
        self._filename = filename
        self._file = None  # only open if there was something written.  Also supports multiple files and rollover.
        super().__init__(topics=topics)

    def log(self, topic, message):
        """
        Logs a message for a given topic.
        :param topic: The topic to log to.
        :type topic: str
        :param message:  The message to log.
        :type message: str
        :return:  None
        """
        if not self._file:
            self._file = open(self._filename, "w")

        self._file.write("{0}\n".format(BaseLogger.format_message(topic=topic, message=message)))
        self._file.flush()

    def close(self):
        """
        Closes the file if it was opened.
        :return: None
        """
        if self._file:
            self._file.close()
        self._file = None

    def __del__(self):
        """
        Closes the file if opened.  Just in case the file wasn't cleanly closed.
        :return:  None
        """
        self.close()

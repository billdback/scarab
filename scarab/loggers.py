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

from scarab.util import eprint

now = datetime.datetime.now()  # shortcut for getting the current time.


class Loggers:

    def __init__(self):
        """
        Manages all loggers.
        """
        self.__loggers = {}

    def add_logger(self, logger, topic):
        """
        Adds a logger to the list of loggers.
        :param logger: The logger to add.
        :type logger: BaseLogger
        :param topic: Topic to log on.
        :type topic: str
        :return: None
        """
        assert isinstance(logger, BaseLogger)

        if isinstance(topic, str):
            self.__add_logger_for_topic(topic=topic, logger=logger)
        elif isinstance(topic, list):
            for t in topic:
                self.__add_logger_for_topic(topic=t, logger=logger)
        else:
            raise ValueError(f"{topic} must be a string or list.")

    def __add_logger_for_topic(self, topic, logger) -> None:
        """
        Adds a logger for an individual topic.  Helper for loggers that get added for multiple topics.
        :param logger: The logger to add.
        :type logger: BaseLogger
        :param topic: Topic to log on.
        :type topic: str
        :return: None
        """
        if topic not in self.__loggers.keys():
            self.__loggers[topic] = []
        self.__loggers[topic].append(logger)

    def remove_logger_topic(self, topic):
        """
        Removes any loggers for a given topic.
        :param topic: The topic to remove all loggers for.
        :return: list of loggers that were removed.
        :rtype: list of BaseLogger
        """
        self.__loggers.pop(topic)

    def clear(self):
        """
        Clears all loggers.
        :return: None
        """
        self.__loggers = {}

    def log(self, topic, message):
        """
        Logs a message to a topic.
        :param topic: Topic to log to.
        :type topic: str
        :param message: Message to log.
        :type message: str
        :return: None
        """
        for logger in self.__loggers.get(topic, []):
            logger.log(topic, message)


global_loggers = Loggers()


def log(topic, message):
    """
    Helper to log a message to the global loggers.
    :param topic: The topic to log to.
    :type topic: str
    :param message:  The message to log.
    :type message: str
    :return: None
    """
    global_loggers.log(topic=topic, message=message)


def cancel_log(topic):
    """
    Cancels logging on a topic.  Note that this turns off all logging on the topic and new logs have to be added
    back.  TODO consider pausing and resuming.
    :param topic: The topic to stop logging.
    :type topic: str
    :returns: None
    """
    assert topic
    global_loggers.remove_logger_topic(topic=topic)


class BaseLogger(ABC):
    """
    Base class for all loggers.
    """

    def __init__(self, topics, date_format="%d-%m-%Y %H:%M:%S"):
        """
        Creates a new logger and registers the logger for logging messages.
        :param topics: One or more topics to log on this logger.
        :type topics: str | list of str
        :param date_format: Format to use when writing log messages.
        :type date_format: str
        :return: None
        """
        assert date_format  # don'e allow to be None.  Doesn't check for valid format.
        self._date_format = date_format

        assert topics
        self.topics = list()
        if isinstance(topics, str):
            self.topics.append(topics)
        elif isinstance(topics, list):
            self.topics.extend(topics)
        for topic in self.topics:
            global_loggers.add_logger(logger=self, topic=topic)

        super().__init__()

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


class ListLogger(BaseLogger):
    """
    Logs the messages to a list of strings.  Note that this buffers unless clear() is called, so it can use up an
    unlimited amount of memory.
    """

    def __init__(self, topics):
        """
        Creates a logger that logs to all messages to a list for later retrieval.
        :param topics: One or more topics to log on this logger.
        :type topics: str | list of str
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
        Creates a logger that logs to all messages to standard out.
        :param topics: One or more topics to log on this logger.
        :type topics: str | list of str
        """
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


class StdErrLogger(BaseLogger):
    """
    Logs the messages to standard error.
    """

    def __init__(self, topics):
        """
        Creates a logger that logs to all messages to standard error.
        :param topics: One or more topics to log on this logger.
        :type topics: str | list of str
        """
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
        eprint(BaseLogger.format_message(topic=topic, message=message))


class FileLogger(BaseLogger):
    """
    Logs the messages to a file.
    TODO add rollover support for large file handling.
    """

    def __init__(self, topics, filename):
        """
        Creates a logger that logs to all messages to a list for later retrieval.
        :param topics: One or more topics to log on this logger.
        :type topics: str | list of str
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

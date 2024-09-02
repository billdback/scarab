"""
Loggers are specific loggers for Scarab for tracing different event types.  Unlike the standard Python logging module
it is intended to be used across the whole package.  It also allows for specifying Scarab topics, such as "events" or
"entities" to log relevant information during execution.
"""

from abc import ABC, abstractmethod
from typing import List


class Logger(ABC):
    """
    Abstract logger class that all loggers will extend from.
    """

    def __init__(self, topics: List[str] = None):
        """
        Creates a new logger with a given topic.
        :param topics: The list of topics to log.  Only messages on the appropriate topic will be logged.
        """
        self._topics = list(topics) if topics else []

    def add_topic(self, topic: str) -> List[str]:
        """
        Adds another topic to the list of topics.
        :param topic: The topic to add.
        :return: The list of topics.
        """
        self._topics.append(topic)
        return list(self._topics)

    def remove_topic(self, topic: str) -> List[str]:
        """
        Removes a topic from logging.
        :param topic:
        """
        self._topics.remove(topic)
        return list(self._topics)

    @property
    def topics(self) -> List[str]:
        """
        Returns the list of topics.
        :return: The list of topics.
        """
        return list(self._topics)

    @abstractmethod
    def log(self, topic: str, msg: str):
        pass


class ConsoleLogger(Logger):
    """
    Class the logs messages to the console.
    """

    def __init__(self, topics: List[str] = None):
        """
        Creates a new logger that will log to the console.
        :param topics: The list of topics.
        """
        super().__init__(topics)

    def log(self, topic: str, msg: str) -> None:
        """
        Logs the message to the console.
        :param topic: The topic to log to.
        :param msg: The message to log.
        """
        if topic in self._topics:
            print(msg)

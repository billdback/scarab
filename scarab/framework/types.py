"""
Common variables and types used throughout the framework.
"""
from typing import Callable

from scarab.framework.events import Event

# Standard type for simulation IDs.
SimID = str

# Standard event handler takes an event and doesn't return anything.
EventHandler: object = Callable[[Event], None]

class ScarabException(Exception):
    def __init__(self, msg: str = None):
        self.message = msg
        super().__init__(msg)


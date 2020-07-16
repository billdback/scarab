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

This module contains utility functions and classes for creating simulations.
"""

import uuid
import sys
import time


def eprint(*args, **kwargs):
    """
    Prints to standard error similar to regular print.
    :param args:  Positional arguments.
    :param kwargs:  Keyword arguments.
    """
    print(*args, file=sys.stderr, **kwargs)


def get_uuid():
    """
    Returns a unique ID for something in the simulation.
    :return: A unique ID for something in the simulation.
    :rtype: str
    TODO consider if this is thread safe.
    """

    nanoseconds = int(time.time() * 1e9)
    return uuid.uuid1(clock_seq=nanoseconds)


def ind(length):
    """
    Returns spaces for indentation.
    :param length: The number of spaces.
    :type length: int
    :returns: A string with the number of spaces to indent.
    :rtype: str
    """
    spaces = ""
    for space in range(0,length*4):
        spaces += " "
    return spaces



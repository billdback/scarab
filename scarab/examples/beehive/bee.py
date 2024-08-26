"""
Represents the bee entity.
"""
from . types import BeeType
from scarab.framework.entity import Entity


@Entity(name="bee", conforms_to=BeeType)
class BasicBee:

    def __init__(self, b: bool = False, f: bool = False):
        """Basic Bee that conforms with the Bee interface."""
        self.isBuzzing = b
        self.isFlapping = f

    def __str__(self):
        res = "Basic Bee:\n"
        res += f"  isBuzzing: {'True' if self.isBuzzing else 'False'}\n"
        res += f"  isFlapping: {'True' if self.isFlapping else 'False'}\n"
        return res

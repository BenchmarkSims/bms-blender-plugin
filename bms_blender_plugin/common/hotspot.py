from enum import Enum
from mathutils import Vector
from bms_blender_plugin.common.util import to_bms_coords


class MouseButton(int, Enum):
    LEFT_CLICK = 1
    RIGHT_CLICK = 2


class ButtonType(str, Enum):
    SWITCH = ""
    WHEEL = "w"
    PUSH_BUTTON = "p"


class Callback:
    """Represents a callback which is passed to BMS when a user clicks a cockpit button"""
    def __init__(self, name: str, group: str):
        self.name = name
        self.group = group


class Hotspot:
    """Represents a user-clickable hotspot in the 3d pit. Used in 3dButtons.dat"""

    def __init__(
        self,
        callback_id: str,
        x: float,
        y: float,
        z: float,
        size: int,
        sound_id: int,
        mouse_button: MouseButton,
        button_type: ButtonType,
    ):
        self.callback_id = callback_id
        self.x = x
        self.y = y
        self.z = z
        self.size = size
        self.sound_id = sound_id
        self.mouse_button = mouse_button
        self.button_type = button_type

def __str__(self):
    """"Format according to 3dButtons.dat.
    BMS should have no problems reading different amounts of spaces, but it looks prettier..."""
    # Use consistent coordinate transformation utility
    bms_coords = to_bms_coords(Vector((self.x, self.y, self.z)))
    
    output = f"{self.callback_id.ljust(29 ,' ')}"
    output += "{:{w}.{p}f}{:{w}.{p}f}{:{w}.{p}f}".format(
        round(bms_coords.x, 6), round(bms_coords.y, 6), round(bms_coords.z, 6), w=12, p=6
    )
    output += f"{' ':<4}{self.size}{' ':<4}{self.sound_id}{' ':<4}{self.mouse_button}"

    if self.button_type != ButtonType.SWITCH:
        output += f"{' ':<4}{self.button_type}"

    return output

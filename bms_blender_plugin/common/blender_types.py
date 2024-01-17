import bpy

from enum import Enum

"""Custom Blender ID types"""

class BlenderNodeType (str, Enum):
    """object.bml_type"""
    PBR_LIGHT = "pbr_light"
    DOF = "dof"
    SLOT = "slot"
    SWITCH = "switch"
    BBOX = "bbox"
    HOTSPOT = "hotspot"
    NONE = "none"

    def __str__(self):
        return str(self.value)


class BlenderEditorNodeType (str, Enum):
    """node.bml_node_type"""
    # DOF nodes
    DOF_MODEL = "dof_model"
    RENDER_CONTROL = "render_control"

    # Material nodes
    MATERIAL = "material"
    SHADER_PARAMETER = "shader_parameter"
    SAMPLER = "sampler"
    NONE = "none"

    def __str__(self):
        return str(self.value)


class BlenderNodeTreeType (str, Enum):
    DOF_TREE = "dof_tree"
    MATERIAL_TREE = "material_tree"
    NONE = "none"

    def __str__(self):
        return str(self.value)


class ScriptEnum:
    number: int
    name: str

    def __init__(self, number, name):
        self.number = number
        self.name = name


class DofEnum:
    dof_number: int
    name: str

    def __init__(self, dof_number, name):
        self.dof_number = dof_number
        self.name = name


class SwitchEnum:
    switch_number: int
    branch: int
    name: str
    comment: str

    def __init__(self, switch_number, branch, name, comment):
        self.switch_number = switch_number
        self.branch = branch
        self.name = name
        self.comment = comment

    def __repr__(self):
        return f"{self.name} ({self.switch_number}) - {self.branch}"

    def bpy_enum_entry(self):
        return self.switch_number, self.name, ""


class LodItem:
    def __init__(self, file_suffix: str, viewing_distance: int, collection: bpy.types.Collection):
        self.file_suffix = file_suffix
        self.viewing_distance = viewing_distance
        self.collection = collection

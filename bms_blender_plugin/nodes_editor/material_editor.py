import bpy
import nodeitems_utils
from bpy.types import NodeTree

from bms_blender_plugin.nodes_editor import material_node_categories


class MaterialNodeTree(NodeTree):
    """Base class for the BMS Material Node Tree"""
    bl_label = "BMS Material Node Tree"
    bl_icon = "MATERIAL"

    def execute(self, context):
        pass


def register():
    bpy.utils.register_class(MaterialNodeTree)
    nodeitems_utils.register_node_categories("MATERIALS", material_node_categories)


def unregister():
    nodeitems_utils.unregister_node_categories("MATERIALS")
    bpy.utils.unregister_class(MaterialNodeTree)

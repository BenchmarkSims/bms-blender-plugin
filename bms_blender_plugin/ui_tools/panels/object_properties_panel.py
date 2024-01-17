import bpy

from bms_blender_plugin.common.blender_types import BlenderNodeType
from bms_blender_plugin.common.util import get_bml_type
from bms_blender_plugin.ui_tools.panels.base_panel import BasePanel


class ObjectPropertiesPanel(BasePanel, bpy.types.Panel):
    """The 'Object Properties' panel"""
    bl_label = "Object Properties"
    bl_idname = "BML_PT_ObjectPropertiesPanel"

    @classmethod
    def poll(cls, context):
        return context.active_object and not (
            get_bml_type(context.active_object) == BlenderNodeType.BBOX
            or get_bml_type(context.active_object) == BlenderNodeType.DOF
            or get_bml_type(context.active_object) == BlenderNodeType.HOTSPOT
            or get_bml_type(context.active_object) == BlenderNodeType.SWITCH
            or get_bml_type(context.active_object) == BlenderNodeType.SLOT
        )

    def draw(self, context):
        layout = self.layout
        active_object = context.active_object
        layout.prop(active_object, "bml_do_not_merge")


def register():
    bpy.utils.register_class(ObjectPropertiesPanel)


def unregister():
    bpy.utils.unregister_class(ObjectPropertiesPanel)

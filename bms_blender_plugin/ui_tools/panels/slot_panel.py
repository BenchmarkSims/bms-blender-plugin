import bpy

from bms_blender_plugin.common.blender_types import BlenderNodeType
from bms_blender_plugin.common.util import get_bml_type
from bms_blender_plugin.ui_tools.panels.base_panel import BasePanel


class SlotPanel(BasePanel, bpy.types.Panel):
    """The 'Slot' Panel"""
    bl_label = "Slot"
    bl_idname = "BML_PT_SlotPanel"

    @classmethod
    def poll(cls, context):
        return get_bml_type(context.active_object) == BlenderNodeType.SLOT

    def draw(self, context):
        layout = self.layout
        active_object = context.active_object

        layout.prop(active_object, "bml_slot_number")


def register():
    bpy.utils.register_class(SlotPanel)


def unregister():
    bpy.utils.unregister_class(SlotPanel)

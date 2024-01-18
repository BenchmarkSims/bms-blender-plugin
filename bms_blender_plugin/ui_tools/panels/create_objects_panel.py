import bpy


from bms_blender_plugin.common.util import (
    Icons,
)
from bms_blender_plugin.ui_tools.operators.create_dof import CreateDof
from bms_blender_plugin.ui_tools.panels.base_panel import BasePanel
from bms_blender_plugin.ui_tools.operators.create_hotspot import CreateHotspot

from bms_blender_plugin.ui_tools.operators.create_pbr_light import CreatePBRLight
from bms_blender_plugin.ui_tools.operators.create_switch import CreateSwitch
from bms_blender_plugin.ui_tools.operators.create_bounding_box_operator import CreateBoundingBox
from bms_blender_plugin.ui_tools.operators.slot_operators import CreateSlot


class CreateObjectsPanel(BasePanel, bpy.types.Panel):
    """The 'Create' panel"""
    bl_label = "Create"
    bl_idname = "BML_PT_CreateObjectsPanel"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator(CreateDof.bl_idname, text="DOF", icon="EMPTY_DATA")
        row = layout.row()
        row.operator(CreateSwitch.bl_idname, text="Switch", icon="CHECKBOX_HLT")
        row = layout.row()
        row.operator(CreatePBRLight.bl_idname, text="Billboard Light", icon="LIGHT")
        row = layout.row()
        row.operator(CreateHotspot.bl_idname, text="Hotspot", icon_value=Icons.hotspot_icon_id)
        row = layout.row()
        row.operator(CreateSlot.bl_idname, text="Slot", icon_value=Icons.slot_icon_id)
        row = layout.row()
        row.operator(CreateBoundingBox.bl_idname, text="Bounding Box", icon="META_CUBE")


def register():
    bpy.utils.register_class(CreateObjectsPanel)


def unregister():
    bpy.utils.unregister_class(CreateObjectsPanel)

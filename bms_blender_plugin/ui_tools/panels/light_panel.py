import bpy

from bms_blender_plugin.common.blender_types import BlenderNodeType
from bms_blender_plugin.common.util import get_bml_type
from bms_blender_plugin.ui_tools.panels.base_panel import BasePanel


class LightPanel(BasePanel, bpy.types.Panel):
    """The 'Billboard Light' panel - might be renamed once we have more light types (e.g. ACDATA)"""
    bl_label = "Billboard Light"
    bl_idname = "BML_PT_LightPanel"

    @classmethod
    def poll(cls, context):
        return get_bml_type(context.active_object) == BlenderNodeType.PBR_LIGHT

    def draw(self, context):
        layout = self.layout
        active_object = context.active_object

        layout.prop(active_object, "color")
        layout.prop(active_object, "bml_light_directional")


def register():
    bpy.utils.register_class(LightPanel)


def unregister():
    bpy.utils.unregister_class(LightPanel)

import bpy

from bms_blender_plugin.ui_tools.panels.base_panel import BasePanel


class LodAndMaterialSetsPanel(BasePanel, bpy.types.Panel):
    bl_label = "LODs & Material Sets"
    bl_idname = "BML_PT_LodsAndMaterialSets"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
       pass


def register():
    # registration / unregistration handled in the LODPanel child
    pass


def unregister():
    # registration / unregistration handled in the LODPanel child
    pass

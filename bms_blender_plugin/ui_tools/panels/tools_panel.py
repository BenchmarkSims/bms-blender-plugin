import subprocess

import bpy

from bpy.types import Operator
from bpy.props import StringProperty

from bms_blender_plugin.common.util import to_bms_coords
from bms_blender_plugin.ext.blender_dds_addon.directx import util
from bms_blender_plugin.ui_tools.operators.dof_operators import ResetAllDofs
from bms_blender_plugin.ui_tools.panels.base_panel import BasePanel


class ToolsPanel(BasePanel, bpy.types.Panel):
    bl_label = "Tools"
    bl_idname = "BML_PT_ToolsPanel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        if context.active_object:
            # Blenders internal coords are always in meters, despite the scene settings -> always convert to ft
            scale_factor = 3.28084

            obj_bms_coords = to_bms_coords(
                context.active_object.matrix_world.translation
            )
            x_coord_text = f"{round(obj_bms_coords.x * scale_factor, 2): .2f}"
            y_coord_text = f"{round(obj_bms_coords.y * scale_factor, 2): .2f}"
            z_coord_text = f"{round(obj_bms_coords.z * scale_factor, 2): .2f}"

            layout.label(text="BMS Coordinates")
            box = layout.box()

            row = box.row()
            row.column().label(text="X")
            col = row.column()
            col.alignment = "RIGHT"
            col.label(text=x_coord_text)

            row = box.row()
            row.column().label(text="Y")
            col = row.column()
            col.alignment = "RIGHT"
            col.label(text=y_coord_text)

            row = box.row()
            row.column().label(text="Z")
            col = row.column()
            col.alignment = "RIGHT"
            col.label(text=z_coord_text)

            operator = layout.operator(CopyTextToClipboard.bl_idname, icon="COPYDOWN")
            operator.text = f"{x_coord_text} {y_coord_text} {z_coord_text}"

        layout.separator()
        layout.row().operator(ResetAllDofs.bl_idname, icon="LOOP_BACK")


class CopyTextToClipboard(Operator):
    """Copies the coordinates to the clipboard"""
    bl_idname = "bml.copy_text_to_clipboard"
    bl_label = "Copy to Clipboard"
    bl_description = "Copies the coordinates to the clipboard"

    text: StringProperty(default="")

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        if self.text != "":
            clip_process = ""
            if util.is_windows():
                clip_process = "clip"
            elif util.is_linux():
                clip_process = "wl-copy"
            elif util.is_mac():
                clip_process = "pbcopy"
            else:
                return

            subprocess.run(
                clip_process, input=self.text.strip(), check=True, encoding="utf-8"
            )
            self.report({"INFO"}, f"Copied '{self.text}' to Clipboard")
        return {"FINISHED"}


def register():
    bpy.utils.register_class(CopyTextToClipboard)
    bpy.utils.register_class(ToolsPanel)


def unregister():
    bpy.utils.unregister_class(ToolsPanel)
    bpy.utils.unregister_class(CopyTextToClipboard)
    

import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

from bms_blender_plugin.common.blender_types import BlenderNodeType
from bms_blender_plugin.common.bml_structs import DofType
from bms_blender_plugin.common.util import get_bml_type


class ExporterPreferences(bpy.types.AddonPreferences):
    """Holds the preferences of the plugin."""
    bl_idname = __package__

    editor_path: StringProperty(
        name="BMS Editor path",
        description="Full path to the BMS Editor.exe",
        default="",
        maxlen=255,
        subtype="FILE_PATH",
    )
    do_not_delete_export_collection: BoolProperty(
        name="Do not delete export collection",
        description="Does not delete the export collection after the export is complete",
        default=False,
    )

    do_not_join_materials: BoolProperty(
        name="Do not join same materials",
        description="Does not join objects with identical materials",
        default=False,
    )

    copy_to_clipboard_command: StringProperty(
        name="Alternative 'Copy to Clipboard' command",
        description="Override command to copy text to the clipboard (especially useful on Linux)",
        default=""
    )

    empty_enum_items = (
                        ("PLAIN_AXES", "Plain Axes", "Plain Axes"),
                        ("ARROWS", "Arrows", "Arrows"),
                        ("SINGLE_ARROW", "Single Arrow", "Single Arrow"),
                        ("CIRCLE", "Circle", "Circle"),
                        ("CUBE", "Cube", "Cube"),
                        ("SPHERE", "Sphere", "Sphere"),
                        ("CONE", "Cone", "Cone"),
                        )

    dof_rotate_empty_type: EnumProperty(
        name="Rotate",
        description="The Empty to display a Rotate DOF as",
        items=empty_enum_items,
        default="CIRCLE",
    )

    dof_translate_empty_type: EnumProperty(
        name="Translate",
        description="The Empty to display a Translate DOF as",
        items=empty_enum_items,
        default="PLAIN_AXES",
    )

    dof_scale_empty_type: EnumProperty(
        name="Scale",
        description="The Empty to display a Scale DOF as",
        items=empty_enum_items,
        default="CUBE",
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="External Tools")
        box = layout.box()
        box.prop(self, "editor_path", expand=True)
        box.prop(self, "copy_to_clipboard_command", expand=True)

        layout.separator()
        layout.label(text="DOF Display")
        box = layout.box()
        box.prop(self, "dof_rotate_empty_type")
        box.prop(self, "dof_translate_empty_type")
        box.prop(self, "dof_scale_empty_type")
        box.operator(ApplyEmptyDisplaysToDofs.bl_idname, icon="CHECKMARK")

        layout.separator()
        layout.row().label(text="Debug options")
        layout.row().label(text="Use at your own risk. All options should be OFF by default.", icon="ERROR")
        box = layout.box()
        box.prop(self, "do_not_delete_export_collection", expand=True)
        box.prop(self, "do_not_join_materials", expand=True)


class ApplyEmptyDisplaysToDofs(Operator):
    """Applies the preferences for the DOF empties to all objects in the scene"""
    bl_idname = "bml.apply_empty_displays_to_dofs"
    bl_label = "Apply to all DOFs"
    bl_description = "Applies the display preferences to all DOFs in the scene"

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        rotate_empty = context.preferences.addons["bms_blender_plugin"].preferences.dof_rotate_empty_type
        translate_empty = context.preferences.addons["bms_blender_plugin"].preferences.dof_translate_empty_type
        scale_empty = context.preferences.addons["bms_blender_plugin"].preferences.dof_scale_empty_type

        for obj in bpy.data.objects:
            if get_bml_type(obj) == BlenderNodeType.DOF:
                if obj.dof_type == DofType.ROTATE.name:
                    obj.empty_display_type = rotate_empty
                elif obj.dof_type == DofType.TRANSLATE.name:
                    obj.empty_display_type = translate_empty
                elif obj.dof_type == DofType.SCALE.name:
                    obj.empty_display_type = scale_empty

        return {"FINISHED"}


def register():
    bpy.utils.register_class(ApplyEmptyDisplaysToDofs)
    bpy.utils.register_class(ExporterPreferences)


def unregister():
    bpy.utils.unregister_class(ExporterPreferences)
    bpy.utils.unregister_class(ApplyEmptyDisplaysToDofs)

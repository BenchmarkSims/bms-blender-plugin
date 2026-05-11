import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty
from bpy.types import Operator

from bms_blender_plugin.common.blender_types import BlenderNodeType
from bms_blender_plugin.common.bml_structs import DofType
from bms_blender_plugin.common.util import get_bml_type, get_dofs, get_switches, get_callbacks


class ReloadDofList(Operator):
    """Reload DOF list from DOF.xml file"""
    bl_idname = "bml.reload_dof_list"
    bl_label = "Reload DOF.xml"
    bl_description = "Reload the DOF list from the DOF.xml file. Use this after modifying the XML file"
    bl_options = {"REGISTER"}

    def execute(self, context):
        # Clear the global cache first
        import bms_blender_plugin.common.util as util_module
        util_module.dofs = []
        
        # Clear the cache
        util_module._dofs_hydrated = False
        context.scene.dof_list.clear()
        for dof in get_dofs(force_disk=True): # force_disk to bypass scene cache
            item = context.scene.dof_list.add()
            item.name = dof.name
            item.dof_number = int(dof.dof_number)
        self.report({'INFO'}, f"Reloaded {len(context.scene.dof_list)} DOFs from DOF.xml")
        return {'FINISHED'}


class ReloadSwitchList(Operator):
    """Reload Switch list from switch.xml file"""
    bl_idname = "bml.reload_switch_list"
    bl_label = "Reload switch.xml"
    bl_description = "Reload the Switch list from the switch.xml file. Use this after modifying the XML file"
    bl_options = {"REGISTER"}

    def execute(self, context):
        # Clear the global cache first
        import bms_blender_plugin.common.util as util_module
        util_module.switches = []
        
        # Clear the cache
        util_module._switches_hydrated = False
        context.scene.switch_list.clear()
        for switch in get_switches(force_disk=True): # force_disk to bypass scene cache
            item = context.scene.switch_list.add()
            item.name = switch.name
            item.switch_number = int(switch.switch_number)
            item.branch_number = int(switch.branch)
        self.report({'INFO'}, f"Reloaded {len(context.scene.switch_list)} Switches from switch.xml")
        return {'FINISHED'}


class ReloadCallbackList(Operator):
    """Reload Callback list from callbacks.xml file"""
    bl_idname = "bml.reload_callback_list"
    bl_label = "Reload callbacks.xml"
    bl_description = "Reload the Callback list from the callbacks.xml file. Use this after modifying the XML file"
    bl_options = {"REGISTER"}

    def execute(self, context):
        # Clear the global cache first
        import bms_blender_plugin.common.util as util_module
        util_module.callbacks = []
        
        # Clear the scene cache
        context.scene.bml_all_callbacks.clear()
        
        # Repopulate the scene cache immediately
        for callback in get_callbacks():
            new_callback = context.scene.bml_all_callbacks.add()
            new_callback.name = callback.name
            new_callback.group = callback.group
        
        self.report({'INFO'}, f"Reloaded {len(context.scene.bml_all_callbacks)} Callbacks from callbacks.xml")
        return {'FINISHED'}


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
        default=True,
    )

    prefer_scene_snapshot: BoolProperty(
        name="Prefer Scene Snapshot",
        description="Use scene-cached switch/DOF lists if present. (Recommended)",
        default=True,
    )
    warn_xml_mismatch: BoolProperty(
        name="Warn on XML Mismatch",
        description="Print a console warning if disk XML differs from scene cache.",
        default=True,
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
      
    dof_rotate_empty_size: FloatProperty(
        default=1.0,
        min=0.01,
        name="Size",
        description="The size of the Empty to display a Rotate DOF as"
     )

    dof_translate_empty_type: EnumProperty(
        name="Translate",
        description="The Empty to display a Translate DOF as",
        items=empty_enum_items,
        default="PLAIN_AXES",
    )

    dof_translate_empty_size: FloatProperty(
        default=1.0,
        min=0.01,
        name="Size",
        description="The size of the Empty to display a Translate DOF as"
     )
      
    dof_scale_empty_type: EnumProperty(
        name="Scale",
        description="The Empty to display a Scale DOF as",
        items=empty_enum_items,
        default="CUBE",
    )


    dof_scale_empty_size: FloatProperty(
        default=1.0,
        min=0.01,
        name="Size",
        description="The size of the Empty to display a Scale DOF as"
    )

    switch_empty_type: EnumProperty(
        name="Switch",
        description="The Empty to display a Switch as",
        items=empty_enum_items,
        default="PLAIN_AXES",
    )

    switch_empty_size: FloatProperty(
        default=1.0,
        min=0.01,
        name="Size",
        description="The size of the Empty to display a Switch as"
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
        row = box.row()
        row.prop(self, "dof_rotate_empty_type")
        row.prop(self, "dof_rotate_empty_size")

        row = box.row()
        row.prop(self, "dof_translate_empty_type")
        row.prop(self, "dof_translate_empty_size")

        row = box.row()
        row.prop(self, "dof_scale_empty_type")
        row.prop(self, "dof_scale_empty_size")

        box.operator(ApplyEmptyDisplaysToDofs.bl_idname, icon="CHECKMARK")

        layout.separator()
        layout.label(text="Switch Display")
        box = layout.box()
        row = box.row()
        row.prop(self, "switch_empty_type")
        row.prop(self, "switch_empty_size")

        box.operator(ApplyEmptyDisplaysToSwitches.bl_idname, icon="CHECKMARK")

        layout.separator()
        layout.label(text="Data Management")
        box = layout.box()
        box.operator(ReloadDofList.bl_idname, icon="FILE_REFRESH")
        box.operator(ReloadSwitchList.bl_idname, icon="FILE_REFRESH")
        box.operator(ReloadCallbackList.bl_idname, icon="FILE_REFRESH")
        box.separator()
        box.prop(self, "prefer_scene_snapshot")
        box.prop(self, "warn_xml_mismatch")

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
        rotate_empty_size = context.preferences.addons["bms_blender_plugin"].preferences.dof_rotate_empty_size

        translate_empty = context.preferences.addons["bms_blender_plugin"].preferences.dof_translate_empty_type
        translate_empty_size = context.preferences.addons["bms_blender_plugin"].preferences.dof_translate_empty_size

        scale_empty = context.preferences.addons["bms_blender_plugin"].preferences.dof_scale_empty_type
        scale_empty_size = context.preferences.addons["bms_blender_plugin"].preferences.dof_scale_empty_size

        translate_empty = context.preferences.addons["bms_blender_plugin"].preferences.dof_translate_empty_type
        scale_empty = context.preferences.addons["bms_blender_plugin"].preferences.dof_scale_empty_type

        for obj in bpy.data.objects:
            if get_bml_type(obj) == BlenderNodeType.DOF:
                if obj.dof_type == DofType.ROTATE.name:
                    obj.empty_display_type = rotate_empty
                    obj.empty_display_size = rotate_empty_size

                elif obj.dof_type == DofType.TRANSLATE.name:
                    obj.empty_display_type = translate_empty
                    obj.empty_display_size = translate_empty_size

                elif obj.dof_type == DofType.SCALE.name:
                    obj.empty_display_type = scale_empty
                    obj.empty_display_size = scale_empty_size
                elif obj.dof_type == DofType.TRANSLATE.name:
                    obj.empty_display_type = translate_empty
                elif obj.dof_type == DofType.SCALE.name:
                    obj.empty_display_type = scale_empty

        return {"FINISHED"}


class ApplyEmptyDisplaysToSwitches(Operator):
    """Applies the preferences for the Switch empties to all objects in the scene"""
    bl_idname = "bml.apply_empty_displays_to_switches"
    bl_label = "Apply to all Switches"
    bl_description = "Applies the display preferences to all Switches in the scene"

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        switch_empty = context.preferences.addons[
            "bms_blender_plugin"
        ].preferences.switch_empty_type
        switch_empty_size = context.preferences.addons[
            "bms_blender_plugin"
        ].preferences.switch_empty_size

        for obj in bpy.data.objects:
            if get_bml_type(obj) == BlenderNodeType.SWITCH:
                obj.empty_display_type = switch_empty
                obj.empty_display_size = switch_empty_size

        return {"FINISHED"}


def register():
    bpy.utils.register_class(ReloadDofList)
    bpy.utils.register_class(ReloadSwitchList)
    bpy.utils.register_class(ReloadCallbackList)
    bpy.utils.register_class(ApplyEmptyDisplaysToDofs)
    bpy.utils.register_class(ApplyEmptyDisplaysToSwitches)
    bpy.utils.register_class(ExporterPreferences)


def unregister():
    bpy.utils.unregister_class(ExporterPreferences)
    bpy.utils.unregister_class(ApplyEmptyDisplaysToSwitches)
    bpy.utils.unregister_class(ApplyEmptyDisplaysToDofs)
    bpy.utils.unregister_class(ReloadCallbackList)
    bpy.utils.unregister_class(ReloadSwitchList)
    bpy.utils.unregister_class(ReloadDofList)

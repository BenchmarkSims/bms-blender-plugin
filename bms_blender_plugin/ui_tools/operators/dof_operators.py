import bpy

from bpy.props import StringProperty
from bpy.types import Operator

from bms_blender_plugin.common.blender_types import BlenderNodeType
from bms_blender_plugin.common.util import reset_dof, get_bml_type


class ResetSingleDof(Operator):
    """Resets a single DOFs input to 0"""
    bl_idname = "bml.reset_single_dof"
    bl_label = "Reset single DOF"
    bl_options = {'REGISTER', 'UNDO'}
    dof_to_reset_name: StringProperty(default="")

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        # blender does not allow pointer properties in operator, so we have to find the DOF for ourselves
        if self.dof_to_reset_name in context.scene.objects:
            reset_dof(context.scene.objects[self.dof_to_reset_name])
        return{'FINISHED'}


class ResetAllDofs(Operator):
    """Resets all DOF inputs to 0"""
    bl_idname = "bml.reset_all_dofs"
    bl_label = "Reset all DOFs"
    bl_options = {'REGISTER', 'UNDO'}

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        for obj in context.scene.objects:
            reset_dof(obj)
        return{'FINISHED'}


class CreateDofKeyframe(Operator):
    """Creates a Keyframe for the current DOF"""
    bl_idname = "bml.create_dof_keyframe"
    bl_label = "Create DOF Keyframe"
    bl_options = {'REGISTER', 'UNDO'}
    dof_to_keyframe_name: StringProperty(default="")

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        if self.dof_to_keyframe_name in context.scene.objects:
            dof = context.scene.objects[self.dof_to_keyframe_name]
            if get_bml_type(dof) != BlenderNodeType.DOF:
                return
            dof.keyframe_insert(data_path="dof_input")
        return{'FINISHED'}


class RefreshDofAndSwitchList(Operator):
    """Refreshes the DOF/Switch lists from the XML files"""
    bl_idname = "bml.refresh_dof_switch_list"
    bl_label = "Apply sizes to scene"  # Updated label
    bl_description = "Refreshes the DOF and Switch lists from the XML files and applies sizes from preferences"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        from bms_blender_plugin.common.util import get_dofs, get_switches
        import importlib
        import sys

        # Clear stored lists from the scene
        if 'dof_list' in context.scene:
            del context.scene['dof_list']
        if 'switch_list' in context.scene:
            del context.scene['switch_list']

        # Reload the utility module and clear caches
        util_module = sys.modules['bms_blender_plugin.common.util']
        importlib.reload(util_module)
        if hasattr(get_dofs, 'cache_clear'):
            get_dofs.cache_clear()
        if hasattr(get_switches, 'cache_clear'):
            get_switches.cache_clear()

        # Load the refreshed data
        new_dofs = get_dofs()
        new_switches = get_switches()

        # Get size preferences
        preferences = context.preferences.addons[__name__].preferences
        dof_size = preferences.dof_size
        switch_size = preferences.switch_size

        # Populate scene DOF list
        for dof in new_dofs:
            item = context.scene.dof_list.add()
            item.name = dof.name
            item.dof_number = int(dof.dof_number)
            item.size = dof_size  # Apply size from preferences

        # Populate scene Switch list
        for switch in new_switches:
            item = context.scene.switch_list.add()
            item.name = switch.name
            item.switch_number = int(switch.switch_number)
            item.size = switch_size  # Apply size from preferences

        # Force redraw of all UI areas
        for area in context.screen.areas:
            if area.type == 'PROPERTIES':  # Adjust this to the correct area type if needed
                area.tag_redraw()

        self.report({'INFO'}, "DOF and Switch lists refreshed and sizes applied")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(ResetSingleDof)
    bpy.utils.register_class(ResetAllDofs)
    bpy.utils.register_class(CreateDofKeyframe)
    bpy.utils.register_class(RefreshDofAndSwitchList)


def unregister():
    bpy.utils.unregister_class(CreateDofKeyframe)
    bpy.utils.unregister_class(ResetAllDofs)
    bpy.utils.unregister_class(ResetSingleDof)
    bpy.utils.unregister_class(RefreshDofAndSwitchList)

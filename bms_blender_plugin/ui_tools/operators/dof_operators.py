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


class RefreshDofList(Operator):
    """Refreshes the DOF/Switch lists from the XML files"""
    bl_idname = "bml.refresh_dof_list"
    bl_label = "Refresh DOF/Switch Lists" 
    bl_description = "Refreshes the DOF and Switch lists from the XML files"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        # Import needed modules
        from bms_blender_plugin.common.util import get_dofs, get_switches
        import importlib
        import sys
        
        # Clear stored lists from scene
        if 'dof_list' in context.scene:
            del context.scene['dof_list']
            self.report({'INFO'}, "DOF list cleared from scene")
        
        if 'switch_list' in context.scene:
            del context.scene['switch_list']
            self.report({'INFO'}, "Switch list cleared from scene")
        
        # Force reload of the utility module that loads the XML files
        # This is more thorough than just calling cache_clear()
        util_module = sys.modules['bms_blender_plugin.common.util']
        
        # Reset the module's global variables that store the lists
        if hasattr(util_module, 'dofs'):
            util_module.dofs = None
        if hasattr(util_module, 'switches'):
            util_module.switches = None
            
        # Force Python to reload the module from disk
        importlib.reload(util_module)
        
        # Reset any function caches
        if hasattr(get_dofs, 'cache_clear'):
            get_dofs.cache_clear()
        if hasattr(get_switches, 'cache_clear'):
            get_switches.cache_clear()
        
        # Force immediate reloading of the data
        dofs = get_dofs()
        _ = get_switches()
        
        # Reset DOF indices for all DOF objects in the scene
        for obj in bpy.data.objects:
            if get_bml_type(obj) == BlenderNodeType.DOF:
                # Reset to a valid value or -1 to indicate unset
                obj.dof_list_index = -1
        
        # Clear DofMediator cache to ensure DOFs use the updated definitions
        from bms_blender_plugin.ui_tools.dof_behaviour import DofMediator
        DofMediator.rebuild_cache()
        
        # Force scene update to make sure DOFs are properly initialized
        context.view_layer.update()
        
        # Force redraw of all UI areas
        for area in context.screen.areas:
            area.tag_redraw()
        
        self.report({'INFO'}, "DOF and Switch lists refreshed from XML files")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(ResetSingleDof)
    bpy.utils.register_class(ResetAllDofs)
    bpy.utils.register_class(CreateDofKeyframe)
    bpy.utils.register_class(RefreshDofList)


def unregister():
    bpy.utils.unregister_class(CreateDofKeyframe)
    bpy.utils.unregister_class(ResetAllDofs)
    bpy.utils.unregister_class(ResetSingleDof)
    bpy.utils.unregister_class(RefreshDofList)

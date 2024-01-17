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


def register():
    bpy.utils.register_class(ResetSingleDof)
    bpy.utils.register_class(ResetAllDofs)
    bpy.utils.register_class(CreateDofKeyframe)


def unregister():
    bpy.utils.unregister_class(CreateDofKeyframe)
    bpy.utils.unregister_class(ResetAllDofs)
    bpy.utils.unregister_class(ResetSingleDof)

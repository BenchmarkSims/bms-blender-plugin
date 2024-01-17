import bpy
from bpy.types import Operator

from bms_blender_plugin.common.blender_types import BlenderNodeType
from bms_blender_plugin.common.util import get_dofs
from bms_blender_plugin.nodes_editor.dof_editor import DofNodeTree


class CreateDof(Operator):
    bl_idname = "bml.create_dof"
    bl_label = "Create DOF"
    bl_description = "Adds a new DOF to the scene"
    bl_options = {"REGISTER", "UNDO"}

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        # read all DOF values from the XML file and store them in the active scene
        if len(context.scene.dof_list) == 0:
            for dof in get_dofs():
                item = context.scene.dof_list.add()
                item.name = dof.name
                item.dof_number = int(dof.dof_number)

        dof = get_dofs()[0]
        dof_object = bpy.data.objects.new(f"DOF - {dof.name} ({dof.dof_number})", None)
        dof_object.bml_type = str(BlenderNodeType.DOF)
        dof_object.empty_display_type = context.preferences.addons[
            "bms_blender_plugin"
        ].preferences.dof_rotate_empty_type

        dof_object.empty_display_size = 1

        if context.active_object:
            # assumes that every object is linked to at least one collection
            context.active_object.users_collection[0].objects.link(dof_object)
            dof_object.parent = context.active_object.parent
            dof_object.matrix_world.translation = (
                context.active_object.matrix_world.translation
            )
        else:
            context.collection.objects.link(dof_object)

        # move any selected objects to the new DOF
        for obj in context.selected_objects:
            if obj == dof_object:
                continue
            obj.parent = dof_object
            obj.parent_type = "OBJECT"
            obj.matrix_parent_inverse = dof_object.matrix_world.inverted()

        # select the new object
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = dof_object
        dof_object.select_set(True)

        if DofNodeTree.bl_label in bpy.data.node_groups.keys():
            dof_node_tree = bpy.data.node_groups[DofNodeTree.bl_label]
        else:
            dof_node_tree = bpy.data.node_groups.new(
                DofNodeTree.bl_label, "DofNodeTree"
            )

        dof_node = dof_node_tree.nodes.new("NodeDofModelInput")
        dof_node.parent_dof = dof_object
        dof_node.label = dof_object.name

        return {"FINISHED"}


def menu_func(self, context):
    self.layout.operator(CreateDof.bl_idname, text=CreateDof.bl_label)


def register():
    bpy.utils.register_class(CreateDof)
    bpy.types.VIEW3D_MT_object.append(menu_func)


def unregister():
    bpy.utils.unregister_class(CreateDof)
    bpy.types.VIEW3D_MT_object.remove(menu_func)

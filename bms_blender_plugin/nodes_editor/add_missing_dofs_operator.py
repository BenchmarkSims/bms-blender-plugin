import bpy

from bms_blender_plugin.common.blender_types import BlenderNodeType, BlenderEditorNodeType
from bms_blender_plugin.common.util import get_bml_type
from bms_blender_plugin.nodes_editor.dof_editor import DofNodeTree
from bms_blender_plugin.nodes_editor.util import (
    get_bml_node_type,
    get_farthest_x_location,
)


class AddMissingDofsOperator(bpy.types.Operator):
    """Adds a DOF node for each 3d DOF (i.e. a custom Empty object in Blender 3d) if it is not currently defined in the
    DOF Node Tree."""

    bl_idname = "bml.add_missing_dofs"
    bl_label = "Add missing DOFs"
    bl_description = "Adds nodes for all DOFs which have no node"
    bl_options = {'REGISTER', 'UNDO'}

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        if DofNodeTree.bl_label in bpy.data.node_groups.keys():
            dof_node_tree = bpy.data.node_groups[DofNodeTree.bl_label]
        else:
            dof_node_tree = bpy.data.node_groups.new(
                DofNodeTree.bl_label, "DofNodeTree"
            )

        dofs_with_nodes = []

        last_location_x = get_farthest_x_location(dof_node_tree)

        for node in dof_node_tree.nodes:
            if get_bml_node_type(node) == BlenderEditorNodeType.DOF_MODEL and node.parent_dof:
                dofs_with_nodes.append(node.parent_dof)

        for obj in context.scene.objects:
            if get_bml_type(obj) == BlenderNodeType.DOF and obj not in dofs_with_nodes:
                dof_node = dof_node_tree.nodes.new("NodeDofModelInput")
                dof_node.parent_dof = obj
                dof_node.label = obj.name

                last_location_x += 50 + dof_node.width
                dof_node.location.x = last_location_x

        return {"FINISHED"}


def draw_header(self, context):
    if context.area.ui_type == 'DofNodeTree' and context.space_data.node_tree is not None:
        layout = self.layout
        layout.separator(factor=0.5)

        layout.operator(AddMissingDofsOperator.bl_idname, icon='ADD')


def register():
    bpy.utils.register_class(AddMissingDofsOperator)
    bpy.types.NODE_MT_editor_menus.append(draw_header)


def unregister():
    bpy.utils.unregister_class(AddMissingDofsOperator)
    bpy.types.NODE_MT_editor_menus.remove(draw_header)

import bpy

from bms_blender_plugin.nodes_editor import MaterialNode
from bms_blender_plugin.nodes_editor.dof_editor import DofNodeTree
from bms_blender_plugin.nodes_editor.material_editor import MaterialNodeTree
from bms_blender_plugin.nodes_editor.util import (
    get_bml_node_type,
    get_farthest_x_location,
)


class AddMissingMaterialsOperator(bpy.types.Operator):
    """Adds material nodes for all Blender Materials in a scene which don't have a corresponding material node in the
    BML Material Node Tree. Also makes sure that those nodes use the custom Shader Tree."""

    bl_idname = "bml.add_missing_materials"
    bl_label = "Add missing Materials"
    bl_description = "Adds Materials which have no node"
    bl_options = {'REGISTER', 'UNDO'}

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        if MaterialNodeTree.bl_label in bpy.data.node_groups.keys():
            material_node_tree = bpy.data.node_groups[MaterialNodeTree.bl_label]
        else:
            material_node_tree = bpy.data.node_groups.new(
                DofNodeTree.bl_label, MaterialNodeTree.__name__
            )

        materials_with_nodes = []

        last_location_x = get_farthest_x_location(material_node_tree)
        for node in material_node_tree.nodes:
            if get_bml_node_type(node).MATERIAL and node.material:
                materials_with_nodes.append(node.material)

        for material in bpy.data.materials:
            if material not in materials_with_nodes:
                material_node = material_node_tree.nodes.new(MaterialNode.__name__)
                material_node.material = material
                material_node.label = material.name

                last_location_x += 50 + material_node.width
                material_node.location.x = last_location_x

        return {"FINISHED"}


def draw_header(self, context):
    if context.area.ui_type == 'MaterialNodeTree' and context.space_data.node_tree is not None:
        layout = self.layout
        layout.separator(factor=0.5)

        layout.operator(AddMissingMaterialsOperator.bl_idname, icon='ADD')


def register():
    bpy.utils.register_class(AddMissingMaterialsOperator)
    bpy.types.NODE_MT_editor_menus.append(draw_header)


def unregister():
    bpy.utils.unregister_class(AddMissingMaterialsOperator)
    bpy.types.NODE_MT_editor_menus.remove(draw_header)

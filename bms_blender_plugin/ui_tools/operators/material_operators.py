import bpy
from bms_blender_plugin.common.bml_material import BlendLocation, BlendOperation
from bms_blender_plugin.nodes_editor.util import get_bml_node_type
from bms_blender_plugin.common.blender_types import BlenderEditorNodeType
from bms_blender_plugin.common.bml_material import MaterialTemplate

class OptimizeGlassMaterialOperator(bpy.types.Operator):
    """Sets optimal properties for glass materials to avoid visual artifacts"""
    bl_idname = "bml.optimize_glass_material"
    bl_label = "Optimize Glass Material"
    bl_description = "Configure this material for optimal glass rendering"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_node and get_bml_node_type(context.active_node) == BlenderEditorNodeType.MATERIAL

    def execute(self, context):
        node = context.active_node

        # Set blending properties
        node.blend_enabled = True
        node.blend_src = BlendLocation.SRC_ALPHA.name
        node.blend_dest = BlendLocation.INV_SRC_ALPHA.name
        node.blend_op = BlendOperation.ADD.name
        node.blend_alpha_src = BlendLocation.ONE.name
        node.blend_alpha_dest = BlendLocation.INV_SRC_ALPHA.name
        node.blend_alpha_op = BlendOperation.ADD.name

        # Enable alpha sorting
        node.alpha_sort_triangles = True

        # Use the PBR-Glass template
        if "PBR-Glass" in MaterialTemplate.get_templates():
            node.templates = "PBR-Glass"

        self.report({'INFO'}, "Material optimized for glass rendering")
        return {'FINISHED'}
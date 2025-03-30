import bpy

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
        # Set glass properties
        node.blend_enabled = True
        node.blend_src = BlendLocation.SRC_ALPHA.name
        node.blend_dest = BlendLocation.INV_SRC_ALPHA.name
        node.blend_op = BlendOperation.ADD.name
        node.blend_alpha_src = BlendLocation.ONE.name
        node.blend_alpha_dest = BlendLocation.INV_SRC_ALPHA.name
        node.blend_alpha_op = BlendOperation.ADD.name
        
        # Enable alpha sorting for this material
        node.alpha_sort_triangles = True
        
        # Use a glass template if available
        if "PBR-OptimizedGlass" in MaterialTemplate.get_templates():
            node.templates = "PBR-OptimizedGlass"
        elif "PBR-Glass" in MaterialTemplate.get_templates():
            node.templates = "PBR-Glass"
            
        self.report({'INFO'}, "Material optimized for glass rendering")
        return {'FINISHED'}
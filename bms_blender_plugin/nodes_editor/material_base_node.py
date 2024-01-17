from bpy.types import Node


class MaterialBaseNode(Node):
    """The base node for the MaterialNodeTree. Does not need any execution since we don't display anything in 3D"""
    bl_label = "BMS Material Node"
    bl_icon = "MATERIAL"

    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == "MaterialNodeTree"

    def execute(self, context):
        pass

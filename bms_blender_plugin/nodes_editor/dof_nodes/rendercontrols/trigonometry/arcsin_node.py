import bpy
import math

from bms_blender_plugin.common.bml_structs import MathOp
from bms_blender_plugin.nodes_editor.dof_base_node import subscribe_node, unsubscribe_node
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.base_render_control import BaseRenderControl


class NodeDofArcSin(BaseRenderControl):
    bl_label = "Arcsin"
    bl_description = "arcsin(x)"
    bl_icon = "DRIVER_TRANSFORM"

    def __init__(self):
        super().__init__(MathOp.ASIN)
    
    def init(self, context):
        self.init_sockets(self.bl_label, ["x"])

    def execute(self, context):
        self.fetch_arguments()
        self.clear_argument_error(self.result)

        x = self.get_argument_value("x")
        if x < -1 or x > 1:
            self.set_argument_error(self.result, "invalid value for x")
            self.bl_icon = "ERROR"
            return

        result = math.asin(x)

        self.outputs[self.result.name].default_value = result
        self.result.value = result
        self.bl_icon = "DRIVER_TRANSFORM"


def register():
    bpy.utils.register_class(NodeDofArcSin)
    subscribe_node(NodeDofArcSin)


def unregister():
    unsubscribe_node(NodeDofArcSin)
    bpy.utils.unregister_class(NodeDofArcSin)

import bpy
import math

from bms_blender_plugin.common.bml_structs import MathOp
from bms_blender_plugin.nodes_editor.dof_base_node import subscribe_node, unsubscribe_node
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.base_render_control import BaseRenderControl


class NodeDofArcTan2(BaseRenderControl):
    bl_label = "Arctan2"
    bl_description = "arctan2(x)"
    bl_icon = "DRIVER_TRANSFORM"

    def __init__(self):
        super().__init__(MathOp.ATAN2)
    
    def init(self, context):
        self.init_sockets(self.bl_label, ["x", "y"])

    def execute(self, context):
        self.fetch_arguments()
        self.clear_argument_error(self.result)

        x = self.get_argument_value("x")
        y = self.get_argument_value("y")

        if x == 0:
            self.set_argument_error(self.result, "invalid value for x")
            self.bl_icon = "ERROR"
            return

        if y == 0:
            self.set_argument_error(self.result, "invalid value for y")
            self.bl_icon = "ERROR"
            return

        result = math.atan2(x, y)

        self.outputs[self.result.name].default_value = result
        self.result.value = result
        self.bl_icon = "DRIVER_TRANSFORM"



def register():
    bpy.utils.register_class(NodeDofArcTan2)
    subscribe_node(NodeDofArcTan2)


def unregister():
    unsubscribe_node(NodeDofArcTan2)
    bpy.utils.unregister_class(NodeDofArcTan2)

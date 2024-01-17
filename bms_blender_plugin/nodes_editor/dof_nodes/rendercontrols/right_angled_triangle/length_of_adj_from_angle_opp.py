import bpy
import math

from bms_blender_plugin.common.bml_structs import MathOp
from bms_blender_plugin.nodes_editor.dof_base_node import subscribe_node, unsubscribe_node
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.base_render_control import BaseRenderControl


class NodeDofLengthOfAdjFromAngleOpp(BaseRenderControl):
    bl_label = "Length of Adjacent from angle and the Opposite"
    bl_description = "Length of Adjacent from angle and the Opposite"
    bl_icon = "DRIVER_TRANSFORM"

    def __init__(self):
        super().__init__(MathOp.LENGTHOFADJ_FROM_ANGLE_OPP)
    
    def init(self, context):
        self.init_sockets(self.bl_label, ["Angle", "Opposite"])

    def execute(self, context):
        self.clear_argument_error(self.result)
        self.fetch_arguments()

        angle = self.get_argument_value("Angle")
        opposite = self.get_argument_value("Opposite")

        t = math.tan(angle)
        if t == 0:
            self.set_argument_error(self.result, "invalid argument")
            self.bl_icon = "ERROR"
            return

        result = opposite / t

        self.outputs[self.result.name].default_value = result
        self.result.value = result
        self.bl_icon = "DRIVER_TRANSFORM"


def register():
    bpy.utils.register_class(NodeDofLengthOfAdjFromAngleOpp)
    subscribe_node(NodeDofLengthOfAdjFromAngleOpp)


def unregister():
    unsubscribe_node(NodeDofLengthOfAdjFromAngleOpp)
    bpy.utils.unregister_class(NodeDofLengthOfAdjFromAngleOpp)

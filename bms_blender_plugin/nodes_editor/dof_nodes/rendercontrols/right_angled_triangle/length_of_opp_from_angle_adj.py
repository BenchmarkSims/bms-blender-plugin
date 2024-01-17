import bpy
import math

from bms_blender_plugin.common.bml_structs import MathOp
from bms_blender_plugin.nodes_editor.dof_base_node import subscribe_node, unsubscribe_node
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.base_render_control import BaseRenderControl


class NodeDofLengthOfOppFromAngleAdj(BaseRenderControl):
    bl_label = "Length of Opposite from angle and the Adjacent"
    bl_description = "Length of Opposite from angle and the Adjacent"
    bl_icon = "DRIVER_TRANSFORM"

    def __init__(self):
        super().__init__(MathOp.LENGTHOFOPP_FROM_ANGLE_ADJ)
    
    def init(self, context):
        self.init_sockets(self.bl_label, ["Angle", "Adjacent"])

    def execute(self, context):
        self.clear_argument_error(self.result)
        self.fetch_arguments()

        angle = self.get_argument_value("Angle")
        adjacent = self.get_argument_value("Adjacent")

        result = math.atan(angle) * adjacent

        self.outputs[self.result.name].default_value = result
        self.result.value = result


def register():
    bpy.utils.register_class(NodeDofLengthOfOppFromAngleAdj)
    subscribe_node(NodeDofLengthOfOppFromAngleAdj)


def unregister():
    unsubscribe_node(NodeDofLengthOfOppFromAngleAdj)
    bpy.utils.unregister_class(NodeDofLengthOfOppFromAngleAdj)

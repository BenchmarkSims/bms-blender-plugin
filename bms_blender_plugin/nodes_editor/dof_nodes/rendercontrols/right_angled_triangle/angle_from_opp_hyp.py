import bpy
import math

from bms_blender_plugin.common.bml_structs import MathOp
from bms_blender_plugin.nodes_editor.dof_base_node import subscribe_node, unsubscribe_node
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.base_render_control import BaseRenderControl


class NodeDofAngleFromOpHyp(BaseRenderControl):
    bl_label = "Angle between Opposite and Hypotenuse"
    bl_description = "Angle between Opposite and Hypotenuse"
    bl_icon = "DRIVER_TRANSFORM"

    def __init__(self):
        super().__init__(MathOp.ANGLE_FROM_OPP_HYP)
    
    def init(self, context):
        self.init_sockets(self.bl_label, ["Opposite", "Hypotenuse"])

    def execute(self, context):
        self.clear_argument_error(self.result)
        self.fetch_arguments()

        opposite = self.get_argument_value("Opposite")
        hypotenuse = self.get_argument_value("Hypotenuse")

        if hypotenuse == 0 or (opposite/hypotenuse) < -1 or (opposite/hypotenuse) > 1:
            self.set_argument_error(self.result, "invalid argument")
            self.bl_icon = "ERROR"
            return

        result = math.asin(opposite/hypotenuse)

        self.outputs[self.result.name].default_value = result
        self.result.value = result
        self.bl_icon = "DRIVER_TRANSFORM"


def register():
    bpy.utils.register_class(NodeDofAngleFromOpHyp)
    subscribe_node(NodeDofAngleFromOpHyp)


def unregister():
    unsubscribe_node(NodeDofAngleFromOpHyp)
    bpy.utils.unregister_class(NodeDofAngleFromOpHyp)

import bpy
import math

from bms_blender_plugin.common.bml_structs import MathOp
from bms_blender_plugin.nodes_editor.dof_base_node import subscribe_node, unsubscribe_node
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.base_render_control import (
    BaseRenderControl,
)


class NodeDofAngleAFromSideASideBSideC(BaseRenderControl):
    bl_label = "Angle A from Side a, Side b, Side c"
    bl_description = "Angle A from Side a, Side b, Side c"
    bl_icon = "DRIVER_TRANSFORM"

    def __init__(self):
        super().__init__(MathOp.ANGLEA_FROM_SIDEA_SIDEB_SIDEC)

    def init(self, context):
        self.init_sockets(self.bl_label, ["a", "b", "c"])

    def execute(self, context):
        self.clear_argument_error(self.result)
        self.fetch_arguments()

        a = self.get_argument_value("a")
        b = self.get_argument_value("b")
        c = self.get_argument_value("c")

        if a == 0 or b == 0 or c == 0:
            self.set_argument_error(self.result, "invalid argument")
            self.bl_icon = "ERROR"
            return

        result = math.acos((-a * a + b * b + c * c) / (2 * b * c))

        self.outputs[self.result.name].default_value = result
        self.result.value = result
        self.bl_icon = "DRIVER_TRANSFORM"


def register():
    bpy.utils.register_class(NodeDofAngleAFromSideASideBSideC)
    subscribe_node(NodeDofAngleAFromSideASideBSideC)


def unregister():
    unsubscribe_node(NodeDofAngleAFromSideASideBSideC)
    bpy.utils.unregister_class(NodeDofAngleAFromSideASideBSideC)

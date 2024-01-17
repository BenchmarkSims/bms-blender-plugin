import bpy
import math

from bms_blender_plugin.common.bml_structs import MathOp
from bms_blender_plugin.nodes_editor.dof_base_node import subscribe_node, unsubscribe_node
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.base_render_control import (
    BaseRenderControl,
)


class NodeDofSideAFromAngleASideBSideC(BaseRenderControl):
    bl_label = "Side a from Angle A, Side b, Side c"
    bl_description = "Side a from Angle A, Side b, Side c"
    bl_icon = "DRIVER_TRANSFORM"

    def __init__(self):
        super().__init__(MathOp.SIDEA_FROM_ANGLEA_SIDEB_SIDEC)

    def init(self, context):
        self.init_sockets(self.bl_label, ["A", "b", "c"])

    def execute(self, context):
        self.clear_argument_error(self.result)
        self.fetch_arguments()

        A = self.get_argument_value("A")
        b = self.get_argument_value("b")
        c = self.get_argument_value("c")

        if A == 0 or b <= 0 or c <= 0:
            self.set_argument_error(self.result, "invalid argument")
            self.bl_icon = "ERROR"
            return

        result = math.sqrt(b * b + c * c - (2 * b * c * math.cos(A)))

        self.outputs[self.result.name].default_value = result
        self.result.value = result
        self.bl_icon = "DRIVER_TRANSFORM"


def register():
    bpy.utils.register_class(NodeDofSideAFromAngleASideBSideC)
    subscribe_node(NodeDofSideAFromAngleASideBSideC)


def unregister():
    unsubscribe_node(NodeDofSideAFromAngleASideBSideC)
    bpy.utils.unregister_class(NodeDofSideAFromAngleASideBSideC)

import bpy
import math

from bms_blender_plugin.common.bml_structs import MathOp
from bms_blender_plugin.nodes_editor.dof_base_node import subscribe_node, unsubscribe_node
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.base_render_control import (
    BaseRenderControl,
)


class NodeDofAngleAFromAngleBSideASideB(BaseRenderControl):
    bl_label = "Angle A from Angle B, Side a, Side b"
    bl_description = "Angle A from Angle B, Side a, Side b"
    bl_icon = "DRIVER_TRANSFORM"

    def __init__(self):
        super().__init__(MathOp.ANGLEA_FROM_ANGLEB_SIDEA_SIDEB)

    def init(self, context):
        self.init_sockets(self.bl_label, ["B", "a", "b"])

    def execute(self, context):
        self.clear_argument_error(self.result)
        self.fetch_arguments()

        B = self.get_argument_value("B")
        a = self.get_argument_value("a")
        b = self.get_argument_value("b")

        if a == 0 or math.sin(B) == 0:
            self.set_argument_error(self.result, "invalid argument")
            self.bl_icon = "ERROR"
            return

        result = math.asin(b / math.sin(B) / a)

        self.outputs[self.result.name].default_value = result
        self.result.value = result
        self.bl_icon = "DRIVER_TRANSFORM"


def register():
    bpy.utils.register_class(NodeDofAngleAFromAngleBSideASideB)
    subscribe_node(NodeDofAngleAFromAngleBSideASideB)


def unregister():
    unsubscribe_node(NodeDofAngleAFromAngleBSideASideB)
    bpy.utils.unregister_class(NodeDofAngleAFromAngleBSideASideB)

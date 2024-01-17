import bpy
import math

from bms_blender_plugin.common.bml_structs import MathOp
from bms_blender_plugin.nodes_editor.dof_base_node import subscribe_node, unsubscribe_node
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.base_render_control import (
    BaseRenderControl,
)


class NodeDofAngleAFromAngleBSideASideC(BaseRenderControl):
    bl_label = "Angle A from Angle B, Side a, Side c"
    bl_description = "Angle A from Angle B, Side a, Side c"
    bl_icon = "DRIVER_TRANSFORM"

    def __init__(self):
        super().__init__(MathOp.ANGLEA_FROM_ANGLEB_SIDEA_SIDEC)

    def init(self, context):
        self.init_sockets(self.bl_label, ["B", "a", "c"])

    def execute(self, context):
        self.clear_argument_error(self.result)
        self.fetch_arguments()

        B = self.get_argument_value("B")
        a = self.get_argument_value("a")
        c = self.get_argument_value("c")

        c2 = math.cos(B) * a
        c1 = c - c2
        d = math.tan(B) * c2

        if d == 0 or c1 == 0:
            self.set_argument_error(self.result, "invalid argument")
            self.bl_icon = "ERROR"
            return

        result = math.atan2(d, c1)

        self.outputs[self.result.name].default_value = result
        self.result.value = result
        self.bl_icon = "DRIVER_TRANSFORM"


def register():
    bpy.utils.register_class(NodeDofAngleAFromAngleBSideASideC)
    subscribe_node(NodeDofAngleAFromAngleBSideASideC)


def unregister():
    unsubscribe_node(NodeDofAngleAFromAngleBSideASideC)
    bpy.utils.unregister_class(NodeDofAngleAFromAngleBSideASideC)

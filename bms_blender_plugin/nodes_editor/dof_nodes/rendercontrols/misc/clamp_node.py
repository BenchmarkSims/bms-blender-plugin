import bpy

from bms_blender_plugin.common.bml_structs import MathOp
from bms_blender_plugin.nodes_editor.dof_base_node import unsubscribe_node, subscribe_node
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.base_render_control import (
    BaseRenderControl,
)


class NodeDofClamp(BaseRenderControl):
    bl_label = "Clamp"
    bl_description = "clamp(value, min, max)"
    bl_icon = "DRIVER_TRANSFORM"


    def __init__(self):
        super().__init__(MathOp.CLAMP)

    def init(self, context):
        self.init_sockets(self.bl_label, ["value", "min", "max"])

    def execute(self, context):
        self.clear_argument_error(self.result)
        self.fetch_arguments()

        value = self.get_argument_value("value")
        minimum = self.get_argument_value("min")
        maximum = self.get_argument_value("max")

        if minimum > maximum:
            self.set_argument_error(self.result, "min > max")
            self.bl_icon = "ERROR"
            return

        # straight from the BMS source (I would have used npy.clip() ...)
        result = value
        if result < minimum:
            result = minimum
        elif result > maximum:
            result = maximum

        self.result.value = result
        self.outputs[self.result.name].default_value = result
        self.bl_icon = "DRIVER_TRANSFORM"


def register():
    bpy.utils.register_class(NodeDofClamp)
    subscribe_node(NodeDofClamp)


def unregister():
    unsubscribe_node(NodeDofClamp)
    bpy.utils.unregister_class(NodeDofClamp)

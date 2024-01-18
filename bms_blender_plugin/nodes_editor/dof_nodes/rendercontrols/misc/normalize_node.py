import bpy

from bms_blender_plugin.common.bml_structs import MathOp
from bms_blender_plugin.nodes_editor.dof_base_node import unsubscribe_node, subscribe_node
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.base_render_control import (
    BaseRenderControl,
)


class NodeDofNormalize(BaseRenderControl):
    bl_label = "Normalize"
    bl_description = "normalize(value, min, max)"
    bl_icon = "DRIVER_TRANSFORM"
    
    def __init__(self):
        super().__init__(MathOp.NORMALIZE)

    def init(self, context):
        self.init_sockets(self.bl_label, ["value", "min", "max"])

    def execute(self, context):
        self.clear_argument_error(self.result)
        self.fetch_arguments()

        value = self.get_argument_value("value")
        minimum = self.get_argument_value("min")
        maximum = self.get_argument_value("max")

        if minimum == maximum:
            self.set_argument_error(self.result, "min = max")
            self.bl_icon = "ERROR"
            return

        result = value - minimum
        result = result / (maximum - minimum)
        if result < 0:
            result = 0
        elif result > 1:
            result = 1

        self.result.value = result
        self.outputs[self.result.name].default_value = result
        self.bl_icon = "DRIVER_TRANSFORM"


def register():
    bpy.utils.register_class(NodeDofNormalize)
    subscribe_node(NodeDofNormalize)


def unregister():
    unsubscribe_node(NodeDofNormalize)
    bpy.utils.unregister_class(NodeDofNormalize)

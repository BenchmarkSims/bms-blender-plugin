import math

import bpy

from bms_blender_plugin.common.bml_structs import MathOp
from bms_blender_plugin.nodes_editor.dof_base_node import unsubscribe_node, subscribe_node
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.base_render_control import (
    BaseRenderControl,
)


class NodeDofStep(BaseRenderControl):
    bl_label = "Step"
    bl_description = "step"
    bl_icon = "DRIVER_TRANSFORM"

    def __init__(self):
        super().__init__(MathOp.STEP)

    def init(self, context):
        self.init_sockets(self.bl_label, ["value", "step-size"])

    def execute(self, context):
        self.clear_argument_error(self.result)
        self.fetch_arguments()

        value = self.get_argument_value("value")
        step_size = self.get_argument_value("step-size")

        if step_size == 0:
            self.set_argument_error(self.result, "step-size must not be 0")
            self.bl_icon = "ERROR"
            return

        result = value - math.fmod(value, step_size)

        self.result.value = result
        self.outputs[self.result.name].default_value = result
        self.bl_icon = "DRIVER_TRANSFORM"


def register():
    bpy.utils.register_class(NodeDofStep)
    subscribe_node(NodeDofStep)


def unregister():
    unsubscribe_node(NodeDofStep)
    bpy.utils.unregister_class(NodeDofStep)

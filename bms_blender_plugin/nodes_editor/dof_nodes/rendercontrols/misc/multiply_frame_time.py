import bpy

from bms_blender_plugin.common.bml_structs import MathOp
from bms_blender_plugin.nodes_editor.dof_base_node import unsubscribe_node, subscribe_node
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.base_render_control import (
    BaseRenderControl,
)


class NodeDofMultiplyFrameTime(BaseRenderControl):
    bl_label = "Multiply by FrameTime"
    bl_description = "value * FrameTime"
    bl_icon = "DRIVER_TRANSFORM"

    def __init__(self):
        super().__init__(MathOp.MULTFRAMETIME)

    def init(self, context):
        self.init_sockets(self.bl_label, ["value"])

    def execute(self, context):
        self.clear_argument_error(self.result)
        self.fetch_arguments()

        value = self.get_argument_value("value")

        # we can not simulate this outside of BMS, just pass it through
        result = value

        self.result.value = result
        self.outputs[self.result.name].default_value = result


def register():
    bpy.utils.register_class(NodeDofMultiplyFrameTime)
    subscribe_node(NodeDofMultiplyFrameTime)


def unregister():
    unsubscribe_node(NodeDofMultiplyFrameTime)
    bpy.utils.unregister_class(NodeDofMultiplyFrameTime)

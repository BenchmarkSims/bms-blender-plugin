import bpy

from bms_blender_plugin.common.bml_structs import MathOp
from bms_blender_plugin.nodes_editor.dof_base_node import unsubscribe_node, subscribe_node
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.base_render_control import (
    BaseRenderControl,
)


class NodeDofSet(BaseRenderControl):
    bl_label = "Set"
    bl_description = "result"
    bl_icon = "DRIVER_TRANSFORM"

    def __init__(self):
        super().__init__(MathOp.SET)

    def init(self, context):
        self.init_sockets(self.bl_label, ["value"])

    def execute(self, context):
        self.clear_argument_error(self.result)
        self.fetch_arguments()

        value = self.get_argument_value("value")
        result = value

        self.result.value = result
        self.outputs[self.result.name].default_value = result


def register():
    bpy.utils.register_class(NodeDofSet)
    subscribe_node(NodeDofSet)


def unregister():
    unsubscribe_node(NodeDofSet)
    bpy.utils.unregister_class(NodeDofSet)

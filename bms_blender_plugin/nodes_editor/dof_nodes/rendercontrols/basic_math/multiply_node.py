import bpy

from bms_blender_plugin.common.bml_structs import MathOp
from bms_blender_plugin.nodes_editor.dof_base_node import unsubscribe_node, subscribe_node
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.base_render_control import BaseRenderControl


class NodeDofMultiply(BaseRenderControl):
    bl_label = "Multiply"
    bl_description = "a * b"
    bl_icon = "DRIVER_TRANSFORM"

    def __init__(self):
        super().__init__(MathOp.MULTIPLY)
    
    def init(self, context):
        self.init_sockets(self.bl_label, ["a", "b"])

    def execute(self, context):
        self.fetch_arguments()

        a = self.get_argument_value("a")
        b = self.get_argument_value("b")
        result = a * b

        self.result.value = result
        self.outputs[self.result.name].default_value = result


def register():
    bpy.utils.register_class(NodeDofMultiply)
    subscribe_node(NodeDofMultiply)


def unregister():
    unsubscribe_node(NodeDofMultiply)
    bpy.utils.unregister_class(NodeDofMultiply)

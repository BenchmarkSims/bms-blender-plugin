import bpy

from bms_blender_plugin.common.bml_structs import MathOp
from bms_blender_plugin.nodes_editor.dof_base_node import unsubscribe_node, subscribe_node
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.base_render_control import BaseRenderControl


class NodeDofDivide(BaseRenderControl):
    bl_label = "Divide"
    bl_description = "a / b"
    bl_icon = "DRIVER_TRANSFORM"
    
    def __init__(self):
        super().__init__(MathOp.DIVIDE)
    
    def init(self, context):
        self.init_sockets(self.bl_label, ["a", "b"])

    def execute(self, context):
        self.clear_argument_error(self.result)
        self.fetch_arguments()

        a = self.get_argument_value("a")
        b = self.get_argument_value("b")

        if b == 0:
            self.set_argument_error(self.result, "division by 0")
            self.bl_icon = "ERROR"
            return
        result = a / b

        self.result.value = result
        self.outputs[self.result.name].default_value = result
        self.bl_icon = "DRIVER_TRANSFORM"


def register():
    bpy.utils.register_class(NodeDofDivide)
    subscribe_node(NodeDofDivide)


def unregister():
    unsubscribe_node(NodeDofDivide)
    bpy.utils.unregister_class(NodeDofDivide)

import bpy
import math

from bms_blender_plugin.common.bml_structs import MathOp
from bms_blender_plugin.nodes_editor.dof_base_node import subscribe_node, unsubscribe_node
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.base_render_control import BaseRenderControl


class NodeDofSin(BaseRenderControl):
    bl_label = "Sin"
    bl_description = "sin(x)"
    bl_icon = "DRIVER_TRANSFORM"

    def __init__(self):
        super().__init__(MathOp.SIN)
    
    def init(self, context):
        self.init_sockets(self.bl_label, ["x"])

    def execute(self, context):
        self.fetch_arguments()

        x = self.get_argument_value("x")
        result = math.sin(x)

        self.outputs[self.result.name].default_value = result
        self.result.value = result


def register():
    bpy.utils.register_class(NodeDofSin)
    subscribe_node(NodeDofSin)


def unregister():
    unsubscribe_node(NodeDofSin)
    bpy.utils.unregister_class(NodeDofSin)

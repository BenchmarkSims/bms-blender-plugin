import math

import bpy

from bms_blender_plugin.common.bml_structs import MathOp
from bms_blender_plugin.nodes_editor.dof_base_node import unsubscribe_node, subscribe_node
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.base_render_control import BaseRenderControl


class NodeDofMod(BaseRenderControl):
    bl_label = "Mod"
    bl_description = "a mod b"
    bl_icon = "DRIVER_TRANSFORM"

    def __init__(self):
        super().__init__(MathOp.MODULUS)
    
    def init(self, context):
        self.init_sockets(self.bl_label, ["a", "b"])

    def execute(self, context):
        self.fetch_arguments()

        a = self.get_argument_value("a")
        b = self.get_argument_value("b")

        if b == 0:
            self.set_argument_error(self.result, "b must not be 0")
            self.bl_icon = "ERROR"
            return

        result = math.fmod(a, b)
        self.result.value = result
        self.outputs[self.result.name].default_value = result


def register():
    bpy.utils.register_class(NodeDofMod)
    subscribe_node(NodeDofMod)


def unregister():
    unsubscribe_node(NodeDofMod)
    bpy.utils.unregister_class(NodeDofMod)

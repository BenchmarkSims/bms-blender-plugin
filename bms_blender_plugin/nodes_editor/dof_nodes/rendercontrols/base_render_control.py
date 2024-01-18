import bpy
from bpy.props import IntProperty

from bms_blender_plugin.common.bml_structs import (
    ArgType,
    MathOp,
    ControlType,
)
from bms_blender_plugin.common.blender_types import BlenderEditorNodeType
from bms_blender_plugin.nodes_editor.dof_base_node import DofBaseNode
from bms_blender_plugin.nodes_editor.dof_nodes.scratchpad import Scratchpad
from bms_blender_plugin.nodes_editor.util import (
    get_bml_node_type,
    get_socket_distinct_outgoing_dof_numbers,
)


class BaseRenderControl(DofBaseNode):
    """Base class for all RenderControlNodes. Sets up multiple input and a single output socket."""
    bl_label = "BaseRenderControl"

    node_name: str

    def __init__(self, math_op):
        super().__init__()
        self.bml_node_type = str(BlenderEditorNodeType.RENDER_CONTROL)
        self.math_op = math_op

    def init_sockets(self, node_name, argument_names):
        socket_output = self.outputs.new("NodeSocketFloat", "Result")
        socket_output.show_expanded = True
        self.result.name = "Result"
        self.node_name = node_name

        for argument_name in argument_names:
            argument = self.arguments.add()
            argument.name = argument_name
            socket_input = self.inputs.new("NodeSocketFloat", argument_name)
            socket_input.show_expanded = True

    def draw_buttons(self, context, layout):
        row = layout.row()

        if self.result.has_error:
            row.label(text=self.result.error_text, icon="ERROR")
        else:
            row.label(text=f"{self.bl_description} = {round(self.result.value, 3)}")

        for argument in self.arguments:
            row = layout.row()
            if argument.has_error:
                row.label(text=argument.error_text, icon="ERROR")
            else:
                row.label(text=f"{argument.name}: {round(argument.value, 3)}")

    def get_argument_value(self, argument_name):
        """Returns the current value of an argument by its name."""
        for argument in self.arguments:
            if argument_name == argument.name:
                return argument.value

        raise Exception(f"Argument {argument_name} not found in {self.name}")

    @staticmethod
    def set_result_type(node, argument_type: ArgType, argument_id=-1):
        """Sets the type of the output socket (either a scratch variable or a DOF ID)"""
        node.result.has_error = False
        node.result.error_text = ""

        if argument_type == ArgType.SCRATCH_VARIABLE_ID:
            node.result.type.argument_type = argument_type
            if argument_id == -1:
                node.result.type.argument_id = Scratchpad.alloc()
            else:
                node.result.type.argument_id = argument_id

        elif argument_type != ArgType.SCRATCH_VARIABLE_ID:
            node.result.type.argument_type = argument_type
            node.result.type.argument_id = argument_id

    @staticmethod
    def set_argument_error(argument, error_text):
        argument.has_error = True
        argument.error_text = error_text

    @staticmethod
    def clear_argument_error(argument):
        argument.has_error = False
        argument.error_text = ""

    def fetch_arguments(self):
        """Fetches the data of all input sockets for the node and copies them to the internal data structures."""
        for argument in self.arguments:
            if self.inputs[argument.name].is_linked:
                argument.value = (
                    self.inputs[argument.name].links[0].from_socket.default_value
                )
            else:
                argument.value = self.inputs[argument.name].default_value

    @staticmethod
    def check_connections(node):
        """Checks that an RC control has valid connections. Determines if the control can use a DOF id or has to use a
        scratch variable for each input/output socket."""
        # for incoming connections: always use the argument types of the respective outgoing sockets
        for argument in node.arguments:
            argument.has_error = False
            argument.error_text = ""
            if (
                argument.name in node.inputs.keys()
                and node.inputs[argument.name].is_linked
            ):
                # socket is connected - use the argument_type and argument_id of the other socket
                sending_socket = node.inputs[argument.name].links[0].from_socket

                # error: linked DOF node without parent DOF
                if (
                    get_bml_node_type(sending_socket.node)
                    == BlenderEditorNodeType.DOF_MODEL
                    and not sending_socket.node.parent_dof
                ):
                    BaseRenderControl.set_argument_error(
                        argument, "DOF is not linked to object"
                    )

                else:
                    argument.type.argument_type = sending_socket.node.result.type.argument_type
                    argument.type.argument_id = sending_socket.node.result.type.argument_id

            else:
                # socket is unconnected
                argument.type.argument_type = ArgType.FLOAT
                argument.type.argument_id = 0

        # outgoing connection:
        output_socket = node.outputs[node.result.name]
        if output_socket.is_linked:
            (
                connected_dof_numbers,
                has_unset_dofs,
            ) = get_socket_distinct_outgoing_dof_numbers(output_socket)
            if len(connected_dof_numbers) == 1:
                # connected to a single DOF, we can use its DOF id
                dof_number = connected_dof_numbers[0]
                BaseRenderControl.set_result_type(node, ArgType.DOF_ID, dof_number)
            else:
                # either multiple DOFs or >= 1 RC or mixed - we have to use a scratch variable
                BaseRenderControl.set_result_type(node, ArgType.SCRATCH_VARIABLE_ID)

            if has_unset_dofs:
                BaseRenderControl.set_argument_error(
                    node.result, "At least one DOF is not linked to object"
                )

        else:
            # the result is not linked
            BaseRenderControl.set_result_type(node, ArgType.FLOAT)


def register():
    bpy.utils.register_class(BaseRenderControl)


def unregister():
    bpy.utils.unregister_class(BaseRenderControl)


bpy.types.Node.control_type = IntProperty(default=ControlType.DOF_MATH)
bpy.types.Node.math_op = IntProperty(default=MathOp.SET)

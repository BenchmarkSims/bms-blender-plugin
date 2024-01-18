import bpy
from bpy.props import FloatProperty, PointerProperty

from bms_blender_plugin.common.blender_types import BlenderEditorNodeType
from bms_blender_plugin.common.bml_structs import DofType, ArgType
from bms_blender_plugin.common.util import get_dofs
from bms_blender_plugin.nodes_editor.dof_base_node import (
    DofBaseNode,
    subscribe_node,
    unsubscribe_node,
)
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.base_render_control import (
    BaseRenderControl,
)
from bms_blender_plugin.nodes_editor.util import (
    get_outgoing_nodes,
    dof_nodes_have_equal_dof_numbers,
)
from bms_blender_plugin.ui_tools.operators.dof_operators import ResetSingleDof


def refresh_dof_label(obj, context):
    if obj.parent_dof is None:
        label = "DOF"
    else:
        label = obj.parent_dof.name
    obj.label = label
    obj.name = label


class NodeDofModelInput(DofBaseNode):
    """Represents a tree node which is linked to a DOF in the model."""

    bl_label = "DOF"
    bl_icon = "EMPTY_DATA"

    parent_dof: PointerProperty(
        name="DOF", type=bpy.types.Object, update=refresh_dof_label
    )
    output: FloatProperty(name="output", default=0)

    def init(self, context):
        argument_names = {"DOF Input"}
        self.bml_node_type = str(BlenderEditorNodeType.DOF_MODEL)
        self.width = 300

        for argument_name in argument_names:
            argument = self.arguments.add()
            argument.name = argument_name
            self.inputs.new("NodeSocketVirtual", argument_name)

        self.result.name = "Result"
        socket_output = self.outputs.new("NodeSocketFloat", "Result")
        socket_output.show_expanded = True

    def draw_buttons(self, context, layout):
        layout.prop(self, "parent_dof")

        # DOF Input
        if (
            self.inputs["DOF Input"].is_linked
            and len(self.inputs["DOF Input"].links) > 0
        ):
            dof_input = self.inputs["DOF Input"].links[0].from_socket.default_value
            layout.label(text=f"DOF Input: {round(dof_input, 3)}")

        elif self.parent_dof:
            row = layout.row()
            row.column().prop(self.parent_dof, "dof_input")
            reset_operator = row.column().operator(
                ResetSingleDof.bl_idname, icon="LOOP_BACK", text=""
            )
            reset_operator.dof_to_reset_name = self.parent_dof.name

        # DOF properties
        if self.parent_dof:
            if self.parent_dof.dof_type == DofType.ROTATE.name:
                layout.prop(self.parent_dof, "dof_min")
                if self.parent_dof.dof_multiply_min_max:
                    layout.label(
                        text=f"Multiplied minimum: {round(self.parent_dof.dof_min * self.parent_dof.dof_multiplier,2)}°"
                    )
                layout.prop(self.parent_dof, "dof_max")
                if self.parent_dof.dof_multiply_min_max:
                    layout.label(
                        text=f"Multiplied maximum: {round(self.parent_dof.dof_max * self.parent_dof.dof_multiplier,2)}°"
                    )

            elif (
                self.parent_dof.dof_type == DofType.SCALE.name
                or self.parent_dof.dof_type == DofType.TRANSLATE.name
            ):
                layout.prop(self.parent_dof, "dof_x")
                layout.prop(self.parent_dof, "dof_y")
                layout.prop(self.parent_dof, "dof_z")

                layout.prop(self.parent_dof, "dof_min_input")
                if self.parent_dof.dof_multiply_min_max:
                    layout.label(
                        text=f"Multiplied minimum: "
                        f"{round(self.parent_dof.dof_min_input * self.parent_dof.dof_multiplier, 2)}"
                    )
                layout.prop(self.parent_dof, "dof_max_input")
                if self.parent_dof.dof_multiply_min_max:
                    layout.label(
                        text=f"Multiplied maximum: "
                        f"{round(self.parent_dof.dof_max_input * self.parent_dof.dof_multiplier, 2)}"
                    )

            layout.prop(self.parent_dof, "dof_check_limits")
            layout.prop(self.parent_dof, "dof_reverse")
            layout.prop(self.parent_dof, "dof_normalise")
            layout.prop(self.parent_dof, "dof_multiplier")
            layout.prop(self.parent_dof, "dof_multiply_min_max")

    def execute(self, context):
        """Executes a DOF node by updating the dof_input value of the respective DOF object in the scene."""
        # if the node is linked, take the input from the receiving end
        if self.inputs["DOF Input"].is_linked:
            dof_input = self.inputs["DOF Input"].links[0].from_socket.default_value

            # and apply it to the DOF
            if self.parent_dof:
                self.parent_dof.dof_input = dof_input

        # if the node is not linked, pass the parent DOF dof_input through to the output
        elif self.parent_dof:
            dof_input = self.parent_dof.dof_input

        # fallback
        else:
            dof_input = 0

        self.outputs["Result"].default_value = dof_input

    @staticmethod
    def check_connections(node_tree, node):
        """Checks the input and the output sockets and sets their value types to either a scratch variable or a DOF id.
        This method has to be static to work in Blender headless mode.
        """

        # Input
        for argument in node.arguments:
            argument.has_error = False
            argument.error_text = ""

            if (
                argument.name in node.inputs.keys()
                and node.inputs[argument.name].is_linked
            ):
                first_sending_socket = node.inputs[argument.name].links[0].from_socket

                # a dof can not be connected to other dofs with identical dof numbers
                for link in node.inputs[argument.name].links:
                    sending_node = link.from_socket.node
                    if dof_nodes_have_equal_dof_numbers(node, sending_node):
                        node_tree.links.remove(link)

                # multiple links:
                if len(node.inputs[argument.name].links) > 1:
                    # only multiple links from DOF Nodes are allowed when they have the same DOF number
                    for link in node.inputs[argument.name].links[1:]:
                        sending_node = link.from_socket.node

                        if not dof_nodes_have_equal_dof_numbers(first_sending_socket.node, sending_node):
                            node_tree.links.remove(link)

                argument.type.argument_type = (
                    first_sending_socket.node.result.type.argument_type
                )
                argument.type.argument_id = (
                    first_sending_socket.node.result.type.argument_id
                )

        # Output
        output_socket = node.outputs["Result"]
        if output_socket.is_linked:
            # if the node is connected to multiple nodes
            if len(get_outgoing_nodes(node)) > 1:
                BaseRenderControl.set_result_type(node, ArgType.SCRATCH_VARIABLE_ID)
            elif node.parent_dof:
                # linked to a render control or another DOF - set our result type to the DOF of the current node
                BaseRenderControl.set_result_type(
                    node,
                    ArgType.DOF_ID,
                    get_dofs()[node.parent_dof.dof_list_index].dof_number,
                )


def register():
    bpy.utils.register_class(NodeDofModelInput)
    subscribe_node(NodeDofModelInput)


def unregister():
    unsubscribe_node(NodeDofModelInput)
    bpy.utils.unregister_class(NodeDofModelInput)


bpy.types.Node.parent_dof = bpy.props.PointerProperty(
    name="DOF", type=bpy.types.Object, update=refresh_dof_label
)

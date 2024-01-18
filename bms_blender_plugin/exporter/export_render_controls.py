from collections import OrderedDict
from itertools import chain

import bpy

from bms_blender_plugin.common.bml_structs import (
    RenderControlNode,
    RenderControlMath,
    ArgType,
    MathOp,
)
from bms_blender_plugin.common.blender_types import BlenderEditorNodeType, BlenderNodeTreeType
from bms_blender_plugin.common.util import get_dofs
from bms_blender_plugin.nodes_editor.dof_editor import (
    update_node_links,
)
from bms_blender_plugin.nodes_editor.util import (
    get_bml_node_type,
    get_trees_in_order,
    get_outgoing_nodes, get_bml_node_tree_type,
)


def get_render_controls():
    """Locates the first NodeDofTree in the scene and exports all Render Controls and DOFs as a
    list of ordered subtrees"""
    dof_node_trees = 0
    for node_tree in bpy.data.node_groups.values():
        if get_bml_node_tree_type(node_tree) == BlenderNodeTreeType.DOF_TREE:
            dof_node_trees += 1
            if dof_node_trees > 1:
                raise Exception("More than one Dof Node Tree found, aborting")

            # make sure that the links of the tree are correct
            update_node_links(node_tree)

            trees = get_trees_in_order(node_tree)

            # flatten the list
            trees = list(chain.from_iterable(trees))

            # remove duplicates (preserve order!)
            trees = list(OrderedDict.fromkeys(trees))

            return trees

    # no RCs found: empty list
    return []


def get_render_control_nodes(node_start_index=0):
    """Parses an ordered list of Render Controls into the BMLv2 format.
    Additionally creates "SET" RCs for DOF->DOF or VAR -> DOF connections"""
    bml_nodes = []

    render_control_nodes = get_render_controls()
    for render_control_node in render_control_nodes:
        arguments = []
        math_op = None
        print(f"parsing RC {render_control_node.name}")

        if get_bml_node_type(render_control_node) == BlenderEditorNodeType.DOF_MODEL:
            if render_control_node.inputs[0].is_linked:
                if (get_bml_node_type(render_control_node.inputs[0].links[0].from_socket.node) ==
                        BlenderEditorNodeType.DOF_MODEL):
                    # the DOF node receives its data from another DOF - create a "SET" RC for it
                    math_op = MathOp.SET
                    arguments.append(
                        (ArgType.DOF_ID, render_control_node.arguments[0].type.argument_id)
                    )
                    result_type = ArgType.DOF_ID
                    result_id = get_dofs()[
                        render_control_node.parent_dof.dof_list_index
                    ].dof_number
                elif render_control_node.arguments[0].type.argument_type == ArgType.SCRATCH_VARIABLE_ID:
                    # the DOF node receives its data from a scratch variable - create a "SET" RC for it
                    math_op = MathOp.SET
                    arguments.append(
                        (ArgType.SCRATCH_VARIABLE_ID, render_control_node.arguments[0].type.argument_id)
                    )
                    result_type = ArgType.DOF_ID
                    result_id = get_dofs()[
                        render_control_node.parent_dof.dof_list_index
                    ].dof_number

                elif render_control_node.arguments[0].type.argument_type == ArgType.DOF_ID:
                    # the DOF node receives its data directly from an RC with a target DOF - nothing to do
                    continue

            else:
                # the node does not receive any data from other DOFs or scratchpad values - skip
                continue

        elif (
                get_bml_node_type(render_control_node)
                == BlenderEditorNodeType.RENDER_CONTROL
        ):
            math_op = render_control_node.math_op
            for argument in render_control_node.arguments:
                if argument.type.argument_type == ArgType.FLOAT:
                    argument_id = argument.value
                else:
                    argument_id = argument.type.argument_id
                arguments.append((argument.type.argument_type, argument_id))

            result_type = render_control_node.result.type.argument_type
            if result_type == ArgType.FLOAT:
                if len(get_outgoing_nodes(render_control_node)) > 0:
                    result_id = render_control_node.result.value
                else:
                    result_id = 0
            else:
                result_id = render_control_node.result.type.argument_id

        rc_math = RenderControlMath(
            math_op=math_op,
            arguments=arguments,
            result_type=result_type,
            result_id=result_id,
        )

        rc = RenderControlNode(len(bml_nodes) + node_start_index)
        rc.rc_math = rc_math

        bml_nodes.append(rc)

    return bml_nodes

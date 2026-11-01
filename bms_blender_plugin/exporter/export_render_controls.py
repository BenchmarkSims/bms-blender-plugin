import heapq
from collections import OrderedDict
from itertools import chain

import bpy

from bms_blender_plugin.common.blender_types import BlenderEditorNodeType, BlenderNodeTreeType
from bms_blender_plugin.common.bml_structs import ArgType, MathOp, RenderControlMath, RenderControlNode
from bms_blender_plugin.common.resolve_ids import resolve_dof_number
from bms_blender_plugin.common.util import get_dofs
from bms_blender_plugin.nodes_editor.dof_editor import (
    update_node_links,
)
from bms_blender_plugin.nodes_editor.util import (
    get_bml_node_tree_type,
    get_bml_node_type,
    get_outgoing_nodes,
    get_trees_in_order,
)


class RenderControlExportError(Exception):
    pass


def get_render_controls():
    """Locates the first NodeDofTree in the scene and exports all Render Controls and DOFs as a
    list of ordered subtrees"""
    dof_node_trees = 0
    for node_tree in bpy.data.node_groups.values():
        if get_bml_node_tree_type(node_tree) == BlenderNodeTreeType.DOF_TREE:
            dof_node_trees += 1
            if dof_node_trees > 1:
                raise RenderControlExportError("More than one DOF Node Tree found, aborting")

            # make sure that the links of the tree are correct
            update_node_links(node_tree)

            trees = get_trees_in_order(node_tree)

            # flatten the list
            trees = list(chain.from_iterable(trees))

            # remove duplicates (preserve order!)
            trees = list(OrderedDict.fromkeys(trees))

            return topologically_sort_render_control_nodes(trees)

    # no RCs found: empty list
    return []


def topologically_sort_render_control_nodes(render_control_nodes):
    """Sorts nodes so every dependency is emitted before any node that consumes it."""
    if len(render_control_nodes) < 2:
        return render_control_nodes

    node_positions = {node: index for index, node in enumerate(render_control_nodes)}
    incoming_edge_count = {node: 0 for node in render_control_nodes}
    outgoing_edges = {node: [] for node in render_control_nodes}
    node_set = set(render_control_nodes)

    for node in render_control_nodes:
        for output_socket in node.outputs:
            if not output_socket.is_linked:
                continue

            for link in output_socket.links:
                target_node = link.to_socket.node
                if target_node not in node_set:
                    continue

                outgoing_edges[node].append(target_node)
                incoming_edge_count[target_node] += 1

    ready_nodes = []
    for node, incoming_count in incoming_edge_count.items():
        if incoming_count == 0:
            heapq.heappush(ready_nodes, (node_positions[node], node))

    ordered_nodes = []
    while ready_nodes:
        _, node = heapq.heappop(ready_nodes)
        ordered_nodes.append(node)

        for target_node in outgoing_edges[node]:
            incoming_edge_count[target_node] -= 1
            if incoming_edge_count[target_node] == 0:
                heapq.heappush(ready_nodes, (node_positions[target_node], target_node))

    if len(ordered_nodes) != len(render_control_nodes):
        raise RenderControlExportError("Cycle detected in render control graph, aborting export")

    return ordered_nodes


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
                    try:
                        result_id = resolve_dof_number(render_control_node.parent_dof)
                    except Exception:
                        result_id = None
                    if result_id is None:
                        # legacy fallback to list index
                        try:
                            result_id = get_dofs()[render_control_node.parent_dof.dof_list_index].dof_number
                        except Exception:
                            result_id = 0
                elif render_control_node.arguments[0].type.argument_type == ArgType.SCRATCH_VARIABLE_ID:
                    # the DOF node receives its data from a scratch variable - create a "SET" RC for it
                    math_op = MathOp.SET
                    arguments.append(
                        (ArgType.SCRATCH_VARIABLE_ID, render_control_node.arguments[0].type.argument_id)
                    )
                    result_type = ArgType.DOF_ID
                    try:
                        result_id = resolve_dof_number(render_control_node.parent_dof)
                    except Exception:
                        result_id = None
                    if result_id is None:
                        try:
                            result_id = get_dofs()[render_control_node.parent_dof.dof_list_index].dof_number
                        except Exception:
                            result_id = 0

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

        elif get_bml_node_type(render_control_node) == BlenderEditorNodeType.SOLVER:
            # Solver nodes generate their own RC chains via generate_rc_nodes()
            solver_rc_nodes = render_control_node.generate_rc_nodes(len(bml_nodes) + node_start_index)
            bml_nodes.extend(solver_rc_nodes)
            continue

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

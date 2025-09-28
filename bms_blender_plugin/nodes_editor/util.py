from bms_blender_plugin.common.blender_types import BlenderEditorNodeType, BlenderNodeTreeType
from bms_blender_plugin.common.util import get_dofs
from bms_blender_plugin.common.resolve_ids import resolve_dof_number


def get_incoming_nodes(node):
    """Returns all nodes which are connected to the incoming sockets of a given node"""
    if node:
        incoming_nodes = []
        for socket_input in node.inputs:
            if socket_input.is_linked:
                for link in socket_input.links:
                    incoming_nodes.append(link.from_socket.node)
        return incoming_nodes


def cut_all_connections_between_nodes(from_node, to_node):
    """Removes all links between two nodes"""
    if not from_node or not to_node:
        return

    for socket_input in to_node:
        for link in socket_input.links:
            if link.from_socket.node == from_node:
                from_node.node_tree.links.remove(link)


def get_farthest_x_location(tree):
    """Given a node tree, return the biggest x location of its layout."""
    x_max = None
    for node in tree.nodes:
        if not x_max or node.location.x > x_max:
            x_max = node.location.x

    if not x_max:
        x_max = 0

    return x_max


def get_outgoing_nodes(node):
    """Returns all nodes which are connected to the outgoing sockets of a given node"""
    if node:
        outgoing_nodes = []

        for socket_output in node.outputs:
            if socket_output.is_linked:
                for link in socket_output.links:
                    outgoing_nodes.append(link.to_socket.node)
        return outgoing_nodes


def get_valid_dof_nodes(tree):
    """Returns a dict of all used DOF IDs and their respective DOF nodes"""

    list_dof_numbers = get_dofs()
    dofs = dict()

    for node in tree.nodes:
        if get_bml_node_type(node) == BlenderEditorNodeType.DOF_MODEL and node.parent_dof:
            # Resolve via persistent ID first; fall back to list index if valid
            dof_number = resolve_dof_number(node.parent_dof)
            if dof_number is None:
                idx = getattr(node.parent_dof, 'dof_list_index', -1)
                if 0 <= idx < len(list_dof_numbers):
                    dof_number = list_dof_numbers[idx].dof_number
            if dof_number is None:
                continue  # skip invalid/unresolved
            if dof_number not in dofs:
                dofs[dof_number] = [node]
            else:
                dofs[dof_number].append(node)

    return dofs


def get_bml_node_type(obj):
    """Returns the type of a custom Node"""
    if obj is None or "bml_node_type" not in obj.keys():
        return None
    else:
        bml_node_type = BlenderEditorNodeType(obj.bml_node_type)
        if bml_node_type is BlenderEditorNodeType.NONE:
            return None
        else:
            return bml_node_type


def get_root_nodes(node_tree):
    """Returns all nodes with no incoming connections of a tree"""
    root_nodes = []
    for node in node_tree.nodes:
        linked_inputs = 0
        for node_input in node.inputs:
            if node_input.is_linked:
                linked_inputs += 1
                break

        if linked_inputs == 0:
            root_nodes.append(node)

    return root_nodes


def get_trees_in_order(node_tree, filter_node_type=None):
    """Returns a list of subtrees in a parent tree. Each subtree starts with its root node(s)"""
    root_nodes = get_root_nodes(node_tree)
    trees = []
    for root_node in root_nodes:
        subtree = []

        def _parse_subtree(parent_node, tree):
            if filter_node_type:
                if get_bml_node_type(parent_node) == filter_node_type:
                    tree.append(parent_node)
            else:
                tree.append(parent_node)

            for node_output in parent_node.outputs:
                if node_output.is_linked:
                    for link in node_output.links:
                        _parse_subtree(link.to_socket.node, tree)

        _parse_subtree(root_node, subtree)

        trees.append(subtree)

    return trees


def get_socket_distinct_outgoing_dof_numbers(output_socket):
    """Returns a list of distinct DOF IDs which are connected to a given socket"""
    if output_socket:
        dof_numbers = []
        has_unset_dofs = False
        for link in output_socket.links:
            receiving_node = link.to_socket.node
            if get_bml_node_type(receiving_node) == BlenderEditorNodeType.DOF_MODEL:
                if receiving_node.parent_dof:
                    dof_number = resolve_dof_number(receiving_node.parent_dof)
                    if dof_number is None:
                        idx = getattr(receiving_node.parent_dof, 'dof_list_index', -1)
                        dofs_enum = get_dofs()
                        if 0 <= idx < len(dofs_enum):
                            dof_number = dofs_enum[idx].dof_number
                    if dof_number is None:
                        continue
                    if dof_number not in dof_numbers:
                        dof_numbers.append(dof_number)
                else:
                    has_unset_dofs = True

        return dof_numbers, has_unset_dofs

    return None


def find_material_node_by_material(tree, material):
    """Returns the first node of a tree which has the given material set"""
    # not very efficient but we are dealing with max. ~20 materials per model...
    nodes = tree.nodes.values()
    for node in nodes:
        if "material" in node.keys() and node.material == material:
            return node

    return None


def get_bml_node_tree_type(obj):
    """Returns the type of the custom NodeTrees"""
    if not obj:
        return BlenderNodeTreeType.NONE
    else:
        # the only way to get the tree type in Blender 3.6 is to check out the nodes
        if len(obj.nodes) > 0 and obj.nodes[0].bml_node_type in {
            BlenderEditorNodeType.DOF_MODEL,
            BlenderEditorNodeType.RENDER_CONTROL,
        }:
            return BlenderNodeTreeType.DOF_TREE

        elif len(obj.nodes) > 0 and obj.nodes[0].bml_node_type in {
            BlenderEditorNodeType.MATERIAL,
            BlenderEditorNodeType.SHADER_PARAMETER,
            BlenderEditorNodeType.SAMPLER,
        }:
            return BlenderNodeTreeType.MATERIAL_TREE
        else:
            return BlenderNodeTreeType.NONE


def dof_nodes_have_equal_dof_numbers(node_1, node_2):
    """Returns if 2 nodes have equal RESOLVED DOF numbers. Returns false if either node, parent DOF, or DOF number cannot be resolved."""
    if (get_bml_node_type(node_1) != BlenderEditorNodeType.DOF_MODEL or not node_1.parent_dof
            or get_bml_node_type(node_2) != BlenderEditorNodeType.DOF_MODEL or not node_2.parent_dof):
        return False

    # Fast path (same node or same DOF object)
    if node_1 == node_2 or node_1.parent_dof == node_2.parent_dof:
        return True

    # Compare resolved DOF numbers instead of list indices
    try:
        dof_number_1 = resolve_dof_number(node_1.parent_dof)
        dof_number_2 = resolve_dof_number(node_2.parent_dof)
        
        # Both must resolve to valid numbers to be considered equal
        if dof_number_1 is not None and dof_number_2 is not None:
            return dof_number_1 == dof_number_2
        else:
            return False
    except Exception:
        return False

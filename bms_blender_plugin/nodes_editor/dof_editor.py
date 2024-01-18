import bpy
import nodeitems_utils
from bpy.app.handlers import persistent
from bpy.types import NodeTree

from bms_blender_plugin.common.blender_types import (
    BlenderEditorNodeType,
    BlenderNodeTreeType,
)
from bms_blender_plugin.common.util import get_dofs
from bms_blender_plugin.nodes_editor import dof_node_categories
from bms_blender_plugin.nodes_editor.dof_base_node import DofBaseNode
from bms_blender_plugin.nodes_editor.dof_nodes.dof_input_node import NodeDofModelInput
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.base_render_control import (
    BaseRenderControl,
)
from bms_blender_plugin.nodes_editor.dof_nodes.scratchpad import Scratchpad
from bms_blender_plugin.nodes_editor.util import (
    get_valid_dof_nodes,
    get_outgoing_nodes,
    get_bml_node_type,
    get_root_nodes,
    get_trees_in_order,
    get_bml_node_tree_type,
)


class DofNodeTree(NodeTree):
    """Base class of a DOF Node Tree. Auto-executes all of its nodes while opened."""
    bl_label = "BMS DOF Node Tree"
    bl_icon = "EMPTY_DATA"

    previous_node_size = 0
    previous_link_size = 0

    is_updating = False
    is_headless = bpy.app.background

    cached_subtrees = None

    def execute(self, context):
        if not self.is_headless:
            # Update the nodes in their logical order by getting the ordered subtrees and then executing every node in
            # order. Since getting all subtrees of a tree is too expensive to do every time the tree is updated, we use
            # a very cheap caching logic of checking the amount of nodes and links on every update.

            if (
                not self.cached_subtrees
                or self.previous_node_size != len(self.nodes)
                or self.previous_link_size != len(self.links)
            ):
                self.cached_subtrees = get_trees_in_order(self)
                self.previous_node_size = len(self.nodes)
                self.previous_link_size = len(self.links)

            cache_needs_refreshing = False
            for subtree in self.cached_subtrees:
                for node in subtree:
                    if node and isinstance(node, DofBaseNode):
                        try:
                            node.execute(context)
                        except Exception as e:
                            print(f"Exception when executing Node Tree: {e}")
                            cache_needs_refreshing = True
                            continue
                    elif not node:
                        # we still refer to a node which has already been deleted - force a cache refresh
                        cache_needs_refreshing = True

            if cache_needs_refreshing:
                print("Refreshing cache")
                self.cached_subtrees = None


def execute_active_node_tree():
    """Executes the active node tree."""
    if not bpy.context.screen:
        return

    node_editor = next(
        (a for a in bpy.context.screen.areas if a.type == "NODE_EDITOR"), None
    )
    if node_editor is None:
        return
    for space in node_editor.spaces:
        if hasattr(space, "node_tree"):
            node_tree = getattr(space, "node_tree")
            if node_tree and isinstance(node_tree, DofNodeTree):
                node_tree.execute(bpy.context)
                break


def cleanup_deleted_dof_nodes(scene):
    """Cleans up all deleted nodes, checks their links and then executes the tree once to make sure its cache is
    up to-date."""
    # check all node trees
    for tree in bpy.data.node_groups.values():
        if (
            isinstance(tree, DofNodeTree)
            and get_bml_node_tree_type(tree) == BlenderNodeTreeType.DOF_TREE
            and not tree.is_updating
        ):
            tree.is_updating = True
            # for all DofNodeTrees, set all parent_dofs which contain references to delete objs to None
            for node in tree.nodes:
                if (
                    get_bml_node_type(node) == BlenderEditorNodeType.DOF_MODEL
                    and node.parent_dof
                    and (
                        node.parent_dof.name not in scene.objects
                        or len(node.parent_dof.users_collection) == 0
                    )
                ):
                    node.parent_dof = None

            update_node_links(tree)
            tree.is_updating = False

        execute_active_node_tree()


def update_node_links(node_tree):
    """Iterates all nodes of a Node tree. Creates connections to/from all nodes with DOFs of the same DOF id. Ensures
    that each node assigns their Scratchpad variable IDs."""
    if get_bml_node_tree_type(node_tree) != BlenderNodeTreeType.DOF_TREE:
        return

    dofs_dict = get_valid_dof_nodes(node_tree)
    list_dof_numbers = get_dofs()

    # previous_node_size will only be present when Blender is running
    if not hasattr(node_tree, "previous_node_size") or (
        len(node_tree.nodes) != node_tree.previous_node_size
        or len(node_tree.links) != node_tree.previous_link_size
    ):
        Scratchpad.clear()
        # determine all root nodes - nodes without any linked inputs
        root_nodes = get_root_nodes(node_tree)

        def _check_nodes_recursively(recursive_node):
            # make sure that node connects to all DOF nodes with the same id if it's connected to one
            outgoing_nodes = get_outgoing_nodes(recursive_node)
            for outgoing_node in outgoing_nodes:

                # make sure that nodes are not connected with themselves
                if outgoing_node == recursive_node:
                    continue
                if (
                    get_bml_node_type(outgoing_node) == BlenderEditorNodeType.DOF_MODEL
                    and outgoing_node.parent_dof
                    and get_bml_node_type(recursive_node) != BlenderEditorNodeType.DOF_MODEL
                ):
                    dof_number = list_dof_numbers[
                        outgoing_node.parent_dof.dof_list_index
                    ].dof_number
                    nodes_with_same_dof_number = dofs_dict[dof_number]
                    for node_with_same_dof_number in nodes_with_same_dof_number:
                        node_tree.links.new(
                            recursive_node.outputs[0],
                            node_with_same_dof_number.inputs[0],
                        )
                    dofs_dict[dof_number] = []

            if (
                get_bml_node_type(recursive_node)
                == BlenderEditorNodeType.RENDER_CONTROL
            ):
                BaseRenderControl.check_connections(recursive_node)

            elif get_bml_node_type(recursive_node) == BlenderEditorNodeType.DOF_MODEL:
                NodeDofModelInput.check_connections(node_tree, recursive_node)

            for output in recursive_node.outputs:
                for link in output.links:
                    _check_nodes_recursively(link.to_socket.node)

        # recursively update the node connection types for all nodes, starting with the root nodes
        for root_node in root_nodes:
            _check_nodes_recursively(root_node)

        node_tree.cached_subtrees = get_trees_in_order(node_tree)
        node_tree.previous_node_size = len(node_tree.nodes)
        node_tree.previous_link_size = len(node_tree.links)


def register_update_callback():
    """Callback method, triggered on every depsgraph update"""
    if cleanup_deleted_dof_nodes not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(cleanup_deleted_dof_nodes)

    if load_handler not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load_handler)


@persistent
def load_handler(dummy):
    register_update_callback()


def register():
    bpy.utils.register_class(DofNodeTree)
    nodeitems_utils.register_node_categories("DOFS", dof_node_categories)
    if load_handler not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load_handler)


def unregister():
    nodeitems_utils.unregister_node_categories("DOFS")
    bpy.utils.unregister_class(DofNodeTree)
    if cleanup_deleted_dof_nodes in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(cleanup_deleted_dof_nodes)

    if load_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_handler)


def is_dof_nodes_editor_visible():
    node_editor = next(
        (a for a in bpy.context.screen.areas if a.type == "NODE_EDITOR"), None
    )
    if node_editor is None:
        return False
    for space in node_editor.spaces:
        if hasattr(space, "node_tree"):
            node_tree = getattr(space, "node_tree")
            if node_tree:
                return True

    return False

def register():
    from bms_blender_plugin.nodes_editor.dof_nodes.solvers import (
        pointing_solver_node, oleo_solver_node, linkage_solver_node,
    )
    pointing_solver_node.register()
    oleo_solver_node.register()
    linkage_solver_node.register()


def unregister():
    from bms_blender_plugin.nodes_editor.dof_nodes.solvers import (
        pointing_solver_node, oleo_solver_node, linkage_solver_node,
    )
    linkage_solver_node.unregister()
    oleo_solver_node.unregister()
    pointing_solver_node.unregister()

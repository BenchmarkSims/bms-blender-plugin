import math

import bpy
from bpy.props import PointerProperty, FloatProperty, EnumProperty
from bpy.types import Operator

from bms_blender_plugin.common.blender_types import BlenderEditorNodeType
from bms_blender_plugin.common.bml_structs import MathOp, ArgType, RenderControlMath, RenderControlNode
from bms_blender_plugin.common.resolve_ids import resolve_dof_number
from bms_blender_plugin.nodes_editor.dof_base_node import DofBaseNode, subscribe_node, unsubscribe_node

_ELBOW_ITEMS = [
    ("UP", "Up", "Choose the IK solution where the elbow bends upward"),
    ("DOWN", "Down", "Choose the IK solution where the elbow bends downward"),
]


class InferLinkageLengths(Operator):
    """Infer L1 and L2 from the current scene DOF positions."""

    bl_idname = "bml.infer_linkage_lengths"
    bl_label = "Infer from scene"
    bl_description = "Set L1 and L2 from the current distances between the base DOF, hinge DOF, and target"
    bl_options = {"REGISTER", "UNDO"}

    node_name: bpy.props.StringProperty(name="Node name")

    def execute(self, context):
        for tree in bpy.data.node_groups.values():
            for node in tree.nodes:
                if node.name == self.node_name and isinstance(node, NodeLinkageSolver):
                    node.infer_lengths()
                    return {"FINISHED"}
        self.report({"WARNING"}, f"Linkage Solver node '{self.node_name}' not found.")
        return {"CANCELLED"}


def _solve_two_link_ik(base_loc, target_loc, l1, l2, elbow_up):
    """Solve 2-link IK (law of cosines). Returns (theta1, theta2) in radians or None on failure."""
    dx = target_loc.x - base_loc.x
    dy = target_loc.y - base_loc.y
    d = math.sqrt(dx * dx + dy * dy)

    if d < 1e-8:
        return None

    # Clamp to reachable range
    d_clamped = max(abs(l1 - l2) + 1e-8, min(d, l1 + l2 - 1e-8))

    cos_theta2 = (l1 * l1 + l2 * l2 - d_clamped * d_clamped) / (2.0 * l1 * l2)
    cos_theta2 = max(-1.0, min(1.0, cos_theta2))
    theta2 = math.acos(cos_theta2)

    cos_alpha = (l1 * l1 + d_clamped * d_clamped - l2 * l2) / (2.0 * l1 * d_clamped)
    cos_alpha = max(-1.0, min(1.0, cos_alpha))
    alpha = math.acos(cos_alpha)

    beta = math.atan2(dy, dx)

    if elbow_up:
        theta1 = beta - alpha
    else:
        theta1 = beta + alpha

    return theta1, theta2


class NodeLinkageSolver(DofBaseNode):
    """Solver node that drives a 2-link arm chain using inverse kinematics.

    base_dof:  the root rotation DOF — provides the world pivot position and the
               first-arm angle θ1.
    hinge_dof: the mid-joint rotation DOF — provides the second-arm angle θ2.
    target:    the desired world position of the free end (tip).
    l1:        length of arm 1 (base DOF to hinge DOF).
    l2:        length of arm 2 (hinge DOF to tip).
    elbow_mode: UP or DOWN — selects which of the two valid IK solutions to use.

    At export, both DOF angles are baked as constant SET render controls based
    on the current target position. A warning is printed for static targets.
    """

    bl_label = "Linkage Solver"
    bl_description = "2-link IK solver that drives a base and hinge rotation DOF toward a target"
    bl_icon = "ORIENTATION_GIMBAL"

    solver_base_dof: PointerProperty(name="Base DOF", type=bpy.types.Object)
    solver_hinge_dof: PointerProperty(name="Hinge DOF", type=bpy.types.Object)
    solver_target: PointerProperty(name="Target", type=bpy.types.Object)
    solver_l1: FloatProperty(name="L1 (arm 1 length)", default=1.0, min=0.0001)
    solver_l2: FloatProperty(name="L2 (arm 2 length)", default=1.0, min=0.0001)
    solver_elbow_mode: EnumProperty(name="Elbow Mode", items=_ELBOW_ITEMS, default="UP")

    def get_object_reference_attrs(self):
        """Returns the names of all PointerProperty attributes that hold scene object references."""
        return ("solver_base_dof", "solver_hinge_dof", "solver_target")

    def init(self, context):
        self.bml_node_type = str(BlenderEditorNodeType.SOLVER)
        self.width = 300

    def infer_lengths(self):
        """Sets L1 from base DOF to hinge DOF distance, L2 from hinge DOF to target distance."""
        if self.solver_base_dof and self.solver_hinge_dof:
            base_loc = self.solver_base_dof.matrix_world.to_translation()
            hinge_loc = self.solver_hinge_dof.matrix_world.to_translation()
            self.solver_l1 = (hinge_loc - base_loc).length

        if self.solver_hinge_dof and self.solver_target:
            hinge_loc = self.solver_hinge_dof.matrix_world.to_translation()
            target_loc = self.solver_target.matrix_world.to_translation()
            self.solver_l2 = (target_loc - hinge_loc).length

    def draw_buttons(self, context, layout):
        layout.prop(self, "solver_base_dof")
        layout.prop(self, "solver_hinge_dof")
        layout.prop(self, "solver_target")
        layout.prop(self, "solver_l1")
        layout.prop(self, "solver_l2")
        layout.prop(self, "solver_elbow_mode")

        op = layout.operator(InferLinkageLengths.bl_idname, text="Infer from scene", icon="EYEDROPPER")
        op.node_name = self.name

        if self.solver_base_dof and self.solver_target and self.solver_l1 > 0 and self.solver_l2 > 0:
            base_loc = self.solver_base_dof.matrix_world.to_translation()
            target_loc = self.solver_target.matrix_world.to_translation()
            result = _solve_two_link_ik(
                base_loc, target_loc, self.solver_l1, self.solver_l2, self.solver_elbow_mode == "UP"
            )
            if result:
                theta1_deg = math.degrees(result[0])
                theta2_deg = math.degrees(result[1])
                layout.label(text=f"θ1: {round(theta1_deg, 2)}°  θ2: {round(theta2_deg, 2)}°")
            else:
                layout.label(text="No IK solution (target too close)", icon="ERROR")

    def execute(self, context):
        if not self.solver_base_dof or not self.solver_target:
            return
        if self.solver_l1 <= 0 or self.solver_l2 <= 0:
            return

        base_loc = self.solver_base_dof.matrix_world.to_translation()
        target_loc = self.solver_target.matrix_world.to_translation()

        result = _solve_two_link_ik(
            base_loc, target_loc, self.solver_l1, self.solver_l2, self.solver_elbow_mode == "UP"
        )
        if result is None:
            return

        theta1, theta2 = result
        self.solver_base_dof.dof_input = theta1

        if self.solver_hinge_dof:
            self.solver_hinge_dof.dof_input = theta2

    def generate_rc_nodes(self, node_start_index):
        """Generate RC nodes for export. Bakes both DOF angles as constant SET nodes."""
        rc_nodes = []

        if not self.solver_base_dof or not self.solver_target:
            return rc_nodes
        if self.solver_l1 <= 0 or self.solver_l2 <= 0:
            return rc_nodes

        base_loc = self.solver_base_dof.matrix_world.to_translation()
        target_loc = self.solver_target.matrix_world.to_translation()

        result = _solve_two_link_ik(
            base_loc, target_loc, self.solver_l1, self.solver_l2, self.solver_elbow_mode == "UP"
        )
        if result is None:
            print(f"WARNING: Linkage Solver '{self.name}': no IK solution found — skipping export.")
            return rc_nodes

        theta1, theta2 = result

        print(
            f"WARNING: Linkage Solver '{self.name}': target '{self.solver_target.name}' is treated as static. "
            f"The exported RCs will only be correct for the current target position."
        )

        # Base DOF: θ1
        base_dof_number = resolve_dof_number(self.solver_base_dof)
        if base_dof_number is not None:
            rc_math = RenderControlMath(
                math_op=MathOp.SET,
                arguments=[(ArgType.FLOAT, float(theta1))],
                result_type=ArgType.DOF_ID,
                result_id=base_dof_number,
            )
            rc = RenderControlNode(node_start_index + len(rc_nodes))
            rc.rc_math = rc_math
            rc_nodes.append(rc)
        else:
            print(f"WARNING: Linkage Solver '{self.name}': base DOF has no resolved DOF number — skipping.")

        # Hinge DOF: θ2
        if self.solver_hinge_dof:
            hinge_dof_number = resolve_dof_number(self.solver_hinge_dof)
            if hinge_dof_number is not None:
                rc_math = RenderControlMath(
                    math_op=MathOp.SET,
                    arguments=[(ArgType.FLOAT, float(theta2))],
                    result_type=ArgType.DOF_ID,
                    result_id=hinge_dof_number,
                )
                rc = RenderControlNode(node_start_index + len(rc_nodes))
                rc.rc_math = rc_math
                rc_nodes.append(rc)
            else:
                print(f"WARNING: Linkage Solver '{self.name}': hinge DOF has no resolved DOF number — skipping.")

        return rc_nodes


def register():
    bpy.utils.register_class(InferLinkageLengths)
    bpy.utils.register_class(NodeLinkageSolver)
    subscribe_node(NodeLinkageSolver)


def unregister():
    unsubscribe_node(NodeLinkageSolver)
    bpy.utils.unregister_class(NodeLinkageSolver)
    bpy.utils.unregister_class(InferLinkageLengths)

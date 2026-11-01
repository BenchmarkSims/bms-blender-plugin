import math

import bpy
from bpy.props import PointerProperty, FloatProperty
from bpy.types import Operator

from bms_blender_plugin.common.blender_types import BlenderEditorNodeType
from bms_blender_plugin.common.bml_structs import MathOp, ArgType, RenderControlMath, RenderControlNode
from bms_blender_plugin.common.resolve_ids import resolve_dof_number
from bms_blender_plugin.nodes_editor.dof_base_node import DofBaseNode, subscribe_node, unsubscribe_node


class InferOleoLengths(Operator):
    """Infer oleo rest length and stroke length from the current scene DOF positions."""

    bl_idname = "bml.infer_oleo_lengths"
    bl_label = "Infer from scene"
    bl_description = "Set rest and stroke lengths from the current distance between the rotation DOF and the target"
    bl_options = {"REGISTER", "UNDO"}

    node_name: bpy.props.StringProperty(name="Node name")

    def execute(self, context):
        for tree in bpy.data.node_groups.values():
            for node in tree.nodes:
                if node.name == self.node_name and isinstance(node, NodeOleoSolver):
                    node.infer_lengths()
                    return {"FINISHED"}
        self.report({"WARNING"}, f"Oleo Solver node '{self.node_name}' not found.")
        return {"CANCELLED"}


class NodeOleoSolver(DofBaseNode):
    """Solver node that drives both a rotation DOF and a translation DOF to simulate an oleo strut.

    The rotation DOF is pointed toward the target (like the Pointing Solver) and the
    translation DOF is driven to match the compressed/extended length of the strut.

    rest_length: distance between the rotation DOF pivot and the target at the neutral position.
    stroke_length: total travel of the strut (used to normalise the translation DOF input).

    At export, both DOFs are baked as constant SET render controls based on the current
    target position. A warning is printed for static targets.
    """

    bl_label = "Oleo Solver"
    bl_description = "Drives a rotation DOF (pointing) and a translation DOF (extension) toward a target"
    bl_icon = "ORIENTATION_GIMBAL"

    solver_rot_dof: PointerProperty(name="Rotation DOF", type=bpy.types.Object)
    solver_trans_dof: PointerProperty(name="Translation DOF", type=bpy.types.Object)
    solver_target: PointerProperty(name="Target", type=bpy.types.Object)
    solver_rest_length: FloatProperty(name="Rest Length", default=1.0, min=0.0001)
    solver_stroke_length: FloatProperty(name="Stroke Length", default=1.0, min=0.0001)

    def get_object_reference_attrs(self):
        """Returns the names of all PointerProperty attributes that hold scene object references."""
        return ("solver_rot_dof", "solver_trans_dof", "solver_target")

    def init(self, context):
        self.bml_node_type = str(BlenderEditorNodeType.SOLVER)
        self.width = 300

    def infer_lengths(self):
        """Sets rest_length from the current distance between rotation DOF and target."""
        if self.solver_rot_dof and self.solver_target:
            dof_loc = self.solver_rot_dof.matrix_world.to_translation()
            target_loc = self.solver_target.matrix_world.to_translation()
            self.solver_rest_length = (target_loc - dof_loc).length
            # Default stroke is the same as rest length; user can adjust afterward
            if self.solver_stroke_length <= 0.0001:
                self.solver_stroke_length = self.solver_rest_length

    def draw_buttons(self, context, layout):
        layout.prop(self, "solver_rot_dof")
        layout.prop(self, "solver_trans_dof")
        layout.prop(self, "solver_target")
        layout.prop(self, "solver_rest_length")
        layout.prop(self, "solver_stroke_length")

        op = layout.operator(InferOleoLengths.bl_idname, text="Infer from scene", icon="EYEDROPPER")
        op.node_name = self.name

        if self.solver_rot_dof and self.solver_target:
            dof_loc = self.solver_rot_dof.matrix_world.to_translation()
            target_loc = self.solver_target.matrix_world.to_translation()
            dx = target_loc.x - dof_loc.x
            dy = target_loc.y - dof_loc.y
            angle_deg = math.degrees(math.atan2(dy, dx))
            dist = (target_loc - dof_loc).length
            extension = (
                (dist - self.solver_rest_length) / self.solver_stroke_length
                if self.solver_stroke_length > 0
                else 0.0
            )
            layout.label(text=f"Angle: {round(angle_deg, 2)}°  Extension: {round(extension, 3)}")

    def execute(self, context):
        if not self.solver_rot_dof or not self.solver_target:
            return

        dof_loc = self.solver_rot_dof.matrix_world.to_translation()
        target_loc = self.solver_target.matrix_world.to_translation()

        dx = target_loc.x - dof_loc.x
        dy = target_loc.y - dof_loc.y

        angle = math.atan2(dy, dx)
        self.solver_rot_dof.dof_input = angle

        if self.solver_trans_dof and self.solver_stroke_length > 0:
            dist = (target_loc - dof_loc).length
            extension = (dist - self.solver_rest_length) / self.solver_stroke_length
            self.solver_trans_dof.dof_input = extension

    def generate_rc_nodes(self, node_start_index):
        """Generate RC nodes for export. Bakes both DOFs as constant SET nodes."""
        rc_nodes = []

        if not self.solver_rot_dof or not self.solver_target:
            return rc_nodes

        dof_loc = self.solver_rot_dof.matrix_world.to_translation()
        target_loc = self.solver_target.matrix_world.to_translation()

        dx = target_loc.x - dof_loc.x
        dy = target_loc.y - dof_loc.y

        print(
            f"WARNING: Oleo Solver '{self.name}': target '{self.solver_target.name}' is treated as static. "
            f"The exported RCs will only be correct for the current target position."
        )

        # Rotation DOF: pointing angle
        rot_dof_number = resolve_dof_number(self.solver_rot_dof)
        if rot_dof_number is not None:
            angle = math.atan2(dy, dx)
            rc_math = RenderControlMath(
                math_op=MathOp.SET,
                arguments=[(ArgType.FLOAT, float(angle))],
                result_type=ArgType.DOF_ID,
                result_id=rot_dof_number,
            )
            rc = RenderControlNode(node_start_index + len(rc_nodes))
            rc.rc_math = rc_math
            rc_nodes.append(rc)
        else:
            print(f"WARNING: Oleo Solver '{self.name}': rotation DOF has no resolved DOF number — skipping.")

        # Translation DOF: extension
        if self.solver_trans_dof and self.solver_stroke_length > 0:
            trans_dof_number = resolve_dof_number(self.solver_trans_dof)
            if trans_dof_number is not None:
                dist = (target_loc - dof_loc).length
                extension = (dist - self.solver_rest_length) / self.solver_stroke_length
                rc_math = RenderControlMath(
                    math_op=MathOp.SET,
                    arguments=[(ArgType.FLOAT, float(extension))],
                    result_type=ArgType.DOF_ID,
                    result_id=trans_dof_number,
                )
                rc = RenderControlNode(node_start_index + len(rc_nodes))
                rc.rc_math = rc_math
                rc_nodes.append(rc)
            else:
                print(f"WARNING: Oleo Solver '{self.name}': translation DOF has no resolved DOF number — skipping.")

        return rc_nodes


def register():
    bpy.utils.register_class(InferOleoLengths)
    bpy.utils.register_class(NodeOleoSolver)
    subscribe_node(NodeOleoSolver)


def unregister():
    unsubscribe_node(NodeOleoSolver)
    bpy.utils.unregister_class(NodeOleoSolver)
    bpy.utils.unregister_class(InferOleoLengths)

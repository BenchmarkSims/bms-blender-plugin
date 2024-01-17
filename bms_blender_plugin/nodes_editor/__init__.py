from nodeitems_utils import NodeCategory, NodeItem

from bms_blender_plugin.nodes_editor.dof_nodes.dof_input_node import NodeDofModelInput
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.basic_math.add_node import NodeDofAdd
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.basic_math.divide_node import NodeDofDivide
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.basic_math.mod_node import NodeDofMod
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.basic_math.multiply_node import NodeDofMultiply
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.basic_math.subtract_node import NodeDofSubtract
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.misc.clamp_node import NodeDofClamp
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.misc.multiply_frame_time import NodeDofMultiplyFrameTime
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.misc.normalize_node import NodeDofNormalize
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.misc.set_node import NodeDofSet
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.misc.step_node import NodeDofStep
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.right_angled_triangle.angle_from_adj_hyp import \
    NodeDofAngleFromAdjHyp
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.right_angled_triangle.angle_from_opp_adj import \
    NodeDofAngleFromOppAdj
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.right_angled_triangle.angle_from_opp_hyp import \
    NodeDofAngleFromOpHyp
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.right_angled_triangle.length_of_adj_from_angle_opp import\
    NodeDofLengthOfAdjFromAngleOpp
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.right_angled_triangle.length_of_opp_from_angle_adj import\
    NodeDofLengthOfOppFromAngleAdj
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.triangle.angle_a_from_angle_b_side_a_side_b import \
    NodeDofAngleAFromAngleBSideASideB
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.triangle.angle_a_from_angle_b_side_a_side_c import \
    NodeDofAngleAFromAngleBSideASideC
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.triangle.angle_a_from_side_a_side_b_side_c import \
    NodeDofAngleAFromSideASideBSideC
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.triangle.side_a_from_angle_a_side_b_side_c import \
    NodeDofSideAFromAngleASideBSideC
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.trigonometry.arccos_node import NodeDofArcCos
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.trigonometry.arcsin_node import NodeDofArcSin
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.trigonometry.arctan2_node import NodeDofArcTan2
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.trigonometry.arctan_node import NodeDofArcTan
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.trigonometry.cos_node import NodeDofCos
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.trigonometry.sin_node import NodeDofSin
from bms_blender_plugin.nodes_editor.dof_nodes.rendercontrols.trigonometry.tan_node import NodeDofTan
from bms_blender_plugin.nodes_editor.material_nodes.material_node import MaterialNode
from bms_blender_plugin.nodes_editor.material_nodes.sampler_node import SamplerNode
from bms_blender_plugin.nodes_editor.material_nodes.shader_parameter_node import ShaderNode

"""Defines all categories for the "Add" Menu in the custom Node Trees"""
class CustomDofNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == "DofNodeTree"


dof_node_categories = [
    CustomDofNodeCategory(
        "DOF",
        "DOF",
        items=[
            NodeItem(NodeDofModelInput.__name__),
        ],
    ),
    CustomDofNodeCategory(
        "MATH",
        "Math",
        items=[
            NodeItem(NodeDofAdd.__name__),
            NodeItem(NodeDofSubtract.__name__),
            NodeItem(NodeDofMultiply.__name__),
            NodeItem(NodeDofDivide.__name__),
            NodeItem(NodeDofMod.__name__),
        ],
    ),
    CustomDofNodeCategory(
        "TRIG_BASIC",
        "Trigonometry (basic)",
        items=[
            NodeItem(NodeDofSin.__name__),
            NodeItem(NodeDofCos.__name__),
            NodeItem(NodeDofTan.__name__),
            NodeItem(NodeDofArcCos.__name__),
            NodeItem(NodeDofArcSin.__name__),
            NodeItem(NodeDofArcTan.__name__),
            NodeItem(NodeDofArcTan2.__name__),
        ],
    ),
    CustomDofNodeCategory(
        "RIGHT_TRIANGLE",
        "Right Triangle functions",
        items=[
            NodeItem(NodeDofAngleFromAdjHyp.__name__),
            NodeItem(NodeDofAngleFromOppAdj.__name__),
            NodeItem(NodeDofAngleFromOpHyp.__name__),
            NodeItem(NodeDofLengthOfAdjFromAngleOpp.__name__),
            NodeItem(NodeDofLengthOfOppFromAngleAdj.__name__),
        ],
    ),
    CustomDofNodeCategory(
        "TRIANGLE",
        "Triangle functions",
        items=[
            NodeItem(NodeDofAngleAFromAngleBSideASideC.__name__),
            NodeItem(NodeDofAngleAFromAngleBSideASideB.__name__),
            NodeItem(NodeDofAngleAFromSideASideBSideC.__name__),
            NodeItem(NodeDofSideAFromAngleASideBSideC.__name__),
        ],
    ),

    CustomDofNodeCategory(
        "MISC",
        "Misc functions",
        items=[
            NodeItem(NodeDofSet.__name__),
            NodeItem(NodeDofClamp.__name__),
            NodeItem(NodeDofNormalize.__name__),
            NodeItem(NodeDofStep.__name__),
            NodeItem(NodeDofMultiplyFrameTime.__name__),
        ],
    ),
]


class CustomMaterialNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == "MaterialNodeTree"


material_node_categories = [
    CustomMaterialNodeCategory(
        "MATERIAL",
        "Material",
        items=[
            NodeItem(MaterialNode.__name__),
            NodeItem(SamplerNode.__name__),
            NodeItem(ShaderNode.__name__),
        ],
    ),
]

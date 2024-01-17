from typing import Any

import blf
import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils
from bpy.types import (
    Gizmo,
    GizmoGroup,
)
import mathutils
from math import radians

from bms_blender_plugin.common.bml_structs import DofType
from bms_blender_plugin.common.blender_types import BlenderNodeType
from bms_blender_plugin.common.util import get_bml_type, get_parent_dof_or_switch
from bms_blender_plugin.ui_tools.dof_behaviour import is_dof_input_within_limits

scale_shape_indices = (
    (0, 1, 4),
    (0, 4, 3),
    (9, 10, 11),
    (16, 17, 1),
    (9, 11, 16),
    (2, 8, 9),
    (16, 1, 0),
    (0, 2, 9),
    (9, 16, 0),
    (2, 0, 3),
    (2, 3, 5),
    (7, 6, 5),
    (3, 4, 15),
    (7, 5, 3),
    (13, 12, 7),
    (3, 15, 14),
    (14, 13, 7),
    (7, 3, 14),
    (8, 2, 5),
    (8, 5, 6),
    (9, 8, 6),
    (9, 6, 7),
    (10, 9, 7),
    (10, 7, 12),
    (11, 10, 12),
    (11, 12, 13),
    (16, 11, 13),
    (16, 13, 14),
    (17, 16, 14),
    (17, 14, 15),
    (1, 17, 15),
    (1, 15, 4),
    (18, 19, 21),
    (18, 21, 20),
    (22, 23, 19),
    (22, 19, 18),
    (20, 24, 22),
    (20, 22, 18),
    (39, 40, 29),
    (39, 29, 34),
    (30, 42, 39),
    (30, 39, 34),
    (41, 31, 29),
    (41, 29, 40),
    (25, 26, 41),
    (25, 41, 42),
    (26, 28, 31),
    (26, 31, 41),
    (27, 25, 42),
    (27, 42, 30),
    (28, 27, 30),
    (28, 30, 31),
    (34, 33, 36),
    (34, 36, 30),
    (36, 35, 31),
    (36, 31, 30),
    (33, 34, 29),
    (33, 29, 32),
    (33, 32, 35),
    (33, 35, 36),
    (32, 29, 31),
    (32, 31, 35),
    (39, 42, 44),
    (39, 44, 38),
    (44, 42, 41),
    (44, 41, 43),
    (38, 37, 40),
    (38, 40, 39),
    (38, 44, 43),
    (38, 43, 37),
    (37, 43, 41),
    (37, 41, 40),
    (61, 62, 54),
    (61, 54, 49),
    (56, 51, 61),
    (56, 61, 49),
    (50, 55, 54),
    (50, 54, 62),
    (48, 46, 55),
    (48, 55, 50),
    (45, 47, 51),
    (45, 51, 56),
    (46, 45, 56),
    (46, 56, 55),
    (47, 48, 50),
    (47, 50, 51),
    (49, 53, 58),
    (49, 58, 56),
    (58, 57, 55),
    (58, 55, 56),
    (53, 49, 54),
    (53, 54, 52),
    (53, 52, 57),
    (53, 57, 58),
    (52, 54, 55),
    (52, 55, 57),
    (61, 51, 64),
    (61, 64, 60),
    (64, 51, 50),
    (64, 50, 63),
    (60, 59, 62),
    (60, 62, 61),
    (60, 64, 63),
    (60, 63, 59),
    (59, 63, 50),
    (59, 50, 62),
    (70, 80, 69),
    (70, 69, 71),
    (81, 72, 71),
    (81, 71, 69),
    (73, 82, 80),
    (73, 80, 70),
    (67, 68, 73),
    (67, 73, 72),
    (68, 66, 82),
    (68, 82, 73),
    (65, 67, 72),
    (65, 72, 81),
    (66, 65, 81),
    (66, 81, 82),
    (70, 75, 77),
    (70, 77, 73),
    (77, 76, 72),
    (77, 72, 73),
    (75, 70, 71),
    (75, 71, 74),
    (75, 74, 76),
    (75, 76, 77),
    (74, 71, 72),
    (74, 72, 76),
    (80, 82, 84),
    (80, 84, 79),
    (84, 82, 81),
    (84, 81, 83),
    (79, 78, 69),
    (79, 69, 80),
    (79, 84, 83),
    (79, 83, 78),
    (78, 83, 81),
    (78, 81, 69),
    (89, 88, 87),
    (85, 92, 91),
    (89, 87, 86),
    (85, 91, 90),
    (89, 86, 85),
    (89, 85, 90),
    (95, 93, 94),
    (95, 94, 96),
    (100, 99, 97),
    (97, 95, 96),
    (98, 100, 97),
    (97, 96, 98),
    (87, 88, 99),
    (87, 99, 100),
    (91, 92, 94),
    (91, 94, 93),
    (90, 91, 93),
    (90, 93, 95),
    (92, 85, 96),
    (92, 96, 94),
    (89, 90, 95),
    (89, 95, 97),
    (85, 86, 98),
    (85, 98, 96),
    (88, 89, 97),
    (88, 97, 99),
    (86, 87, 100),
    (86, 100, 98),
    (101, 102, 105),
    (101, 105, 104),
    (103, 109, 110),
    (111, 112, 117),
    (103, 110, 111),
    (102, 101, 103),
    (119, 120, 124),
    (124, 102, 103),
    (103, 111, 117),
    (118, 119, 124),
    (103, 117, 118),
    (103, 118, 124),
    (103, 101, 104),
    (103, 104, 106),
    (106, 104, 105),
    (123, 122, 121),
    (106, 105, 123),
    (108, 107, 106),
    (115, 114, 113),
    (113, 108, 106),
    (106, 123, 121),
    (116, 115, 113),
    (106, 121, 116),
    (106, 116, 113),
    (109, 103, 106),
    (109, 106, 107),
    (110, 109, 107),
    (110, 107, 108),
    (111, 110, 108),
    (111, 108, 113),
    (112, 111, 113),
    (112, 113, 114),
    (117, 112, 114),
    (117, 114, 115),
    (118, 117, 115),
    (118, 115, 116),
    (119, 118, 116),
    (119, 116, 121),
    (120, 119, 121),
    (120, 121, 122),
    (124, 120, 122),
    (124, 122, 123),
    (102, 124, 123),
    (102, 123, 105),
)


scale_shape_verts = (
    (-0.00035530468448996544, 1.205640196800232, -0.005995396990329027),
    (-0.07349913567304611, 1.2995680570602417, -0.005995396990329027),
    (0.07358794659376144, 1.2995680570602417, -0.005995396990329027),
    (-0.00035530468448996544, 1.205640196800232, 0.005995396990329027),
    (-0.07349913567304611, 1.2995680570602417, 0.005995396990329027),
    (0.07358794659376144, 1.2995680570602417, 0.005995396990329027),
    (0.12075175344944, 1.2995680570602417, 0.005995396990329027),
    (0.019629379734396935, 1.170866847038269, 0.005995396990329027),
    (0.12075175344944, 1.2995680570602417, -0.005995396990329027),
    (0.019629379734396935, 1.170866847038269, -0.005995396990329027),
    (0.019629379734396935, 1.026977300643921, -0.005995396990329027),
    (-0.019540566951036453, 1.026977300643921, -0.005995396990329027),
    (0.019629379734396935, 1.026977300643921, 0.005995396990329027),
    (-0.019540566951036453, 1.026977300643921, 0.005995396990329027),
    (-0.019540566951036453, 1.1712665557861328, 0.005995396990329027),
    (-0.12066293507814407, 1.2995680570602417, 0.005995396990329027),
    (-0.019540566951036453, 1.1712665557861328, -0.005995396990329027),
    (-0.12066293507814407, 1.2995680570602417, -0.005995396990329027),
    (-0.014999999664723873, -0.014999985694885254, -0.014999999664723873),
    (-0.014999999664723873, -0.014999985694885254, 0.014999999664723873),
    (-0.014999999664723873, 0.014999985694885254, -0.014999999664723873),
    (-0.014999999664723873, 0.014999985694885254, 0.014999999664723873),
    (0.014999999664723873, -0.014999985694885254, -0.014999999664723873),
    (0.014999999664723873, -0.014999985694885254, 0.014999999664723873),
    (0.014999999664723873, 0.014999985694885254, -0.014999999664723873),
    (-0.014999999664723873, 0.014999985694885254, -0.014999999664723873),
    (-0.014999999664723873, 0.014999985694885254, 0.014999999664723873),
    (0.014999999664723873, 0.014999985694885254, -0.014999999664723873),
    (0.014999999664723873, 0.014999985694885254, 0.014999999664723873),
    (0.014999999664723873, 1.0, 0.014999999664723873),
    (0.014999999664723873, 0.9400616884231567, -0.014999999664723873),
    (0.014999999664723873, 0.9400616884231567, 0.014999999664723873),
    (0.20107340812683105, 0.747423529624939, 0.014999999664723873),
    (0.20120537281036377, 0.7476334571838379, -0.014999999664723873),
    (0.014999955892562866, 1.0003854036331177, -0.014999999664723873),
    (0.1686938852071762, 0.7239394187927246, 0.014999999664723873),
    (0.16882586479187012, 0.7241493463516235, -0.014999999664723873),
    (-0.20107346773147583, 0.747423529624939, 0.014999999664723873),
    (-0.20120544731616974, 0.7476334571838379, -0.014999999664723873),
    (-0.01500004343688488, 1.0003854036331177, -0.014999999664723873),
    (-0.015000039711594582, 1.0001040697097778, 0.014999999664723873),
    (-0.015108074061572552, 0.9400616884231567, 0.014999999664723873),
    (-0.015108074061572552, 0.940278172492981, -0.014999999664723873),
    (-0.16869394481182098, 0.7239394187927246, 0.014999999664723873),
    (-0.1688259243965149, 0.7241493463516235, -0.014999999664723873),
    (0.014999999664723873, -0.014999985694885254, -0.014999999664723873),
    (0.014999999664723873, -0.014999985694885254, 0.014999999664723873),
    (0.014999999664723873, 0.014999985694885254, -0.014999999664723873),
    (0.014999999664723873, 0.014999985694885254, 0.014999999664723873),
    (1.0, -0.014999985694885254, -0.014999999664723873),
    (0.9400616884231567, 0.014999985694885254, 0.014999999664723873),
    (0.9400616884231567, 0.014999985694885254, -0.014999999664723873),
    (0.747423529624939, -0.20107340812683105, 0.014999999664723873),
    (0.7476334571838379, -0.20120537281036377, -0.014999999664723873),
    (1.0001040697097778, -0.014999985694885254, 0.014999999664723873),
    (0.9400616884231567, -0.015107989311218262, 0.014999999664723873),
    (0.940278172492981, -0.015107989311218262, -0.014999999664723873),
    (0.7239394187927246, -0.1686939001083374, 0.014999999664723873),
    (0.7241493463516235, -0.16882586479187012, -0.014999999664723873),
    (0.747423529624939, 0.20107340812683105, 0.014999999664723873),
    (0.7476334571838379, 0.20120543241500854, -0.014999999664723873),
    (1.0003854036331177, 0.014999985694885254, -0.014999999664723873),
    (1.0001040697097778, 0.014999985694885254, 0.014999999664723873),
    (0.7239394187927246, 0.1686939001083374, 0.014999999664723873),
    (0.7241493463516235, 0.16882586479187012, -0.014999999664723873),
    (-0.014999999664723873, -0.014999985694885254, 0.014999999664723873),
    (-0.014999999664723873, 0.014999985694885254, 0.014999999664723873),
    (0.014999999664723873, -0.014999985694885254, 0.014999999664723873),
    (0.014999999664723873, 0.014999985694885254, 0.014999999664723873),
    (-0.014999999664723873, -0.014999985694885254, 1.0),
    (0.014999999664723873, 0.014999985694885254, 1.0),
    (0.014999999664723873, -0.014999985694885254, 1.0),
    (0.014999999664723873, -0.014999985694885254, 0.940278172492981),
    (0.014999999664723873, 0.014999985694885254, 0.940278172492981),
    (0.20107349753379822, -0.014999985694885254, 0.747423529624939),
    (0.20120546221733093, 0.014999985694885254, 0.7476334571838379),
    (0.16869397461414337, -0.014999985694885254, 0.7239394187927246),
    (0.16882595419883728, 0.014999985694885254, 0.7241493463516235),
    (-0.20107337832450867, -0.014999985694885254, 0.747423529624939),
    (-0.20120535790920258, 0.014999985694885254, 0.7476334571838379),
    (-0.014999925158917904, 0.014999985694885254, 1.0003854036331177),
    (-0.015107961371541023, -0.014999985694885254, 0.9400616884231567),
    (-0.015107963234186172, 0.014999985694885254, 0.940278172492981),
    (-0.16869385540485382, -0.014999985694885254, 0.7239394187927246),
    (-0.16882583498954773, 0.014999985694885254, 0.7241493463516235),
    (0.04786316677927971, 0.10112237930297852, 1.1940046548843384),
    (-0.12560361623764038, -0.13629531860351562, 1.1940046548843384),
    (0.12020762264728546, -0.13629531860351562, 1.1940046548843384),
    (0.12020762264728546, -0.10112237930297852, 1.1940046548843384),
    (-0.05325920507311821, -0.10112237930297852, 1.1940046548843384),
    (0.12020762264728546, 0.13629531860351562, 1.1940046548843384),
    (-0.11481191962957382, 0.13629531860351562, 1.1940046548843384),
    (-0.11481191962957382, 0.10112237930297852, 1.1940046548843384),
    (-0.11481191962957382, 0.13629531860351562, 1.2059954404830933),
    (-0.11481191962957382, 0.10112237930297852, 1.2059954404830933),
    (0.12020762264728546, 0.13629531860351562, 1.2059954404830933),
    (0.04786316677927971, 0.10112237930297852, 1.2059954404830933),
    (-0.05325920507311821, -0.10112237930297852, 1.2059954404830933),
    (-0.12560361623764038, -0.13629531860351562, 1.2059954404830933),
    (0.12020762264728546, -0.10112237930297852, 1.2059954404830933),
    (0.12020762264728546, -0.13629531860351562, 1.2059954404830933),
    (1.3326648473739624, 0.13476324081420898, -0.005995396990329027),
    (1.2855011224746704, 0.13476324081420898, -0.005995396990329027),
    (1.223948359489441, 0.003264188766479492, -0.005995396990329027),
    (1.3326648473739624, 0.13476324081420898, 0.005995396990329027),
    (1.2855011224746704, 0.13476324081420898, 0.005995396990329027),
    (1.223948359489441, 0.003264188766479492, 0.005995396990329027),
    (1.340259075164795, -0.13782751560211182, 0.005995396990329027),
    (1.2930952310562134, -0.13782751560211182, 0.005995396990329027),
    (1.340259075164795, -0.13782751560211182, -0.005995396990329027),
    (1.2930952310562134, -0.13782751560211182, -0.005995396990329027),
    (1.200366497039795, -0.025114059448242188, -0.005995396990329027),
    (1.1064385175704956, -0.13782751560211182, -0.005995396990329027),
    (1.200366497039795, -0.025114059448242188, 0.005995396990329027),
    (1.1064385175704956, -0.13782751560211182, 0.005995396990329027),
    (1.0588750839233398, -0.13782751560211182, 0.005995396990329027),
    (1.1763848066329956, 0.003264188766479492, 0.005995396990329027),
    (1.0588750839233398, -0.13782751560211182, -0.005995396990329027),
    (1.1763848066329956, 0.003264188766479492, -0.005995396990329027),
    (1.0672686100006104, 0.13476324081420898, -0.005995396990329027),
    (1.1148321628570557, 0.13476324081420898, -0.005995396990329027),
    (1.0672686100006104, 0.13476324081420898, 0.005995396990329027),
    (1.1148321628570557, 0.13476324081420898, 0.005995396990329027),
    (1.200366497039795, 0.030843019485473633, 0.005995396990329027),
    (1.200366497039795, 0.030843019485473633, -0.005995396990329027),
)


class DOFScaleGizmo(Gizmo):
    bl_idname = "VIEW3D_GT_bml_dof_scale_gizmo"
    bl_target_properties = ({"id": "dof_value", "type": "FLOAT", "array_length": 1},)
    custom_shape: tuple[Any, Any]
    init_value: float
    init_mouse_x: float
    __slots__ = (
        "custom_shape",
        "init_mouse_x",
        "init_value",
    )

    def draw(self, context):
        self.draw_custom_shape(self.custom_shape)

    def draw_select(self, context, select_id):
        self.draw_custom_shape(self.custom_shape, select_id=select_id)

    def invoke(self, context, event):
        self.init_mouse_x = event.mouse_x
        self.init_value = self.target_get_value("dof_value")
        bpy.ops.ed.undo_push(message=f"Scale DOF {round(self.init_value, 2)}")
        return {"RUNNING_MODAL"}

    def exit(self, context, cancel):
        context.area.header_text_set(None)
        if cancel:
            self.target_set_value("dof_value", self.init_value)

    def modal(self, context, event, tweak):
        delta = (self.init_mouse_x - event.mouse_x) / 50.0
        if "SNAP" in tweak:
            delta = round(delta)
        if "PRECISE" in tweak:
            delta /= 100.0
        value = self.init_value - delta
        self.target_set_value("dof_value", value)
        context.area.header_text_set(f"DOF Scale {round(value, 2)}")
        return {"RUNNING_MODAL"}

    def setup(self):
        if not hasattr(self, "custom_shape"):
            shader = gpu.shader.from_builtin("3D_UNIFORM_COLOR")
            batch = batch_for_shader(
                shader, "TRIS", {"pos": scale_shape_verts}, indices=scale_shape_indices
            )
            shader.uniform_float("color", (1, 0, 0, 1))
            batch.program_set(shader)
            self.custom_shape = (batch, shader)


class DOFScaleGizmoGroup(GizmoGroup):
    bl_idname = "OBJECT_GGT_dof_scale"
    bl_label = "DOF Scale Gizmo Group"
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_options = {"3D", "PERSISTENT", "SHOW_MODAL_ALL"}

    draw_text_handler = None
    prev_obj = None

    def __init__(self):
        self.scale_gizmo = None

    @classmethod
    def draw_callback_px(cls, context, obj):
        if obj:
            font_id = 0
            if is_dof_input_within_limits(obj, context):
                blf.color(0, 0, 1, 0, 0.6)
            else:
                blf.color(0, 1, 0, 0, 0.6)
            location_window = view3d_utils.location_3d_to_region_2d(
                context.region,
                context.space_data.region_3d,
                obj.matrix_world.translation,
            )
            if location_window:
                location_window.x += 10
                location_window.y += 10
                blf.position(font_id, location_window.x, location_window.y, 0)

                blf.size(font_id, 15)

                sign = 1
                if obj.dof_reverse:
                    sign = -1
                dof_input = obj.dof_input * obj.dof_multiplier * sign

                blf.draw(
                    font_id,
                    f"{round(dof_input, 2)} / {round(context.object.dimensions.x, 2)}, "
                    f"{round(context.object.dimensions.y, 2)}, "
                    f"{round(context.object.dimensions.z, 2)}",
                )

    @classmethod
    def poll(cls, context):
        obj = get_parent_dof_or_switch(context.active_object)

        if (
            get_bml_type(obj) == BlenderNodeType.DOF
            and obj.dof_type == DofType.SCALE.name
        ):
            # DOF object has changed and text is still drawing - remove the text
            if obj != cls.prev_obj and cls.draw_text_handler:
                bpy.types.SpaceView3D.draw_handler_remove(
                    cls.draw_text_handler, "WINDOW"
                )
                cls.draw_text_handler = None

            # no text showing - draw the text
            if not cls.draw_text_handler:
                cls.draw_text_handler = bpy.types.SpaceView3D.draw_handler_add(
                    DOFScaleGizmoGroup.draw_callback_px,
                    (context, obj),
                    "WINDOW",
                    "POST_PIXEL",
                )
            cls.prev_obj = obj
            return True
        else:
            # no DOF selected, remove the text
            if cls.draw_text_handler:
                bpy.types.SpaceView3D.draw_handler_remove(
                    cls.draw_text_handler, "WINDOW"
                )
                cls.draw_text_handler = None
                cls.prev_obj = None
                return False

    def setup(self, context):
        obj = get_parent_dof_or_switch(context.object)
        gz = self.gizmos.new(DOFScaleGizmo.bl_idname)
        gz.target_set_prop("dof_value", obj, "dof_input")

        mat_rot = mathutils.Matrix.Rotation(radians(90.0), 4, "X")
        gz.matrix_basis = obj.matrix_world.normalized() @ mat_rot
        gz.line_width = 3

        gz.color = 0.0, 1.0, 0.0
        gz.alpha = 0.4

        self.scale_gizmo = gz

    def refresh(self, context):
        dof = get_parent_dof_or_switch(context.active_object)

        if dof:
            gz = self.scale_gizmo
            gz.target_set_prop("dof_value", dof, "dof_input")

            mat_rot = mathutils.Matrix.Rotation(0, 4, "X")
            mat_rot.translation = dof.matrix_world.translation
            gz.matrix_basis = mat_rot

            if is_dof_input_within_limits(dof, context):
                gz.color = 0.0, 1.0, 0.0
            else:
                gz.color = 1.0, 0.0, 0.0


def register():
    bpy.utils.register_class(DOFScaleGizmo)
    bpy.utils.register_class(DOFScaleGizmoGroup)


def unregister():
    bpy.utils.unregister_class(DOFScaleGizmoGroup)
    bpy.utils.unregister_class(DOFScaleGizmo)

from typing import Any

import blf
import bpy
import gpu
from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader
from bpy.types import (
    Gizmo,
    GizmoGroup,
)
import mathutils
from mathutils import Vector
from math import radians

from bms_blender_plugin.common.bml_structs import DofType
from bms_blender_plugin.common.blender_types import BlenderNodeType
from bms_blender_plugin.common.util import get_bml_type, get_parent_dof_or_switch
from bms_blender_plugin.ui_tools.dof_behaviour import is_dof_input_within_limits

translate_shape_indices = (
    (11, 23, 14),
    (11, 14, 2),
    (15, 3, 7),
    (15, 7, 19),
    (2, 4, 10),
    (2, 10, 11),
    (4, 2, 7),
    (4, 7, 6),
    (3, 1, 9),
    (3, 9, 7),
    (9, 8, 6),
    (9, 6, 7),
    (1, 3, 5),
    (1, 5, 0),
    (4, 16, 22),
    (4, 22, 10),
    (18, 6, 5),
    (18, 5, 17),
    (17, 5, 3),
    (17, 3, 15),
    (1, 0, 8),
    (1, 8, 9),
    (0, 5, 6),
    (0, 6, 8),
    (16, 4, 6),
    (16, 6, 18),
    (14, 23, 22),
    (14, 22, 16),
    (16, 18, 19),
    (16, 19, 14),
    (15, 19, 21),
    (15, 21, 13),
    (21, 19, 18),
    (21, 18, 20),
    (13, 12, 17),
    (13, 17, 15),
    (13, 21, 20),
    (13, 20, 12),
    (12, 20, 18),
    (12, 18, 17),
    (14, 19, 7),
    (14, 7, 2),
    (31, 29, 24),
    (31, 24, 30),
    (26, 27, 25),
    (26, 25, 28),
    (32, 33, 34),
    (32, 34, 35),
    (24, 33, 32),
    (24, 32, 27),
    (29, 34, 33),
    (29, 33, 24),
    (25, 35, 34),
    (25, 34, 29),
    (27, 32, 35),
    (27, 35, 25),
    (36, 37, 38),
    (36, 38, 39),
    (30, 37, 36),
    (30, 36, 26),
    (24, 38, 37),
    (24, 37, 30),
    (27, 39, 38),
    (27, 38, 24),
    (26, 36, 39),
    (26, 39, 27),
    (40, 41, 42),
    (40, 42, 43),
    (25, 41, 40),
    (25, 40, 28),
    (29, 42, 41),
    (29, 41, 25),
    (31, 43, 42),
    (31, 42, 29),
    (28, 40, 43),
    (28, 43, 31),
    (44, 45, 46),
    (44, 46, 47),
    (28, 45, 44),
    (28, 44, 26),
    (31, 46, 45),
    (31, 45, 28),
    (30, 47, 46),
    (30, 46, 31),
    (26, 44, 47),
    (26, 47, 30),
    (55, 49, 48),
    (55, 48, 52),
    (48, 49, 50),
    (48, 50, 51),
    (55, 54, 50),
    (55, 50, 49),
    (52, 53, 54),
    (52, 54, 55),
    (48, 51, 53),
    (48, 53, 52),
    (53, 51, 50),
    (53, 50, 54),
)

translate_shape_verts = (
    (0.747423529624939, -0.20666001737117767, 0.014999999664723873),
    (0.7476334571838379, -0.2067919820547104, -0.014999999664723873),
    (0.0, -0.020694613456726074, -0.014999999664723873),
    (1.0003854036331177, -0.02058658003807068, -0.014999999664723873),
    (0.0, -0.020694613456726074, 0.014999999664723873),
    (1.0001040697097778, -0.02058657631278038, 0.014999999664723873),
    (0.9400616884231567, -0.020694613456726074, 0.014999999664723873),
    (0.940278172492981, -0.020694613456726074, -0.014999999664723873),
    (0.7239394187927246, -0.17428049445152283, 0.014999999664723873),
    (0.7241493463516235, -0.17441247403621674, -0.014999999664723873),
    (-1.0, -0.020694613456726074, 0.014999999664723873),
    (-1.0, -0.020694613456726074, -0.014999999664723873),
    (0.747423529624939, 0.20666001737117767, 0.014999999664723873),
    (0.7476334571838379, 0.20679199695587158, -0.014999999664723873),
    (0.0, 0.020694613456726074, -0.014999999664723873),
    (1.0003854036331177, 0.02058658003807068, -0.014999999664723873),
    (0.0, 0.020694613456726074, 0.014999999664723873),
    (1.0001040697097778, 0.02058657631278038, 0.014999999664723873),
    (0.9400616884231567, 0.020694613456726074, 0.014999999664723873),
    (0.940278172492981, 0.020694613456726074, -0.014999999664723873),
    (0.7239394187927246, 0.17428049445152283, 0.014999999664723873),
    (0.7241493463516235, 0.17441247403621674, -0.014999999664723873),
    (-1.0, 0.020694613456726074, 0.014999999664723873),
    (-1.0, 0.020694613456726074, -0.014999999664723873),
    (0.9793052673339844, -0.2706946134567261, 0.014999999664723873),
    (0.9793052673339844, -0.22930538654327393, -0.014999999664723873),
    (1.0206944942474365, -0.2706946134567261, -0.014999999664723873),
    (0.9793052673339844, -0.2706946134567261, -0.014999999664723873),
    (1.0206944942474365, -0.22930538654327393, -0.015000001527369022),
    (0.9793052673339844, -0.22930538654327393, 0.014999999664723873),
    (1.0206944942474365, -0.2706946134567261, 0.015000001527369022),
    (1.0206944942474365, -0.22930538654327393, 0.015000001527369022),
    (0.8793053030967712, -0.2706946134567261, -0.014999999664723873),
    (0.8793053030967712, -0.2706946134567261, 0.014999999664723873),
    (0.8793053030967712, -0.22930538654327393, 0.014999999664723873),
    (0.8793053030967712, -0.22930538654327393, -0.014999999664723873),
    (1.0206944942474365, -0.3706946074962616, -0.014999999664723873),
    (1.0206944942474365, -0.3706946074962616, 0.015000001527369022),
    (0.9793052673339844, -0.3706946074962616, 0.014999999664723873),
    (0.9793052673339844, -0.3706946074962616, -0.014999999664723873),
    (1.0206944942474365, -0.1293053925037384, -0.015000001527369022),
    (0.9793052673339844, -0.1293053925037384, -0.014999999664723873),
    (0.9793052673339844, -0.1293053925037384, 0.014999999664723873),
    (1.0206944942474365, -0.1293053925037384, 0.015000001527369022),
    (1.1206945180892944, -0.2706946134567261, -0.014999999664723873),
    (1.1206945180892944, -0.22930538654327393, -0.015000001527369022),
    (1.1206945180892944, -0.22930538654327393, 0.015000001527369022),
    (1.1206945180892944, -0.2706946134567261, 0.015000001527369022),
    (-1.120694637298584, -0.2706946134567261, -0.014999999664723873),
    (-1.120694637298584, -0.2706946134567261, 0.014999999664723873),
    (-1.120694637298584, -0.22930538654327393, 0.014999999664723873),
    (-1.120694637298584, -0.22930538654327393, -0.014999999664723873),
    (-0.8793054819107056, -0.2706946134567261, -0.014999999664723873),
    (-0.8793054819107056, -0.22930538654327393, -0.015000001527369022),
    (-0.8793054819107056, -0.22930538654327393, 0.015000001527369022),
    (-0.8793054819107056, -0.2706946134567261, 0.015000001527369022),
)


class DOFTranslateGizmo(Gizmo):
    bl_idname = "VIEW3D_GT_bml_dof_translate_gizmo"
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
        context.area.header_text_set(f"DOF Translate {round(value, 2)}")
        return {"RUNNING_MODAL"}

    def setup(self):
        if not hasattr(self, "custom_shape"):
            shader = gpu.shader.from_builtin("3D_UNIFORM_COLOR")
            batch = batch_for_shader(
                shader,
                "TRIS",
                {"pos": translate_shape_verts},
                indices=translate_shape_indices,
            )
            shader.uniform_float("color", (1, 0, 0, 1))
            batch.program_set(shader)
            self.custom_shape = (batch, shader)


class DOFTranslateGizmoGroup(GizmoGroup):
    bl_idname = "OBJECT_GGT_dof_translate"
    bl_label = "DOF Translate Gizmo Group"
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_options = {"3D", "PERSISTENT", "SHOW_MODAL_ALL"}

    draw_text_handler = None
    prev_obj = None

    def __init__(self):
        self.translate_gizmo = None

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
                    f"{round(dof_input, 2)} / {round(context.object.matrix_world.translation.x, 2)}, "
                    f"{round(context.object.matrix_world.translation.y, 2)}, "
                    f"{round(context.object.matrix_world.translation.z, 2)}",
                )

    @classmethod
    def poll(cls, context):
        obj = get_parent_dof_or_switch(context.object)

        if (
            get_bml_type(obj) == BlenderNodeType.DOF
            and obj.dof_type == DofType.TRANSLATE.name
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
                    DOFTranslateGizmoGroup.draw_callback_px,
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
        obj = get_parent_dof_or_switch(context.active_object)
        gz = self.gizmos.new(DOFTranslateGizmo.bl_idname)
        gz.target_set_prop("dof_value", obj, "dof_input")

        mat_rot = mathutils.Matrix.Rotation(radians(90.0), 4, "X")
        gz.matrix_basis = obj.matrix_world.normalized() @ mat_rot
        gz.line_width = 3

        gz.color = 0.0, 1.0, 0.0
        gz.alpha = 0.4

        self.translate_gizmo = gz

    def refresh(self, context):
        obj = context.object
        dof = get_parent_dof_or_switch(obj)

        if dof:
            gz = self.translate_gizmo
            gz.target_set_prop("dof_value", dof, "dof_input")

            mat_rot = mathutils.Matrix.Rotation(radians(90.0), 4, "Y")

            # always face in the direction of the object
            src = obj.matrix_world.translation

            if dof.dof_reverse:
                dest = src - Vector((dof.dof_x, dof.dof_y, dof.dof_z))
            else:
                dest = src + Vector((dof.dof_x, dof.dof_y, dof.dof_z))

            direction = dest - src
            rot_quat = direction.to_track_quat("-Z", "Y")

            mat_rot = rot_quat.to_matrix().to_4x4() @ mat_rot
            mat_rot.translation = obj.matrix_world.translation
            gz.matrix_basis = mat_rot

            if is_dof_input_within_limits(dof, context):
                gz.color = 0.0, 1.0, 0.0
            else:
                gz.color = 1.0, 0.0, 0.0


def register():
    bpy.utils.register_class(DOFTranslateGizmo)
    bpy.utils.register_class(DOFTranslateGizmoGroup)


def unregister():
    bpy.utils.unregister_class(DOFTranslateGizmoGroup)
    bpy.utils.unregister_class(DOFTranslateGizmo)

import bpy

from bpy.props import StringProperty, IntProperty, CollectionProperty
from bpy.types import PropertyGroup, UIList

import math

from bms_blender_plugin.common.blender_types import BlenderNodeType
from bms_blender_plugin.common.bml_structs import DofType
from bms_blender_plugin.common.util import get_bml_type, get_parent_dof_or_switch
from bms_blender_plugin.ui_tools.operators.dof_operators import ResetSingleDof, CreateDofKeyframe
from bms_blender_plugin.ui_tools.panels.base_panel import BasePanel


class DofListItem(PropertyGroup):
    """The DOF List item"""

    name: StringProperty(name="Name", description="", default="Untitled")

    dof_number: IntProperty(name="DOF Number", description="", default=0)


class DofList(UIList):
    """The DOF List"""

    bl_idname = "BML_UL_DofList"

    def __init__(self):
        self.use_filter_show = True

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        custom_icon = "OUTLINER_OB_EMPTY"
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            layout.label(text=f"{item.name} ({item.dof_number})", icon=custom_icon)

        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text=item.dof_number, icon=custom_icon)


class DofPanel(BasePanel, bpy.types.Panel):
    """The 'DOF' panel"""
    bl_label = "DOF"
    bl_idname = "BML_PT_DofPanel"

    @classmethod
    def poll(cls, context):
        return get_bml_type(get_parent_dof_or_switch(context.active_object)) == BlenderNodeType.DOF

    def draw(self, context):
        layout = self.layout
        active_object = context.active_object
        dof = get_parent_dof_or_switch(active_object)
        if get_bml_type(dof) != BlenderNodeType.DOF:
            return

        row = layout.row()
        row.label(text="Type")
        row = layout.row()
        row.template_list(
            DofList.bl_idname,
            "Dof_List",
            context.scene,
            "dof_list",
            dof,
            "dof_list_index",
        )
        
        layout.operator("bml.refresh_dof_list", icon="FILE_REFRESH", text="Refresh DOF/Switch Lists")
        
        row = layout.row()
        row.prop(dof, "dof_type")

        layout.separator()
        row = layout.row()
        row.column().prop(dof, "dof_input")

        reset_operator = row.column().operator(ResetSingleDof.bl_idname, icon="LOOP_BACK", text="")
        reset_operator.dof_to_reset_name = dof.name

        create_keyframe_operator = row.column().operator(CreateDofKeyframe.bl_idname, icon="KEYFRAME", text="")
        create_keyframe_operator.dof_to_keyframe_name = dof.name

        if dof.dof_type == DofType.ROTATE.name:
            layout.label(
                text=f"{round(math.degrees(dof.dof_input))}°"
                     f" x {round(dof.dof_multiplier, 2)}"
                     f" = {round(math.degrees(dof.dof_input * active_object.dof_multiplier), 2)}°"
            )
            layout.prop(dof, "dof_min")
            if dof.dof_multiply_min_max:
                layout.label(
                    text=f"Multiplied minimum: {round(dof.dof_min * dof.dof_multiplier,2)}°"
                )
            layout.prop(dof, "dof_max")
            if dof.dof_multiply_min_max:
                layout.label(
                    text=f"Multiplied maximum: {round(dof.dof_max * dof.dof_multiplier,2)}°"
                )

        elif (
                dof.dof_type == DofType.SCALE.name
                or dof.dof_type == DofType.TRANSLATE.name
        ):
            layout.prop(dof, "dof_x")
            layout.prop(dof, "dof_y")
            layout.prop(dof, "dof_z")

            layout.prop(dof, "dof_min_input")
            if dof.dof_multiply_min_max:
                layout.label(
                    text=f"Multiplied minimum: "
                         f"{round(dof.dof_min_input * dof.dof_multiplier, 2)}"
                )
            layout.prop(dof, "dof_max_input")
            if dof.dof_multiply_min_max:
                layout.label(
                    text=f"Multiplied maximum: "
                         f"{round(dof.dof_max_input * dof.dof_multiplier, 2)}"
                )

        else:
            layout.label(text=f"Unknown DOF type: {active_object.dof_type}")

        layout.separator()
        layout.label(text="DOF Options")
        layout.prop(dof, "dof_check_limits")
        layout.prop(dof, "dof_reverse")
        layout.prop(dof, "dof_normalise")
        layout.prop(dof, "dof_multiplier")
        layout.prop(dof, "dof_multiply_min_max")


def register():
    bpy.utils.register_class(DofListItem)
    bpy.types.Scene.dof_list = CollectionProperty(type=DofListItem)

    bpy.utils.register_class(DofPanel)
    bpy.utils.register_class(DofList)


def unregister():
    bpy.utils.unregister_class(DofList)
    bpy.utils.unregister_class(DofPanel)
    bpy.utils.unregister_class(DofListItem)

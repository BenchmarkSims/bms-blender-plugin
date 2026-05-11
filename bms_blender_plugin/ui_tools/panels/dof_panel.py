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

    def filter_items(self, context, data, propname):
        """Custom filter that matches both name and DOF numbers"""
        dofs = getattr(data, propname)
        
        flt_flags = []
        flt_neworder = []
        
        # Check if there's a search filter active
        if self.filter_name:
            # Start with name-based filtering
            flt_flags = bpy.types.UI_UL_list.filter_items_by_name(
                self.filter_name, self.bitflag_filter_item, dofs, "name"
            )
            
            # Also check if the filter text matches DOF numbers
            filter_text = self.filter_name.lower().strip()
            if filter_text.isdigit():
                for i, dof in enumerate(dofs):
                    # If name filter already matched, keep it
                    if flt_flags[i] & self.bitflag_filter_item:
                        continue
                    
                    # Check if filter matches DOF number (supports partial matching)
                    if str(dof.dof_number).startswith(filter_text):
                        flt_flags[i] |= self.bitflag_filter_item
        else:
            # No filter, sort by name
            flt_neworder = bpy.types.UI_UL_list.sort_items_by_name(dofs, "name")
        
        return flt_flags, flt_neworder

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
        row = layout.row()
        # Persistent ID box shown first
        box_ids = layout.box()
        box_ids.label(text="Persistent DOF Properties:")
        box_ids.prop(dof, "bml_dof_number")
        dof_num = getattr(dof, "bml_dof_number", -1)
        if dof_num < 0:
            row_unset = box_ids.row(align=True)
            row_unset.label(text="Not Assigned", icon="ERROR")
            # Use popup to provide single + scene/collection batch assignment options
            row_unset.operator("bml.assign_dof_popup", text="Assign...", icon="IMPORT")
        else:
            found = False
            try:
                from bms_blender_plugin.common.util import get_dofs
                for de in get_dofs():
                    if de.dof_number == dof_num:
                        found = True
                        break
            except Exception:
                pass
            if not found:
                box_ids.label(text="Warning: DOF number not found in DOF.xml (still exported)", icon="INFO")

        # DOF Type selector moved below persistent ID box for clarity
        type_row = layout.row()
        type_row.prop(dof, "dof_type")

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
        options_box = layout.box()
        options_box.label(text="DOF Options")
        options_box.prop(dof, "dof_check_limits")
        options_box.prop(dof, "dof_reverse")
        options_box.prop(dof, "dof_normalise")
        options_box.prop(dof, "dof_multiplier")
        options_box.prop(dof, "dof_multiply_min_max")


def register():
    bpy.utils.register_class(DofListItem)
    bpy.types.Scene.dof_list = CollectionProperty(type=DofListItem)

    bpy.utils.register_class(DofPanel)
    bpy.utils.register_class(DofList)


def unregister():
    bpy.utils.unregister_class(DofList)
    bpy.utils.unregister_class(DofPanel)
    bpy.utils.unregister_class(DofListItem)

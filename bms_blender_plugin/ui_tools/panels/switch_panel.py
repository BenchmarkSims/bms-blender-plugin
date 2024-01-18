import bpy
from bpy.props import StringProperty, IntProperty, CollectionProperty
from bpy.types import PropertyGroup, UIList

from bms_blender_plugin.common.blender_types import BlenderNodeType
from bms_blender_plugin.common.util import get_bml_type, get_parent_dof_or_switch, get_switches
from bms_blender_plugin.ui_tools.panels.base_panel import BasePanel


class SwitchListItem(PropertyGroup):
    """A single Switch Item - this is read from the XML and stored in the scene for caching"""

    name: StringProperty(
        name="Name", description="A name for this item", default="Untitled"
    )
    switch_number: IntProperty(name="Switch Number", description="", default=0)
    branch_number: IntProperty(name="Branch Number", description="", default=0)


class SwitchList(UIList):
    """Switch UIList."""

    bl_idname = "BML_UL_SwitchList"

    def __init__(self):
        self.use_filter_show = True

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        custom_icon = "OUTLINER_OB_EMPTY"

        if self.layout_type in {"DEFAULT", "COMPACT"}:
            layout.label(text=f"{item.name} ({item.switch_number})", icon=custom_icon)

        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text=item.switch_number, icon=custom_icon)


class SwitchPanel(BasePanel, bpy.types.Panel):
    """The 'Switch' panel"""
    bl_label = "Switch"
    bl_idname = "BML_PT_SwitchPanel"

    @classmethod
    def poll(cls, context):
        return get_bml_type(get_parent_dof_or_switch(context.active_object)) == BlenderNodeType.SWITCH

    def draw(self, context):
        layout = self.layout
        active_object = context.active_object
        switch = get_parent_dof_or_switch(active_object)
        if get_bml_type(switch) != BlenderNodeType.SWITCH:
            return

        row = layout.row()
        row.label(text="Type")
        row = layout.row()
        row.template_list(
            SwitchList.bl_idname,
            "Switch_List",
            context.scene,
            "switch_list",
            switch,
            "switch_list_index",
        )

        comment = get_switches()[switch.switch_list_index].comment

        if comment and comment != "":
            layout.row()
            layout.label(text=comment)

        layout.prop(switch, "switch_default_on")


def register():
    bpy.utils.register_class(SwitchListItem)
    bpy.types.Scene.switch_list = CollectionProperty(type=SwitchListItem)

    bpy.utils.register_class(SwitchPanel)
    bpy.utils.register_class(SwitchList)


def unregister():
    bpy.utils.unregister_class(SwitchList)
    bpy.utils.unregister_class(SwitchPanel)
    bpy.utils.unregister_class(SwitchListItem)

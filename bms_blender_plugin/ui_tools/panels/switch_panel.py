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

    def filter_items(self, context, data, propname):
        """Custom filter that matches both name and switch/branch numbers"""
        switches = getattr(data, propname)
        
        flt_flags = []
        flt_neworder = []
        
        # Check if there's a search filter active
        if self.filter_name:
            # Start with name-based filtering
            flt_flags = bpy.types.UI_UL_list.filter_items_by_name(
                self.filter_name, self.bitflag_filter_item, switches, "name"
            )
            
            # Also check if the filter text matches switch or branch numbers
            filter_text = self.filter_name.lower().strip()
            if filter_text.isdigit() or ':' in filter_text:
                for i, switch in enumerate(switches):
                    # If name filter already matched, keep it
                    if flt_flags[i] & self.bitflag_filter_item:
                        continue
                    
                    # Check if filter matches switch number
                    if filter_text.isdigit() and str(switch.switch_number).startswith(filter_text):
                        flt_flags[i] |= self.bitflag_filter_item
                    # Check if filter matches switch:branch format
                    elif ':' in filter_text:
                        switch_branch_text = f"{switch.switch_number}:{switch.branch_number}"
                        if switch_branch_text.startswith(filter_text):
                            flt_flags[i] |= self.bitflag_filter_item
        else:
            # No filter: preserve original insertion (XML) order which is already numeric (switch_number, branch_number)
            if switches:
                # Flag all items visible; no reordering
                flt_flags = [self.bitflag_filter_item] * len(switches)
                flt_neworder = []  # empty => keep original order
        
        return flt_flags, flt_neworder

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        custom_icon = "OUTLINER_OB_EMPTY"

        if self.layout_type in {"DEFAULT", "COMPACT"}:
            # Display switch number and branch together e.g. 213:24
            layout.label(text=f"{item.name} ({item.switch_number}:{item.branch_number})", icon=custom_icon)

        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text=f"{item.switch_number}:{item.branch_number}", icon=custom_icon)


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
        # Comment (legacy list based)
        try:
            comment = get_switches()[switch.switch_list_index].comment
        except Exception:
            comment = ""
        if comment:
            layout.label(text=comment)

        box = layout.box()
        box.label(text="Persistent IDs for Export")
        row_ids = box.row(align=True)
        row_ids.prop(switch, "bml_switch_number")
        row_ids.prop(switch, "bml_switch_branch")

        # Show mismatch / status info
        sw_num = getattr(switch, "bml_switch_number", -1)
        sw_branch = getattr(switch, "bml_switch_branch", -1)
        if sw_num < 0 or sw_branch < 0:
            row_unset = box.row(align=True)
            row_unset.label(text="Not Assigned", icon="ERROR")
            row_unset.operator("bml.assign_switch_popup", text="Assign...", icon="IMPORT")
        else:
            # Check if present in current list
            found = False
            try:
                for sw in get_switches():
                    if sw.switch_number == sw_num and sw.branch == sw_branch:
                        found = True
                        break
            except Exception:
                pass
            if not found:
                box.label(text="Warning: IDs not found in switch.xml (still exported)", icon="INFO")

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

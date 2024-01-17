import bpy
from bpy.types import Operator, UIList
from bpy.props import EnumProperty

from bms_blender_plugin.common.blender_types import BlenderNodeType
from bms_blender_plugin.common.hotspot import MouseButton, ButtonType
from bms_blender_plugin.common.util import get_bml_type, get_callbacks, Icons
from bms_blender_plugin.ui_tools.panels.base_panel import BasePanel


class CallbackList(UIList):
    """Callback UIList."""

    bl_idname = "BML_UL_CallbackList"

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        if item.button_type == ButtonType.SWITCH.name:
            button_type_icon = Icons.toggle_icon_id
        elif item.button_type == ButtonType.PUSH_BUTTON.name:
            button_type_icon = Icons.push_button_icon_id
        elif item.button_type == ButtonType.WHEEL.name:
            button_type_icon = Icons.wheel_icon_id
        else:
            button_type_icon = 0
            print(f"Warning: unknown button type {item.button_type}")

        # Make sure your code supports all 3 layout types
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            column = layout.column()

            if item.mouse_button == MouseButton.LEFT_CLICK.name:
                mouse_icon = "MOUSE_LMB"
            else:
                mouse_icon = "MOUSE_RMB"
            column.label(text="", icon=mouse_icon)

            column = layout.column()
            column.label(text=f"{item.callback_name}", icon_value=button_type_icon)

            column = layout.column()
            column.operator(RemoveHotspotCallback.bl_idname, icon="X", text="")

        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text=item.callback_name, icon=button_type_icon)
            layout.label(text="", icon=button_type_icon)


class AddHotspotCallback(Operator):
    """Adds a new callback to the active Hotspot"""

    bl_idname = "bml.add_hotspot_callback"
    bl_label = "Add Callback"
    bl_description = "Adds a new Callback to a Hotspot"
    bl_options = {"REGISTER", "UNDO"}

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        hotspot = context.active_object
        if not get_bml_type(hotspot) == BlenderNodeType.HOTSPOT:
            return

        callback = hotspot.bml_hotspot_callbacks.add()

        if (
                0 < context.scene.bml_all_callbacks_selected_index < len(get_callbacks())
        ):
            callback.callback_name = get_callbacks()[
                context.scene.bml_all_callbacks_selected_index
            ].name
        else:
            callback.callback_name = get_callbacks()[0].name

        return {"FINISHED"}


class RemoveHotspotCallback(Operator):
    """Removes a callback from the active Hotspot"""

    bl_idname = "bml.remove_hotspot_callback"
    bl_label = "Remove Callback"
    bl_description = "Removes the selected Callback from a Hotspot"
    bl_options = {"REGISTER", "UNDO"}

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        hotspot = context.active_object
        if not get_bml_type(hotspot) == BlenderNodeType.HOTSPOT:
            return

        # also make sure the list index doesn't point on an invalid entry
        hotspot.bml_hotspot_selected_callback_index = min(
            max(0, hotspot.bml_hotspot_selected_callback_index - 1),
            len(hotspot.bml_hotspot_callbacks) - 1,
        )
        hotspot.bml_hotspot_callbacks.remove(
            hotspot.bml_hotspot_selected_callback_index
        )
        return {"FINISHED"}


class AllCallbacksList(UIList):
    """Callback UIList."""

    bl_idname = "BML_UL_AllCallbacksList"

    def __init__(self):
        self.use_filter_show = True

    def filter_items(self, context, data, propname):
        callbacks = getattr(data, propname)

        flt_flags = []
        flt_neworder = []

        # filtering by group name
        group_filter = context.scene.bml_callback_groups_filter

        if group_filter != "All":
            flt_flags = bpy.types.UI_UL_list.filter_items_by_name(
                group_filter, self.bitflag_filter_item, callbacks, "group"
            )
        else:
            flt_neworder = bpy.types.UI_UL_list.sort_items_by_name(callbacks, "group")

        return flt_flags, flt_neworder

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            layout.alignment = "LEFT"
            column = layout.column()
            column.label(text=item.name)

            column = layout.column()
            column.label(text=item.group)

        elif self.layout_type in {"GRID"}:
            layout.alignment = "LEFT"
            column = layout.column()
            column.label(text=item.name)

            column = layout.column()
            column.label(text=item.group)


class HotspotPanel(BasePanel, bpy.types.Panel):
    """The 'Hotspot' panel"""
    bl_label = "Hotspot"
    bl_idname = "BML_PT_HotspotPanel"

    @classmethod
    def poll(cls, context):
        return get_bml_type(context.active_object) == BlenderNodeType.HOTSPOT

    def draw(self, context):
        if get_bml_type(context.active_object) != BlenderNodeType.HOTSPOT:
            return

        hotspot_object = context.active_object
        layout = self.layout

        row = layout.row()
        row.prop(hotspot_object, "bml_hotspot_size", text="Size")
        if len(hotspot_object.bml_hotspot_callbacks) > 0:
            row = layout.row()
            row.template_list(
                CallbackList.bl_idname,
                CallbackList.bl_idname,
                hotspot_object,
                "bml_hotspot_callbacks",
                hotspot_object,
                "bml_hotspot_selected_callback_index",
                rows=1,
            )

        layout.separator()
        if (
            len(hotspot_object.bml_hotspot_callbacks) > 0
            and 0 <= hotspot_object.bml_hotspot_selected_callback_index < len(hotspot_object.bml_hotspot_callbacks)
        ):
            selected_callback = hotspot_object.bml_hotspot_callbacks[
                hotspot_object.bml_hotspot_selected_callback_index
            ]
            layout.prop(selected_callback, "callback_name", text="Callback")
            layout.prop(selected_callback, "mouse_button", text="Mouse")
            layout.prop(selected_callback, "button_type", text="Type")
            layout.prop(selected_callback, "sound_id", text="Sound ID")

        layout.separator()
        box = layout.box()
        row = box.row()
        row.prop(context.scene, "bml_callback_groups_filter")
        row = box.row()
        row.template_list(
            AllCallbacksList.bl_idname,
            AllCallbacksList.bl_idname,
            context.scene,
            "bml_all_callbacks",
            context.scene,
            "bml_all_callbacks_selected_index",
        )

        row = box.row()
        row.operator(AddHotspotCallback.bl_idname, icon="ADD")


class CallbackItem(bpy.types.PropertyGroup):
    """A single callback item - their list is read from the XML file and stored in the scene itself"""
    name: bpy.props.StringProperty(default="")
    group: bpy.props.StringProperty()


def register():
    bpy.types.Object.bml_hotspot_selected_callback_index = bpy.props.IntProperty(
        name="Index for the selected callback item"
    )
    bpy.utils.register_class(CallbackList)

    bpy.utils.register_class(CallbackItem)
    bpy.types.Scene.bml_all_callbacks = bpy.props.CollectionProperty(type=CallbackItem)
    bpy.types.Scene.bml_all_callbacks_selected_index = bpy.props.IntProperty(default=0)

    callback_groups_filter_enum_values = [("All", "All", "All")]
    for group in sorted(set((cb.group for cb in get_callbacks()))):
        # get all unique groups from the callback objects
        callback_groups_filter_enum_values.append(
            (
                group,
                group,
                group,
            )
        )
    bpy.types.Scene.bml_callback_groups_filter = EnumProperty(
        name="Group",
        description="Built-In Templates",
        items=callback_groups_filter_enum_values,
        default="All",
    )

    bpy.utils.register_class(AllCallbacksList)

    bpy.utils.register_class(AddHotspotCallback)
    bpy.utils.register_class(RemoveHotspotCallback)
    bpy.utils.register_class(HotspotPanel)


def unregister():
    bpy.utils.unregister_class(HotspotPanel)
    bpy.utils.unregister_class(RemoveHotspotCallback)
    bpy.utils.unregister_class(AddHotspotCallback)
    bpy.utils.unregister_class(CallbackList)
    bpy.utils.unregister_class(AllCallbacksList)
    bpy.utils.unregister_class(CallbackItem)

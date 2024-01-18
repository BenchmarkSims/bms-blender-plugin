import bpy

from bpy.types import Operator, UIList
from bpy.props import CollectionProperty, IntProperty

from bms_blender_plugin.ui_tools.panels.base_panel import BasePanel
from bms_blender_plugin.ui_tools.panels.lod_and_material_sets_panel import LodAndMaterialSetsPanel


class LodListItem(bpy.types.PropertyGroup):
    file_suffix: bpy.props.StringProperty(name="Suffix")
    viewing_distance: bpy.props.IntProperty(name="Viewing Distance (ft)")
    collection: bpy.props.PointerProperty(name="Collection", type=bpy.types.Collection)


class LodList(UIList):
    """LOD UIList."""
    bl_idname = "BML_UL_LodList"

    def __init__(self):
        self.use_filter_show = False

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            if item.collection:
                layout.column().label(text=f"{item.collection.name}")
            else:
                layout.column().label(text="No collection set", icon="ERROR")
            layout.column().label(text=f"{item.viewing_distance} ft")
            operator = layout.column().operator(RemoveLod.bl_idname, icon="X", text="")
            operator.item_index = index

        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            if item.collection:
                layout.column().label(text=f"{item.collection.name}")
            else:
                layout.column().label(text="No collection set", icon="ERROR")
            layout.column().label(text=f"{item.viewing_distance} ft")
            operator = layout.column().operator(RemoveLod.bl_idname, icon="X", text="")
            operator.item_index = index


class AddLod(Operator):
    bl_idname = "bml.add_lod"
    bl_label = "Add LOD"
    bl_description = "Adds a new LOD to be exported"

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        item = context.scene.lod_list.add()
        item.file_suffix = f"_{len(context.scene.lod_list) - 1}"  # traditionally the first model is Model_0
        return {"FINISHED"}


class RemoveLod(Operator):
    bl_idname = "bml.remove_lod"
    bl_label = ""
    bl_description = "Removes an existing LOD"
    item_index: IntProperty(default=-1)

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        context.scene.lod_list.remove(self.item_index)
        return {"FINISHED"}


class LodPanel(BasePanel, bpy.types.Panel):
    bl_label = "LODs"
    bl_idname = "BML_PT_LodPanel"
    bl_parent_id = LodAndMaterialSetsPanel.bl_idname

    def draw(self, context):
        layout = self.layout

        if len(context.scene.lod_list) > 0:
            layout.row().template_list(
                LodList.bl_idname,
                LodList.bl_idname,
                context.scene,
                "lod_list",
                context.scene,
                "lod_list_selected_index",
                rows=1,
            )

        if (
                len(context.scene.lod_list) > 0
                and 0 <= context.scene.lod_list_selected_index < len(context.scene.lod_list)
        ):
            selected_lod = context.scene.lod_list[
                context.scene.lod_list_selected_index
            ]
            layout.prop(selected_lod, "collection")
            layout.prop(selected_lod, "viewing_distance")
            layout.prop(selected_lod, "file_suffix")

        layout.separator()
        layout.row().operator(AddLod.bl_idname, icon="ADD")


def register():
    bpy.utils.register_class(LodListItem)
    bpy.types.Scene.lod_list = CollectionProperty(type=LodListItem)
    bpy.types.Scene.lod_list_selected_index = bpy.props.IntProperty(default=0)

    bpy.utils.register_class(AddLod)
    bpy.utils.register_class(RemoveLod)

    bpy.utils.register_class(LodList)
    bpy.utils.register_class(LodAndMaterialSetsPanel)
    bpy.utils.register_class(LodPanel)


def unregister():
    bpy.utils.unregister_class(LodPanel)
    bpy.utils.unregister_class(LodList)
    bpy.utils.unregister_class(LodAndMaterialSetsPanel)
    bpy.utils.unregister_class(RemoveLod)
    bpy.utils.unregister_class(AddLod)
    bpy.utils.unregister_class(LodListItem)

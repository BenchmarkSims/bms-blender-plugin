import bpy
from bpy.props import (
    CollectionProperty,
    IntProperty,
    StringProperty,
    BoolProperty,
)
from bpy.types import Operator, UIList, PropertyGroup

from bms_blender_plugin.ui_tools.operators.material_sets_operators import (
    DeleteMaterialSet,
    CreateMaterialSet,
    get_active_material_set,
)
from bms_blender_plugin.ui_tools.panels.base_panel import BasePanel
from bms_blender_plugin.ui_tools.panels.lod_and_material_sets_panel import (
    LodAndMaterialSetsPanel,
)

edit_dialog_material_set_index = -1


def on_alternative_material_update(material_alternative, context):
    if (
        material_alternative.previous_alternative_material
        == material_alternative.alternative_material
    ):
        return
    if (
        context.scene.bml_material_sets_active_index == 0
        or edit_dialog_material_set_index
        != context.scene.bml_material_sets_active_index
    ):
        return

    # remove the previous material from the model:
    if material_alternative.previous_alternative_material:
        print("updating material of an active dataset - has previous material")
        for obj in context.scene.objects:
            if (
                obj.type == "MESH"
                and len(obj.data.materials) > 0
                and (
                    obj.data.materials[0]
                    == material_alternative.previous_alternative_material
                    or obj.data.materials[0] == material_alternative.base_material
                )
            ):
                obj.data.materials[0] = material_alternative.alternative_material

    # apply the current alternative material to the model:
    else:
        print("updating material of an active dataset - no previous material")
        for obj in context.scene.objects:
            if (
                obj.type == "MESH"
                and len(obj.data.materials) > 0
                and obj.data.materials[0] == material_alternative.base_material
            ):
                obj.data.materials[0] = material_alternative.alternative_material

    material_alternative.previous_alternative_material = (
        material_alternative.alternative_material
    )


class BaseMaterialList(UIList):
    """BaseMaterial UIList."""

    bl_idname = "BML_UL_BaseMaterialList"

    def __init__(self):
        self.use_filter_show = False

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        if self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"

        layout.column().prop(item, "bml_is_base_material", text="")
        col = layout.column()
        col.label(text=f"{item.name}")
        col.enabled = item.bml_is_base_material


class EditMaterialSetDialog(Operator):
    """Shows the dialog to edit a Material Set"""

    bl_idname = "bml.edit_material_set_dialog"
    bl_label = "Edit Material Sets"

    base_material_selected_index: IntProperty()
    material_set_index: IntProperty()
    material_alternatives_selected_index: IntProperty(default=-1)

    def draw(self, context):
        layout = self.layout
        material_set = context.scene.bml_material_sets[self.material_set_index]
        self.bl_label = material_set.name
        layout.prop(material_set, "name")

        col = layout.grid_flow()
        box = col.box()
        box.label(text="Base Materials")

        box.template_list(
            BaseMaterialList.bl_idname,
            BaseMaterialList.bl_idname,
            bpy.data,
            "materials",
            self,
            "base_material_selected_index",
        )

        box = col.box()
        box.label(text="Material Alternatives")

        box.template_list(
            MaterialAlternativeList.bl_idname,
            MaterialAlternativeList.bl_idname,
            material_set,
            "material_alternatives",
            self,
            "material_alternatives_selected_index",
        )

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        global edit_dialog_material_set_index
        edit_dialog_material_set_index = -1
        return {"FINISHED"}

    def invoke(self, context, event):
        global edit_dialog_material_set_index
        edit_dialog_material_set_index = self.material_set_index
        return context.window_manager.invoke_props_dialog(self, width=500)


class MaterialSetList(UIList):
    """Material Set UIList."""

    bl_idname = "BML_UL_MaterialSetList"

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        if self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"

        if index == context.scene.bml_material_sets_active_index:
            layout.column().label(text=f"{item.name}", icon="HIDE_OFF")
        else:
            layout.column().label(text=f"{item.name}", icon="HIDE_ON")
        if index != 0:
            operator = layout.column().operator(
                EditMaterialSetDialog.bl_idname, icon="GREASEPENCIL", text=""
            )
            operator.material_set_index = index
            operator = layout.column().operator(
                DeleteMaterialSet.bl_idname, icon="X", text=""
            )
            operator.material_set_index = index


class MaterialAlternativeList(UIList):
    """Material Set Alternatives List."""

    bl_idname = "BML_UL_MaterialAlternativeList"

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        if self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"

        col = layout.column()
        col.label(text=f"{item.base_material.name}")
        col = layout.column()
        col.label(text="", icon="ARROW_LEFTRIGHT")
        col.alignment = "CENTER"
        layout.column().prop(item, "alternative_material", text="")


class MaterialSetsPanel(BasePanel, bpy.types.Panel):
    bl_label = "Material Sets"
    bl_idname = "BML_PT_MaterialSetsPanel"
    bl_parent_id = LodAndMaterialSetsPanel.bl_idname

    def draw(self, context):
        layout = self.layout

        if len(context.scene.bml_material_sets) > 1:
            layout.box().template_list(
                MaterialSetList.bl_idname,
                MaterialSetList.bl_idname,
                context.scene,
                "bml_material_sets",
                context.scene,
                "bml_material_sets_active_index",
            )
        layout.operator(CreateMaterialSet.bl_idname, icon="ADD")


def apply_selected_material_set(obj, context):
    current_material_index = context.scene.bml_material_sets_previous_active_index
    current_material_set = context.scene.bml_material_sets[current_material_index]
    new_material_set = context.scene.bml_material_sets[
        context.scene.bml_material_sets_active_index
    ]

    def _apply_material_set(material_set: MaterialSet, revert=False):
        print(f"applying material set {material_set.name} (revert = {revert}) ")
        for scene_obj in context.scene.objects:
            if scene_obj.type == "MESH" and len(scene_obj.material_slots) > 0:
                # do not revert, apply the alternatives
                if not revert:
                    for alternative in material_set.material_alternatives:
                        if alternative.base_material == scene_obj.data.materials[0]:
                            scene_obj.data.materials[0] = alternative.alternative_material

                # revert to the base material set
                else:
                    for alternative in material_set.material_alternatives:
                        if alternative.alternative_material == scene_obj.data.materials[0]:
                            scene_obj.data.materials[0] = alternative.base_material

    # already applied, nothing to do
    if new_material_set == current_material_set:
        return

    if not current_material_set.is_base_material_set:
        _apply_material_set(current_material_set, revert=True)

    _apply_material_set(new_material_set)

    context.scene.bml_material_sets_previous_active_index = context.scene.bml_material_sets_active_index
    context.space_data.shading.type = "MATERIAL"


class MaterialAlternative(PropertyGroup):
    base_material: bpy.props.PointerProperty(type=bpy.types.Material)
    alternative_material: bpy.props.PointerProperty(
        type=bpy.types.Material, update=on_alternative_material_update
    )
    previous_alternative_material: bpy.props.PointerProperty(type=bpy.types.Material)


def revert_to_base_material_set(context, start_collection):
    active_material_set = get_active_material_set(context)
    if not active_material_set or active_material_set.is_base_material_set:
        return

    def _revert_recursive(collection):
        for obj in collection.objects:
            if obj.type == "MESH" and len(obj.material_slots) > 0:
                for material_alternative in active_material_set.material_alternatives:
                    if (
                        material_alternative.alternative_material
                        == obj.data.materials[0]
                    ):
                        obj.data.materials[0] = material_alternative.base_material

        for child in collection.children:
            _revert_recursive(child)

    _revert_recursive(start_collection)


class MaterialSet(PropertyGroup):
    name: StringProperty(name="Name")
    material_alternatives: CollectionProperty(type=MaterialAlternative)
    is_base_material_set: BoolProperty(default=False)


def register():
    bpy.utils.register_class(MaterialAlternative)
    bpy.utils.register_class(MaterialSet)
    bpy.types.Scene.bml_material_sets = CollectionProperty(type=MaterialSet)

    bpy.utils.register_class(BaseMaterialList)
    bpy.types.Scene.bml_material_sets_active_index = IntProperty(
        update=apply_selected_material_set
    )
    bpy.types.Scene.bml_material_sets_previous_active_index = IntProperty(default=0)

    bpy.utils.register_class(EditMaterialSetDialog)
    bpy.utils.register_class(MaterialSetList)
    bpy.utils.register_class(MaterialAlternativeList)

    bpy.utils.register_class(MaterialSetsPanel)


def unregister():
    bpy.utils.unregister_class(MaterialSetsPanel)
    bpy.utils.unregister_class(BaseMaterialList)

    bpy.utils.unregister_class(MaterialAlternativeList)
    bpy.utils.unregister_class(MaterialSetList)
    bpy.utils.unregister_class(EditMaterialSetDialog)

    bpy.utils.unregister_class(MaterialSet)
    bpy.utils.unregister_class(MaterialAlternative)

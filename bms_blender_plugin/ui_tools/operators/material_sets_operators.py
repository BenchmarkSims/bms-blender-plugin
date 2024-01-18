import bpy
from bpy.types import Operator
from bpy.props import IntProperty, BoolProperty


class CreateMaterialSet(Operator):
    bl_idname = "bml.create_material_set"
    bl_label = "Create Material Set"
    bl_description = "Creates a new Material Set"

    @classmethod
    def create_base_material_set(cls, context):
        if len(context.scene.bml_material_sets) == 0:
            base_material_set = bpy.context.scene.bml_material_sets.add()
            base_material_set.name = "Base Material Set"
            base_material_set.is_base_material_set = True

            for obj in context.scene.objects:
                if obj.type == "MESH" and len(obj.data.materials) > 0:
                    obj.data.materials[0].bml_is_base_material = True

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        self.create_base_material_set(context)

        material_set = context.scene.bml_material_sets.add()
        material_set.name = f"Set {len(context.scene.bml_material_sets) - 1}"

        for material in bpy.data.materials:
            if material.bml_is_base_material:
                material_alternative = material_set.material_alternatives.add()
                material_alternative.base_material = material
                material_alternative.alternative_material = material

        context.scene.bml_material_sets_active_index = (
            len(context.scene.bml_material_sets) - 1
        )
        return {"FINISHED"}


class DeleteMaterialSet(Operator):
    bl_idname = "bml.delete_material_set"
    bl_label = "Delete Material Set"
    bl_description = "Deletes a Material Set"
    bl_options = {"UNDO"}

    # noinspection PyMethodMayBeStatic
    material_set_index: IntProperty(default=-1)

    def execute(self, context):
        if self.material_set_index == 0:
            self.report({"WARNING", "Can not delete the Base Material Set"})
            return {"FINISHED"}

        # if the user deletes a material set which is currently active, revert to the base set first
        material_set_to_delete = context.scene.bml_material_sets[self.material_set_index]
        if get_active_material_set(context) == material_set_to_delete:
            context.scene.bml_material_sets_active_index = 0
            context.scene.bml_material_sets_previous_active_index = 0

        context.scene.bml_material_sets.remove(self.material_set_index)
        return {"FINISHED"}


def on_base_material_set(material, context):
    # SET
    if material.bml_is_base_material:
        for material_set in context.scene.bml_material_sets:
            material_alternative = material_set.material_alternatives.add()
            material_alternative.base_material = material
            material_alternative.alternative_material = material

    # UNSET
    else:
        for material_set in context.scene.bml_material_sets:
            for index, material_alternative in enumerate(material_set.material_alternatives):
                if material_alternative.base_material == material:
                    material_set.material_alternatives.remove(index)

def get_active_material_set(context):
    if len(context.scene.bml_material_sets) == 0:
        return None
    return context.scene.bml_material_sets[context.scene.bml_material_sets_active_index]

def register():
    bpy.types.Material.bml_is_base_material = BoolProperty(default=False, update=on_base_material_set)

    bpy.utils.register_class(CreateMaterialSet)
    bpy.utils.register_class(DeleteMaterialSet)


def unregister():
    bpy.utils.unregister_class(DeleteMaterialSet)
    bpy.utils.unregister_class(CreateMaterialSet)

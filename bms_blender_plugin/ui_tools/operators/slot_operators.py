import bpy

from bpy.types import Operator

from bms_blender_plugin.common.blender_types import BlenderNodeType
from bms_blender_plugin.common.util import Icons

class CreateSlot(Operator):
    bl_idname = "bml.create_slot"
    bl_label = "Create Slot"
    bl_description = "Adds a new Slot to the scene"
    bl_options = {'REGISTER', 'UNDO'}

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        slot_object = bpy.data.objects.new("Slot #0", None)
        slot_object.bml_type = str(BlenderNodeType.SLOT)
        slot_object.empty_display_type = "IMAGE"
        slot_object.empty_display_size = 2
        img = Icons.get_slot_image()
        slot_object.data = img

        if context.active_object:
            # assumes that every object is linked to at least one collection
            context.active_object.users_collection[0].objects.link(slot_object)
            slot_object.parent = context.active_object.parent
            slot_object.matrix_world.translation = context.active_object.matrix_world.translation
        else:
            context.collection.objects.link(slot_object)

        # select the new object
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = slot_object
        slot_object.select_set(True)

        return {"FINISHED"}


def register():
    bpy.utils.register_class(CreateSlot)


def unregister():
    bpy.utils.unregister_class(CreateSlot)

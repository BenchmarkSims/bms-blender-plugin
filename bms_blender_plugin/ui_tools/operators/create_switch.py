import bpy
from bpy.types import Operator

from bms_blender_plugin.common.blender_types import BlenderNodeType
from bms_blender_plugin.common.util import get_switches


class CreateSwitch(Operator):
    """Add a new switch to the scene"""

    bl_idname = "bml.create_switch"
    bl_label = "Create Switch"
    bl_description = "Adds a new switch to the scene"
    bl_options = {'REGISTER', 'UNDO'}

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        # read all switch values from the XML file and store them in the active scene
        if len(context.scene.switch_list) == 0:
            for switch in get_switches():
                item = context.scene.switch_list.add()
                item.name = switch.name
                item.switch_number = int(switch.switch_number)
                item.branch_number = int(switch.branch)

        switch = get_switches()[0]
        switch_object = bpy.data.objects.new(
            f"Switch - {switch.name} ({switch.switch_number})", None
        )
        switch_object.bml_type = str(BlenderNodeType.SWITCH)

        if context.active_object:
            # assumes that every object is linked to at least one collection
            context.active_object.users_collection[0].objects.link(switch_object)
            switch_object.parent = context.active_object.parent
            switch_object.matrix_world.translation = context.active_object.matrix_world.translation

        else:
            context.collection.objects.link(switch_object)

        # move any selected objects to the new switch
        for obj in context.selected_objects:
            obj.parent = switch_object
            obj.matrix_parent_inverse = switch_object.matrix_world.inverted()
            obj.select_set(True)

        # select the new object
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = switch_object
        switch_object.select_set(True)

        return {"FINISHED"}


def register():
    bpy.utils.register_class(CreateSwitch)


def unregister():
    bpy.utils.unregister_class(CreateSwitch)

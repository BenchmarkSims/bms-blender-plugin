import bpy
from bpy.types import Operator

from bms_blender_plugin.common.blender_types import BlenderNodeType


class CreatePBRLight(Operator):
    bl_idname = "bml.create_pbr_light"
    bl_label = "Create Billboard Light"
    bl_description = "Adds a new Billboard Light"

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        bpy.ops.mesh.primitive_plane_add(
            size=2.0,
            calc_uvs=True,
            enter_editmode=False,
            align="WORLD",
            location=(0.0, 0.0, 0.0),
            rotation=(0.0, 0.0, 0.0),
            scale=(0.0, 0.0, 0.0),
        )

        obj = bpy.context.active_object
        obj.name = "Billboard Light"
        obj.color = (0, 1, 1, 1)
        obj.bml_type = str(BlenderNodeType.PBR_LIGHT)

        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:  # iterate through areas in current screen
                if area.type == "VIEW_3D":
                    for (
                        space
                    ) in area.spaces:  # iterate through spaces in current VIEW_3D area
                        if space.type == "VIEW_3D":  # check if space is a 3D view
                            space.shading.color_type = "OBJECT"
        return {"FINISHED"}


def register():
    bpy.utils.register_class(CreatePBRLight)


def unregister():
    bpy.utils.unregister_class(CreatePBRLight)

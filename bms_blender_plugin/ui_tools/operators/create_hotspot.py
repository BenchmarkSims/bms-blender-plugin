import bpy
from bpy.types import Operator

from bms_blender_plugin.common.blender_types import BlenderNodeType
from bms_blender_plugin.common.hotspot import MouseButton, ButtonType
from bms_blender_plugin.common.util import Icons, get_callbacks


class CreateHotspot(Operator):
    """Add a new hotspot to the scene"""

    bl_idname = "bml.create_hotspot"
    bl_label = "Create Hotspot"
    bl_description = "Adds a new Hotspot to the scene"
    bl_options = {'REGISTER', 'UNDO'}

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        # populate the UI list for the hotspot panel
        if len(context.scene.bml_all_callbacks) == 0:
            for callback in get_callbacks():
                new_callback = bpy.context.scene.bml_all_callbacks.add()
                new_callback.name = callback.name
                new_callback.group = callback.group

        hotspot = bpy.data.objects.new(
            "Hotspot", None
        )
        hotspot.bml_type = str(BlenderNodeType.HOTSPOT)
        hotspot.empty_display_type = "IMAGE"
        hotspot.empty_display_size = 1
        img = Icons.get_hotspot_image()
        hotspot.data = img

        if context.active_object:
            context.active_object.users_collection[0].objects.link(hotspot)
            hotspot.location = context.active_object.location

        else:
            context.collection.objects.link(hotspot)
        # select the new object
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = hotspot
        hotspot.select_set(True)

        return {"FINISHED"}


class HotspotCallback(bpy.types.PropertyGroup):
    callback_name: bpy.props.StringProperty(default="")
    sound_id: bpy.props.IntProperty(default=129, min=0, max=999)
    mouse_button: bpy.props.EnumProperty(
        items=(
            (MouseButton.LEFT_CLICK.name, "Left Click", "Left Click"),
            (MouseButton.RIGHT_CLICK.name, "Right Click", "Right Click"),
        ),
        default=MouseButton.LEFT_CLICK.name,
        name="Mouse Button"
    )
    button_type: bpy.props.EnumProperty(
        items=(
            (ButtonType.SWITCH.name, "Toggle Switch", "Toggle Switch"),
            (ButtonType.PUSH_BUTTON.name, "Push Button", "Push Button"),
            (ButtonType.WHEEL.name, "Wheel", "Wheel"),
        ),
        default=ButtonType.SWITCH.name,
        name="Button Type"
    )


def register():
    bpy.utils.register_class(HotspotCallback)
    bpy.types.Object.bml_hotspot_callbacks = bpy.props.CollectionProperty(type=HotspotCallback)
    bpy.types.Object.bml_hotspot_size = bpy.props.IntProperty(default=25, min=5, max=150, step=5)
    bpy.utils.register_class(CreateHotspot)


def unregister():
    bpy.utils.unregister_class(CreateHotspot)
    bpy.utils.unregister_class(HotspotCallback)

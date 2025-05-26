import bpy

from bms_blender_plugin.common.bml_structs import DofType
from bms_blender_plugin.common.blender_types import BlenderNodeType
from bms_blender_plugin.ui_tools.dof_behaviour import (
    dof_update_input,
    dof_reverse,
    update_dof_display_type,
    update_switch_or_dof_name, dof_set_input, dof_get_input,
)
from bms_blender_plugin.ui_tools.slot_behaviour import update_slot_number


def register_blender_properties():
    bpy.types.Scene.color = bpy.props.FloatVectorProperty(
        subtype="COLOR_GAMMA", size=4, min=0.0, max=1.0
    )

    # Generic
    bpy.types.Object.bml_type = bpy.props.EnumProperty(
        name="BML Type",
        description="BML Type",
        items=(
            (str(BlenderNodeType.PBR_LIGHT), "PBR Light", "A BML billboard light"),
            (str(BlenderNodeType.SLOT), "Slot", "A BML slot for droppable ordnance"),
            (str(BlenderNodeType.DOF), "DOF", "A BML DOF"),
            (
                str(BlenderNodeType.SWITCH),
                "Switch",
                "A BML Switch to toggle visibility",
            ),
            (
                str(BlenderNodeType.HOTSPOT),
                "Hotspot",
                "A clickable BML Hotspot for cockpits",
            ),
            (
                str(BlenderNodeType.BBOX),
                "Bounding Box",
                "A Bounding Box to be exported to the Parent.dat",
            ),
            (str(BlenderNodeType.NONE), "None", "None"),
        ),
        default=str(BlenderNodeType.NONE),
    )

    bpy.types.Object.bml_do_not_merge = bpy.props.BoolProperty(
        name="Do not merge",
        description="Will not merge the mesh with others which have the same material",
        default=False,
    )

    # Lights
    bpy.types.Object.bml_light_directional = bpy.props.BoolProperty(
        name="Directional",
        description="Indicates whether the light should be directional",
        default=False,
    )

    # Slots
    bpy.types.Object.bml_slot_number = bpy.props.IntProperty(
        name="Slot number",
        description="Slot number (0-20)",
        default=0,
        min=0,
        max=20,
        update=update_slot_number,
    )

    # Switches
    bpy.types.Object.switch_list_index = bpy.props.IntProperty(
        name="Index for switch_list", default=0, update=update_switch_or_dof_name
    )
    bpy.types.Object.switch_default_on = bpy.props.BoolProperty(
        name="Default ON", description="The switch is ON by default", default=False
    )

    # DOFs
    bpy.types.Object.dof_list_index = bpy.props.IntProperty(
        name="Index for dof_list", default=0, update=update_switch_or_dof_name
    )

    bpy.types.Object.dof_type = bpy.props.EnumProperty(
        name="Type",
        description="DOF Type",
        items=(
            (DofType.ROTATE.name, "Rotate", "Rotate around the Z axis"),
            (DofType.TRANSLATE.name, "Translate", "Move the objects"),
            (DofType.SCALE.name, "Scale", "Scale the objects"),
        ),
        update=update_dof_display_type,
    )

    # dof_input must be keyframed, so only use custom getters/setters
    bpy.types.Object.dof_input = bpy.props.FloatProperty(
        name="DOF Input",
        description="DOF input value",
        default=0,
        min=-10,
        max=10,
        set=dof_set_input,
        get=dof_get_input
    )

    bpy.types.Object.dof_min = bpy.props.FloatProperty(
        name="Minimum °",
        description="Minimum DOF rotation value",
        default=0,
        min=-360,
        max=360,
        update=dof_update_input,
    )
    bpy.types.Object.dof_max = bpy.props.FloatProperty(
        name="Maximum °",
        description="Maximum DOF rotation value",
        default=180,
        min=-360,
        max=360,
        update=dof_update_input,
    )

    bpy.types.Object.dof_min_input = bpy.props.FloatProperty(
        name="Minimum Input",
        description="Minimum DOF input value",
        default=0,
        min=-10,
        max=10,
        update=dof_update_input,
    )
    bpy.types.Object.dof_max_input = bpy.props.FloatProperty(
        name="Maximum Input",
        description="Maximum DOF input value",
        default=0,
        min=-10,
        max=10,
        update=dof_update_input,
    )

    bpy.types.Object.dof_x = bpy.props.FloatProperty(
        name="X",
        description="Factor to scale/translate the object on the X axis",
        default=1,
        min=-1024,
        max=1024,
        update=dof_update_input,
    )
    bpy.types.Object.dof_y = bpy.props.FloatProperty(
        name="Y",
        description="Factor to scale/translate the object on the Y axis",
        default=1,
        min=-1024,
        max=1024,
        update=dof_update_input,
    )
    bpy.types.Object.dof_z = bpy.props.FloatProperty(
        name="Z",
        description="Factor to scale/translate the object on the Z axis",
        default=1,
        min=-1024,
        max=1024,
        update=dof_update_input,
    )

    bpy.types.Object.dof_check_limits = bpy.props.BoolProperty(
        name="Check Limits",
        description="Sets if the DOF should travel between the min / max values",
        default=False,
        update=dof_update_input,
    )
    bpy.types.Object.dof_reverse = bpy.props.BoolProperty(
        name="Reverse",
        description="Sets if the DOFs direction should be reversed",
        default=False,
        update=dof_reverse,
    )
    bpy.types.Object.dof_normalise = bpy.props.BoolProperty(
        name="Normalise",
        description="Causes the DOF to travel <multiplier> degrees in the time a regular DOF travels 360°",
        default=False,
    )
    bpy.types.Object.dof_multiply_min_max = bpy.props.BoolProperty(
        name="Multiply Min/Max",
        description="Sets whether min/max should be affected by the multiplier",
        default=False,
        update=dof_update_input,
    )

    bpy.types.Object.dof_multiplier = bpy.props.FloatProperty(
        name="Multiplier",
        description="Multiplier",
        default=1,
        min=0.001,
        max=100,
        update=dof_update_input,
    )


register_blender_properties()

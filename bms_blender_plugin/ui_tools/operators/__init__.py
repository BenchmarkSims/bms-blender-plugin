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
from bms_blender_plugin.common.util import get_switches, get_dofs, get_bml_type
from bms_blender_plugin.common.constants import (
    BMS_MAX_SWITCH_NUMBER,
    BMS_MAX_SWITCH_BRANCH,
    BMS_MAX_DOF_NUMBER,
)


def _update_switch_list_index(obj, context):
    """Whenever the list index changes, force persistent switch number/branch to match the selected XML entry."""
    try:
        switches = get_switches()
        if 0 <= obj.switch_list_index < len(switches):
            sw = switches[obj.switch_list_index]
            obj.bml_switch_number = sw.switch_number
            obj.bml_switch_branch = sw.branch
            try:
                print(f"[DEBUG] _update_switch_list_index: obj={getattr(obj,'name',None)} index={obj.switch_list_index} -> {sw.switch_number}:{sw.branch}")
            except Exception:
                pass
        else:
            try:
                print(f"[DEBUG] _update_switch_list_index: obj={getattr(obj,'name',None)} index={getattr(obj,'switch_list_index',None)} out_of_range (len={len(switches)})")
            except Exception:
                pass
    except Exception:
        pass
    update_switch_or_dof_name(obj, context)


def _update_dof_list_index(obj, context):
    """Whenever the list index changes, force persistent DOF number to match the selected XML entry."""
    try:
        dofs = get_dofs()
        if 0 <= obj.dof_list_index < len(dofs):
            de = dofs[obj.dof_list_index]
            obj.bml_dof_number = de.dof_number
    except Exception:
        pass
    update_switch_or_dof_name(obj, context)



# Keep legacy list index in sync when persistent switch IDs are edited manually
def _update_persistent_switch_ids(obj, context):
    """When user edits persistent switch number/branch, update switch_list_index to matching XML entry if found.
    If both IDs are -1 (not set), leave index unchanged for backward compatibility.
    """
    update_switch_or_dof_name(obj, context)
    def _tag_redraw(ctx):
        try:
            if ctx and ctx.screen:
                for area in ctx.screen.areas:
                    area.tag_redraw()
        except Exception:
            pass

    try:
        sw_num = getattr(obj, "bml_switch_number", -1)
        sw_branch = getattr(obj, "bml_switch_branch", -1)
        if sw_num >= 0 and sw_branch >= 0:
            scene_list = getattr(bpy.context.scene, 'switch_list', None)
            found_index = None
            if scene_list:
                for i, item in enumerate(scene_list):
                    if item.switch_number == sw_num and item.branch_number == sw_branch:
                        found_index = i
                        break
            if found_index is None:
                switches = get_switches()
                for i, sw in enumerate(switches):
                    if sw.switch_number == sw_num and sw.branch == sw_branch:
                        found_index = i
                        break
            if found_index is not None and getattr(obj, 'switch_list_index', -1) != found_index:
                obj.switch_list_index = found_index
                _tag_redraw(context)
        # If unset leave legacy index
    except Exception:
        pass

# Keep legacy list index in sync when persistent DOF ID is edited manually
def _update_persistent_dof_number(obj, context):
    """When user edits persistent DOF number, update dof_list_index to matching XML entry if found.
    If ID is -1 (not set), leave index unchanged.
    """
    update_switch_or_dof_name(obj, context)
    def _tag_redraw(ctx):
        try:
            if ctx and ctx.screen:
                for area in ctx.screen.areas:
                    area.tag_redraw()
        except Exception:
            pass

    try:
        dof_num = getattr(obj, "bml_dof_number", -1)
        if dof_num >= 0:
            scene_list = getattr(bpy.context.scene, 'dof_list', None)
            found_index = None
            if scene_list:
                for i, item in enumerate(scene_list):
                    if item.dof_number == dof_num:
                        found_index = i
                        break
            if found_index is None:
                dofs = get_dofs()
                for i, de in enumerate(dofs):
                    if de.dof_number == dof_num:
                        found_index = i
                        break
            if found_index is not None and getattr(obj, 'dof_list_index', -1) != found_index:
                obj.dof_list_index = found_index
                _tag_redraw(context)
        # Unset -> leave legacy index
    except Exception:
        pass


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
        name="Index for switch_list", default=0, update=_update_switch_list_index
    )
    bpy.types.Object.switch_default_on = bpy.props.BoolProperty(
        name="Default ON", description="The switch is ON by default", default=False
    )
    # Persistent switch number & branch (new). -1 => unset (legacy scenes)
    bpy.types.Object.bml_switch_number = bpy.props.IntProperty(
        name="Switch #",
        description="Persistent switch number used for export (independent of switch.xml ordering)",
        default=-1,
        min=-1,
        max=BMS_MAX_SWITCH_NUMBER,
        update=_update_persistent_switch_ids,
    )
    bpy.types.Object.bml_switch_branch = bpy.props.IntProperty(
        name="Branch #",
        description="Persistent branch number used for export (independent of switch.xml ordering)",
        default=-1,
        min=-1,
        max=BMS_MAX_SWITCH_BRANCH,
        update=_update_persistent_switch_ids,
    )

    # DOFs
    bpy.types.Object.dof_list_index = bpy.props.IntProperty(
        name="Index for dof_list", default=0, update=_update_dof_list_index
    )

    # Persistent DOF number (new)
    bpy.types.Object.bml_dof_number = bpy.props.IntProperty(
        name="DOF #",
        description="Persistent DOF number used for export (independent of DOF.xml ordering)",
        default=-1,
        min=-1,
        max=BMS_MAX_DOF_NUMBER,
        update=_update_persistent_dof_number,
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

    # Silent legacy migration disabled: manual validation-driven assignment required.
    try:
        for obj in bpy.data.objects:
            update_switch_or_dof_name(obj, None)
    except Exception:
        pass


class BML_OT_reconcile_dof_switch_indices(bpy.types.Operator):
    bl_idname = "bml.reconcile_dof_switch_indices"
    bl_label = "Reconcile DOF/Switch Indices"
    bl_description = "Synchronize xml list indices with current persistent IDs. Persistent ID -> List Index. (Prioritize scene cached list.)"
    bl_options = {"UNDO"}

    def execute(self, context):
        count = 0
        for obj in bpy.data.objects:
            t = get_bml_type(obj)
            if t == BlenderNodeType.SWITCH:
                _update_persistent_switch_ids(obj, context)
                count += 1
            elif t == BlenderNodeType.DOF:
                _update_persistent_dof_number(obj, context)
                count += 1
        self.report({'INFO'}, f"Reconciled indices for {count} DOF/Switch objects")
        return {'FINISHED'}


register_blender_properties()

# Explicit registration for reconciliation operator (others auto-executed above)
try:
    bpy.utils.register_class(BML_OT_reconcile_dof_switch_indices)
except Exception:
    pass

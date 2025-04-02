import bpy
from bpy.app.handlers import persistent

import math

from mathutils import Matrix, Vector

from bms_blender_plugin import nodes_editor
from bms_blender_plugin.common.bml_structs import (
    DofType,
)
from bms_blender_plugin.common.blender_types import (
    BlenderNodeType,
    BlenderEditorNodeType, BlenderNodeTreeType,
)
from bms_blender_plugin.common.util import (
    get_bml_type,
    get_switches,
    get_dofs,
    reset_dof,
    get_parent_dof_or_switch,
)
from bms_blender_plugin.nodes_editor.util import get_bml_node_type, get_bml_node_tree_type


class DofMediator:
    """Mediator which makes sure that all DOF objects with the same dof_number receive the identical dof_input when they
    are updated individually"""

    dof_number_dofs = dict()
    dof_dof_number = dict()

    @classmethod
    def is_cache_empty(cls):
        return len(cls.dof_dof_number) == 0

    @classmethod
    def rebuild_cache(cls):
        """Builds a local cache of all DOFs by parsing the whole object tree"""
        print("rebuilding cache")
        cls.dof_number_dofs.clear()
        cls.dof_dof_number.clear()

        for obj in bpy.data.objects:
            if get_bml_type(obj) == BlenderNodeType.DOF:
                cls.subscribe(obj)

    @classmethod
    def subscribe(cls, dof):
        """Subscribes a DOF to dof_input updates for his DOF number"""
        if get_bml_type(dof) != BlenderNodeType.DOF:
            return
        dof_number = get_dofs()[dof.dof_list_index].dof_number

        # first time subscription
        if dof not in cls.dof_dof_number.keys():
            cls.dof_dof_number[dof] = dof_number

            if dof_number not in cls.dof_number_dofs.keys():
                cls.dof_number_dofs[dof_number] = {dof}
            else:
                cls.dof_number_dofs[dof_number].add(dof)

        # update existing subscription
        else:
            # filter out unnecessary updates
            old_dof_number = cls.dof_dof_number[dof]
            if old_dof_number == dof_number:
                return
            else:
                # unsubscribe from the old subscriptions
                cls.dof_number_dofs[old_dof_number].remove(dof)

                if dof_number not in cls.dof_number_dofs.keys():
                    cls.dof_number_dofs[dof_number] = {dof}
                else:
                    cls.dof_number_dofs[dof_number].add(dof)

            cls.dof_dof_number[dof] = dof_number

    @classmethod
    def unsubscribe(cls, dof):
        """Unsubscribes a DOF from all subscriptions"""
        dof_number = get_dofs()[dof.dof_list_index].dof_number
        cls.dof_number_dofs[dof_number].remove(dof)
        cls.dof_dof_number.pop(dof)

    @classmethod
    def post_new_dof_value(cls, dof):
        """Notifies that a DOF has received a new dof_input value. Updates the other DOFs to the same dof_input."""
        if bpy.app.background:
            return

        if dof not in cls.dof_dof_number:
            cls.rebuild_cache()

        dof_number = get_dofs()[dof.dof_list_index].dof_number

        dofs_to_cleanup = []
        new_dof_input = dof.dof_input

        for other_dof in cls.dof_number_dofs[dof_number]:
            if (
                len(other_dof.users_collection) > 0
                and other_dof.dof_input != new_dof_input
            ):
                other_dof.dof_input = new_dof_input
            elif len(other_dof.users_collection) == 0:
                dofs_to_cleanup.append(other_dof)

        # clean up orphaned DOFs which might have accumulated
        for dof in dofs_to_cleanup:
            cls.dof_number_dofs[dof_number].remove(dof)
            cls.dof_dof_number.pop(dof)
            bpy.data.objects.remove(dof)


def update_switch_or_dof_name(obj, context):
    """Updates the name of a DOF or Switch when their respective DOF/Switch values are changed. Overwrites any previous
    name updates by the user."""
    if get_bml_type(obj) == BlenderNodeType.SWITCH:
        active_switch = get_switches()[obj.switch_list_index]
        obj.name = f"Switch - {active_switch.name} ({active_switch.switch_number})"
    elif get_bml_type(obj) == BlenderNodeType.DOF:
        active_dof = get_dofs()[obj.dof_list_index]

        name = f"DOF - {active_dof.name} ({active_dof.dof_number})"
        obj.name = name

        for tree in bpy.data.node_groups.values():
            if isinstance(tree, nodes_editor.dof_editor.DofNodeTree):
                # for all DofNodeTrees, set all parent_dofs which contain references to delete objs to None
                for node in tree.nodes:
                    if (
                        get_bml_node_type(node) == BlenderEditorNodeType.DOF_MODEL
                        and node.parent_dof == obj
                    ):
                        node.label = obj.name

        DofMediator.subscribe(obj)


def update_dof_display_type(obj, context):
    """Updates the display-type of a DOF Empty"""
    reset_dof(obj)

    if obj.dof_type == DofType.ROTATE.name:
        clear_parent_dof_rotation(obj)
        obj.empty_display_type = context.preferences.addons[
            "bms_blender_plugin"
        ].preferences.dof_rotate_empty_type
        obj.empty_display_size = context.preferences.addons[
            "bms_blender_plugin"
        ].preferences.dof_rotate_empty_size

    elif obj.dof_type == DofType.TRANSLATE.name:
        align_parent_dof_rotation(obj)
        obj.empty_display_type = context.preferences.addons[
            "bms_blender_plugin"
        ].preferences.dof_translate_empty_type
        obj.empty_display_size = context.preferences.addons[
            "bms_blender_plugin"
        ].preferences.dof_translate_empty_size

    elif obj.dof_type == DofType.SCALE.name:
        clear_parent_dof_rotation(obj)
        obj.empty_display_type = context.preferences.addons[
            "bms_blender_plugin"
        ].preferences.dof_scale_empty_type
        obj.empty_display_size = context.preferences.addons[
            "bms_blender_plugin"
        ].preferences.dof_scale_empty_size
    
    elif get_bml_type(obj) == BlenderNodeType.SWITCH:
        obj.empty_display_type = context.preferences.addons[
            "bms_blender_plugin"
        ].preferences.switch_empty_type
        obj.empty_display_size = context.preferences.addons[
            "bms_blender_plugin"
        ].preferences.switch_empty_size


def dof_set_input(obj, value):
    """ Custom setter/getter methods for dof_input so it can be keyframed"""
    if obj:
        obj["dof_input"] = value
        dof_update_input(obj, None)
        obj.update_tag()


def dof_get_input(obj):
    if "dof_input" not in obj.keys():
        obj.dof_input = 0
    return obj["dof_input"]


def dof_update_input(obj, context):
    """Main method to preview how a DOF will behave in BMS. Generally, it will update the DOFs delta values so that
    we can reset those safely and not touch its original coords.
    It is also important to only apply the new dof input if it has not been applied to the object as this method will
    be called multiple times when DOFs update each other."""

    if get_bml_type(obj) != BlenderNodeType.DOF:
        # this might be the case if the object was purged
        return

    obj.rotation_mode = "XYZ"

    sign = 1
    if obj.dof_reverse:
        sign = -1

    dof_input = obj.dof_input * obj.dof_multiplier * sign

    # rotation
    if obj.dof_type == DofType.ROTATE.name:
        dof_min = obj.dof_min
        dof_max = obj.dof_max
        if obj.dof_multiply_min_max:
            dof_min *= obj.dof_multiplier
            dof_max *= obj.dof_multiplier

        dof_min = math.radians(dof_min)
        dof_max = math.radians(dof_max)

        if obj.dof_check_limits:
            if dof_input < dof_min:
                dof_input = dof_min
            elif dof_input > dof_max:
                dof_input = dof_max

        if obj.dof_normalise:
            if dof_max == dof_min:
                dof_input = 0
            else:
                result = dof_input - dof_min
                result = result / (dof_max - dof_min)
                if result < 0:
                    result = 0
                elif result > 1:
                    result = 1
                dof_input = result

        obj.rotation_mode = "XYZ"
        rot_delta = (
            Matrix.Rotation(dof_input, 3, "Y")
            @ obj.rotation_euler.to_matrix().inverted()
        )

        new_obj_rotation = (obj.rotation_euler.to_matrix() @ rot_delta).to_euler()

        if obj.delta_rotation_euler != new_obj_rotation:
            obj.delta_rotation_euler = new_obj_rotation

    else:
        dof_min = obj.dof_min_input
        dof_max = obj.dof_max_input
        if obj.dof_multiply_min_max:
            dof_min *= obj.dof_multiplier
            dof_max *= obj.dof_multiplier

        if obj.dof_check_limits:
            if dof_input < dof_min:
                dof_input = dof_min
            elif dof_input > dof_max:
                dof_input = dof_max

        if obj.dof_normalise:
            if dof_max == dof_min:
                dof_input = 0
            else:
                result = dof_input - dof_min
                result = result / (dof_max - dof_min)
                if result < 0:
                    result = 0
                elif result > 1:
                    result = 1
                dof_input = result

        # translation
        if obj.dof_type == DofType.TRANSLATE.name:
            # BMS quirk: translations always rotate to their parent DOF rotations
            align_parent_dof_rotation(obj)
            translation = Vector((obj.dof_x, obj.dof_y, obj.dof_z))

            new_location_x = dof_input * translation.x
            new_location_y = dof_input * translation.y
            new_location_z = dof_input * translation.z

            if obj.delta_location.x != new_location_x:
                obj.delta_location.x = new_location_x

            if obj.delta_location.y != new_location_y:
                obj.delta_location.y = new_location_y

            if obj.delta_location.z != new_location_z:
                obj.delta_location.z = new_location_z

        # scale
        if obj.dof_type == DofType.SCALE.name:
            new_scale_x = 1 + (dof_input * (obj.dof_x - 1))
            new_scale_y = 1 + (dof_input * (obj.dof_y - 1))
            new_scale_z = 1 + (dof_input * (obj.dof_z - 1))

            if obj.delta_scale.x != new_scale_x:
                obj.delta_scale.x = new_scale_x

            if obj.delta_scale.y != new_scale_y:
                obj.delta_scale.y = new_scale_y

            if obj.delta_scale.z != new_scale_z:
                obj.delta_scale.z = new_scale_z

    DofMediator.post_new_dof_value(obj)


def dof_trigger_redraw(obj, context):
    """Forces a redraw of a DOF by setting its world matrix"""
    matrix_world = obj.matrix_world
    obj.matrix_world = matrix_world


def is_dof_input_within_limits(obj, context):
    """Checks if a DOF is within its input limits"""
    if not obj.dof_check_limits:
        return True

    else:
        multiplier = obj.dof_multiplier
        sign = 1
        if obj.dof_reverse:
            sign = -1
        dof_input = obj.dof_input * multiplier * sign
        if not obj.dof_multiply_min_max:
            multiplier = 1

        if obj.dof_type == DofType.ROTATE.name:
            dof_min = math.radians(obj.dof_min * multiplier)
            dof_max = math.radians(obj.dof_max * multiplier)
        else:
            dof_min = obj.dof_min_input
            dof_max = obj.dof_max_input
        if dof_input < dof_min or dof_input > dof_max:
            return False
        else:
            return True


def dof_reverse(obj, context):
    """Reverses a DOF by switching its minimum and maximum"""
    old_min = obj.dof_min * -1
    old_max = obj.dof_max * -1
    obj.dof_min = old_max
    obj.dof_max = old_min

    dof_update_input(obj, context)


def align_parent_dof_rotation(obj):
    """Forces a child to align to its parent DOF rotation by adding a COPY ROTATION constraint.
    This is only needed for translation DOFs which are children of rotate DOFs - in BMS, they will always move according
    to their parent's rotation."""
    if obj and obj.parent:
        parent_dof = get_parent_dof_or_switch(obj.parent)
        if (
            get_bml_type(parent_dof) == BlenderNodeType.DOF
            and parent_dof.dof_type == DofType.ROTATE.name
        ):
            if "DOF_Copy_Rotation" not in obj.constraints:
                constraint = obj.constraints.new("COPY_ROTATION")
                constraint.target = parent_dof
                constraint.name = "DOF_Copy_Rotation"
            else:
                obj.constraints["DOF_Copy_Rotation"].target = parent_dof

        return parent_dof


def clear_parent_dof_rotation(obj):
    """Removes a COPY ROTATION constraint which was added with align_parent_dof_rotation()"""
    if obj and "DOF_Copy_Rotation" in obj.constraints:
        constraint = obj.constraints["DOF_Copy_Rotation"]
        obj.constraints.remove(constraint)


def update_post(scene, depsgraph):
    """Called on every Depsgraph update. Use this to make sure that newly created DOFs are subscribed to updates from
    the DofMediator"""
    for update_obj in depsgraph.updates:
        # if a DOF is updated...
        if (
            isinstance(update_obj.id, bpy.types.Object)
            and get_bml_type(obj := bpy.data.objects[update_obj.id.name])
            == BlenderNodeType.DOF
        ):

            # DOF is either moved normally or newly created
            if update_obj.is_updated_geometry:
                if obj not in DofMediator.dof_dof_number:
                    DofMediator.subscribe(bpy.data.objects[update_obj.id.name])

            # Only the parent DOF object was manipulated (e.g. rotated) - snap back all DOFs with this number
            elif not update_obj.is_updated_geometry and update_obj.is_updated_transform and obj.dof_input != 0:
                obj.dof_input = 0
                DofMediator.post_new_dof_value(obj)


def frame_change_post(scene):
    for dof in DofMediator.dof_dof_number.keys():
        dof.update_tag()

    for tree in bpy.data.node_groups.values():
        if get_bml_node_tree_type(tree) == BlenderNodeTreeType.DOF_TREE:
            tree.execute(None)


def register_update_callback():
    if update_post not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(update_post)

    if load_handler not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load_handler)

    if frame_change_post not in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.append(frame_change_post)



@persistent
def load_handler(dummy):
    register_update_callback()
    DofMediator.rebuild_cache()


def register():
    if not bpy.app.background:
        if load_handler not in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.append(load_handler)

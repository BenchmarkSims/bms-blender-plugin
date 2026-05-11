import operator
import os

from bms_blender_plugin.common.blender_types import BlenderNodeType
from bms_blender_plugin.common.util import (
    get_bml_type,
    get_switches,
    get_dofs,
    get_bounding_sphere,
)
from bms_blender_plugin.common.resolve_ids import resolve_dof_number, resolve_switch_id
from bms_blender_plugin.common.constants import (
    BMS_MAX_SWITCH_NUMBER,
    BMS_MAX_DOF_NUMBER,
)
from bms_blender_plugin.common.coordinates import to_bms_coords


def get_highest_switch_and_dof_number(objs):
    """Returns the highest values of dofs and switches. Required for the Parent.dat"""
    # default value 0 to prevent editor crashing
    highest_switch_number = 0
    highest_dof_number = 0

    for obj in objs:
        if len(obj.children) > 0:
            if get_bml_type(obj) == BlenderNodeType.SWITCH:
                try:
                    switch_number, _branch = resolve_switch_id(obj)
                except Exception:
                    switch_number = None
                if switch_number is None:
                    # legacy fallback
                    try:
                        sw = get_switches()[obj.switch_list_index]
                        switch_number = sw.switch_number
                    except Exception:
                        switch_number = 0
                required_switch_index = switch_number + 1  # parent.dat off-by-one requirement
                if required_switch_index > highest_switch_number:
                    highest_switch_number = required_switch_index
            elif get_bml_type(obj) == BlenderNodeType.DOF:
                try:
                    dof_number = resolve_dof_number(obj)
                except Exception:
                    dof_number = None
                if dof_number is None:
                    try:
                        dof_enum = get_dofs()[obj.dof_list_index]
                        dof_number = dof_enum.dof_number
                    except Exception:
                        dof_number = 0
                required_dof_index = dof_number + 1
                if required_dof_index > highest_dof_number:
                    highest_dof_number = required_dof_index

    # Cap values at BMS maximum
    highest_switch_number = min(highest_switch_number, BMS_MAX_SWITCH_NUMBER)
    highest_dof_number = min(highest_dof_number, BMS_MAX_DOF_NUMBER)

    return highest_switch_number, highest_dof_number


def get_slots(scene):
    """Returns the amount of Slots in a scene. Required for the Parent.dat"""
    if scene:
        return [
            obj for obj in scene.objects if get_bml_type(obj) == BlenderNodeType.SLOT
        ]
    else:
        return []


def export_parent_dat(
    context,
    file_directory: str,
    file_prefix: str,
    bounding_box_1_min_coords,
    bounding_box_1_max_coords,
    scale_factor,
    number_of_texture_sets,
    slot_list,
    lod_list,
):
    """Exports the Parent.dat as a file"""
    parent_dat_filepath = os.path.join(file_directory, "Parent.dat")

    # note: the "Switches" and "Dofs" config in the Parent.dat don't actually amount to the number of DOFs/switches but
    # to the highest dof_number in the model
    highest_switch_number, highest_dof_number = get_highest_switch_and_dof_number(
        context.scene.objects
    )

    bounding_sphere_center, bounding_sphere_radius = get_bounding_sphere(
        context.scene.objects
    )
    
    bounding_sphere_radius *= scale_factor

    with open(parent_dat_filepath, "w") as parent_dat_file:
        str_output = (
            f"// Dimensions = bounding_sphere_radius bbox_min_x bbox_max_x bbox_min_y bbox_max_y bbox_min_z bbox_max_z\n"
            f"Dimensions = {round(bounding_sphere_radius, 6)} "
            f"{round(bounding_box_1_min_coords.x, 6):.6f} {round(bounding_box_1_max_coords.x, 6):.6f} "
            f"{round(bounding_box_1_min_coords.y, 6):.6f} {round(bounding_box_1_max_coords.y, 6):.6f} "
            f"{round(bounding_box_1_min_coords.z, 6):.6f} {round(bounding_box_1_max_coords.z, 6):.6f}\n"
            f"TextureSets = {number_of_texture_sets}\n"
            f"Switches = {highest_switch_number}\n"
            f"Dofs = {highest_dof_number}\n"
        )

        # convert the slots to BML, sort them by Y coord and add them
        slot_bml_coords = [
            to_bms_coords(slot.matrix_world.translation) for slot in slot_list
        ]
        slot_bml_coords.sort(key=operator.attrgetter("y"))

        for slot_coord in slot_bml_coords:
            str_output += (
                f"AddSlot = {round(slot_coord.x, 6):.6f} "
                f"{round(slot_coord.y, 6):.6f} "
                f"{round(slot_coord.z, 6):.6f}\n"
            )

        # get the lod list from the scene and sort it by viewing distance
        lod_filenames_distances = []
        for lod in lod_list:
            lod_filenames_distances.append(
                (file_prefix + lod.file_suffix + ".bml", lod.viewing_distance)
            )
        lod_filenames_distances.sort(key=lambda a: a[1])

        for lod in lod_filenames_distances:
            str_output += f"AddLOD = {lod[0]} {lod[1]}\n"

        parent_dat_file.write(str_output)

    print(f"Exported Parent.dat file: {parent_dat_filepath}")

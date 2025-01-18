import operator
import os

from bms_blender_plugin.common.blender_types import BlenderNodeType
from bms_blender_plugin.common.util import (
    get_bml_type,
    get_switches,
    get_dofs,
    to_bms_coords,
    get_bounding_sphere,
)


def get_highest_switch_and_dof_number(objs):
    """Returns the highest values of dofs and switches. Required for the Parent.dat"""
    # default value 0 to prevent editor crashing
    highest_switch_number = 0
    highest_dof_number = 0

    for obj in objs:
        if len(obj.children) > 0:
            if get_bml_type(obj) == BlenderNodeType.SWITCH:
                switch = get_switches()[obj.switch_list_index]
                if switch.switch_number > highest_switch_number:
                    highest_switch_number = switch.switch_number
            elif get_bml_type(obj) == BlenderNodeType.DOF:
                dof = get_dofs()[obj.dof_list_index]
                if dof.dof_number > highest_dof_number:
                    highest_dof_number = dof.dof_number

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
    bounding_box_1_coords,
    bounding_box_2_coords,
    scale_factor,
    number_of_texture_sets,
    slot_list,
    lod_list,
):
    """Exports the Parent.dat as a file"""
    parent_dat_filepath = os.path.join(file_directory, "Parent.dat")

    bounding_box_1_coords = to_bms_coords(bounding_box_1_coords)
    bounding_box_2_coords = to_bms_coords(bounding_box_2_coords)

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
            f"Dimensions = {round(bounding_sphere_radius, 6)} "
            f"{round(bounding_box_1_coords.x, 6):.6f} {round(bounding_box_2_coords.x, 6):.6f} "
            f"{round(bounding_box_1_coords.y, 6):.6f} {round(bounding_box_2_coords.y, 6):.6f} "
            f"{round(bounding_box_1_coords.z, 6):.6f} {round(bounding_box_2_coords.z, 6):.6f}\n"
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

import datetime
import math

import bpy
from mathutils import Vector

from bms_blender_plugin.common.blender_types import BlenderNodeType, LodItem
from bms_blender_plugin.common.export_settings import ExportSettings
from bms_blender_plugin.common.util import (
    get_bml_type,
)
from bms_blender_plugin.exporter.export_hotspots import export_hotspots
from bms_blender_plugin.exporter.export_lods import (
    export_lods, )
from bms_blender_plugin.exporter.export_materials import (
    export_materials,
)
from bms_blender_plugin.exporter.export_parent_dat import get_slots, export_parent_dat


def export_bml(context, lods, file_directory, file_prefix, export_settings: ExportSettings):
    """Exports the current scene to the BML v2 files:
    * For each LOD a BML
    * A single Materials.mtl file
    * For each LOD a MTI file
    * For each Material file multiple DDS textures
    * A single Parent.dat
    * A single 3dButtons.dat
    """

    start_time = datetime.datetime.now()
    print(f"Starting BML export at {start_time}\n")

    # blender uses meters as base unit, BMS works in feet
    # note that unit system does not scale the model, it just changes the dimension units
    scale_factor = 3.28084

    # apply the scale factor as set in scene->units->unit scale
    # this factor does not scale the model, it scales the dimension units
    # to get this reflected in the model, apply this on scale factor
    scale_factor *= bpy.context.scene.unit_settings.scale_length

    print(f"unit scaling factor: {scale_factor}")

    bounding_box_1_coords = Vector((0, 0, 0))
    bounding_box_2_coords = Vector((0, 0, 0))

    # try to find the bounding box - we take the first one we get
    for obj in context.scene.objects:
        if get_bml_type(obj) == BlenderNodeType.BBOX:
            max_x, min_x, max_y, min_y, max_z, min_z = (0,)*6
            # find the min and max coordinates of the 8 vertices
            for corner in obj.data.vertices:
                max_x = max(corner.co.x, max_x)
                min_x = min(corner.co.x, min_x)
                max_y = max(corner.co.y, max_y)
                min_y = min(corner.co.y, min_y)
                max_z = max(corner.co.z, max_z)
                min_z = min(corner.co.z, min_z)

            bounding_box_1_coords = Vector((max_x, max_y, max_z))
            bounding_box_2_coords = Vector((min_x, min_y, min_z))

            bounding_box_1_coords *= scale_factor
            bounding_box_2_coords *= scale_factor
            break

    # we have to call export_lods even if we don't want to export models
    # because it will return materials and hotspots
    if len(lods) == 0 and bpy.context.collection:
        lods = [LodItem("", 0, bpy.context.collection)]

    elif len(lods) == 0:
        raise Exception("No active collection and no LODs - can not export")

    all_exported_bmls, all_material_names, all_hotspots = export_lods(
        context, file_directory, file_prefix, lods, scale_factor, export_settings
    )

    if export_settings.export_materials_file or export_settings.export_textures:
        export_materials(
            all_material_names,
            file_directory,
            export_settings,
        )

    if export_settings.export_materials_sets and len(context.scene.bml_material_sets) > 1:
        number_of_texture_sets = len(context.scene.bml_material_sets)
    else:
        number_of_texture_sets = 1

    if export_settings.export_parent_dat:
        export_parent_dat(
            context,
            file_directory,
            file_prefix,
            bounding_box_1_coords,
            bounding_box_2_coords,
            scale_factor,
            number_of_texture_sets,
            get_slots(context.scene),
            lods
        )

    if export_settings.export_hotspots:
        export_hotspots(all_hotspots, file_directory)

    elapsed = datetime.datetime.now() - start_time
    elapsed_minutes = divmod(elapsed.total_seconds(), 60)

    success_message = (
        f"BML export finished in "
        f"{math.trunc(elapsed_minutes[0])}m {round(elapsed_minutes[1],2)}s"
    )

    print(success_message)
    return success_message, all_exported_bmls

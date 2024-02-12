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

    # determine whether the current scene is set to imperial units, otherwise we have to scale our objects
    scale_factor = 1

    if bpy.context.scene.unit_settings.system == "METRIC":
        if bpy.context.scene.unit_settings.length_unit == "METERS":
            scale_factor = 3.28084
        elif bpy.context.scene.unit_settings.length_unit == "CENTIMETERS":
            scale_factor = 3.28084 * 100
        elif bpy.context.scene.unit_settings.length_unit == "MILLIMETERS":
            scale_factor = 3.28084 * 1000
    elif bpy.context.scene.unit_settings.length_unit == "INCHES":
        scale_factor = 0.0833333

    print(f"unit scaling factor: {scale_factor}")

    bounding_box_1_coords = Vector((0, 0, 0))
    bounding_box_2_coords = Vector((0, 0, 0))

    # try to find the bounding box - we take the first one we get
    for obj in context.scene.objects:
        if get_bml_type(obj) == BlenderNodeType.BBOX:
            bounding_box_1_coords = obj.matrix_world @ obj.data.vertices[0].co
            bounding_box_2_coords = obj.matrix_world @ obj.data.vertices[5].co

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

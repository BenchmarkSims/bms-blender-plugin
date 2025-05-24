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
from bms_blender_plugin.common.bounding_box import BoundingBox
from bms_blender_plugin.exporter.export_lods import (
    export_lods, )
from bms_blender_plugin.exporter.export_materials import (
    export_materials,
)
from bms_blender_plugin.exporter.export_parent_dat import get_slots, export_parent_dat
from bms_blender_plugin.exporter.export_bounding_boxes import export_bounding_boxes


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

    """
    Bounding Box handling.
    A complex model can have more than one bounding box, for example an Aircraft Model usually has fuselage, 
    wing, rudder and radar hitboxes defined by separate bounding boxes. 
    As far as I know we don't care about identifying each particular bounding box with an identity key.
    Here we will iterate over all bounding boxes and construct the min and max vertex positions
    We will then take the first BBox and extract it's coordinates for the Parent.dat file.
    The remaining hitboxes can be exported to a separate file, but we need to do further work to integrate these into the
    AC.txtpb files.
    """

    # Gather all bounding boxes into an array of bounding_box objects.
    BBox_Array = [BoundingBox(obj) for obj in context.scene.objects if get_bml_type(obj) == BlenderNodeType.BBOX]
    """
    Get the first bounding box min and max coordinates. A bit arbitrary at this point, 
    but in instances of a single bbox, no harm and I suspect that these will be in named order. 
    Scale appropriately
    """
    bounding_box_1_min_coords = BBox_Array[0].min_bms_vertex
    bounding_box_1_max_coords = BBox_Array[0].max_bms_vertex
    bounding_box_1_min_coords *= scale_factor
    bounding_box_1_max_coords *= scale_factor

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
            bounding_box_1_min_coords,
            bounding_box_1_max_coords,
            scale_factor,
            number_of_texture_sets,
            get_slots(context.scene),
            lods
        )

    if export_settings.export_hotspots:
        export_hotspots(all_hotspots, file_directory)

    # If there is more than one bounding box defined, output all to a file.
    if len(BBox_Array) > 1:
        export_bounding_boxes(BBox_Array, file_directory)


    elapsed = datetime.datetime.now() - start_time
    elapsed_minutes = divmod(elapsed.total_seconds(), 60)

    success_message = (
        f"BML export finished in "
        f"{math.trunc(elapsed_minutes[0])}m {round(elapsed_minutes[1],2)}s"
    )


    print(success_message)
    return success_message, all_exported_bmls

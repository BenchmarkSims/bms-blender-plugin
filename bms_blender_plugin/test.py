import bpy

import bms_blender_plugin
from bms_blender_plugin.common.bml_structs import Compression
from bms_blender_plugin.common.export_settings import ExportSettings
from bms_blender_plugin.exporter.bml_output import export_bml

"""This file is used for internal testing and to demonstrate how the plugin could be used headless (e.g. in a CI).
As a precondition, the Blender Python modules must be installed and importable by the Python runtime - 
see https://wiki.blender.org/wiki/Building_Blender/Other/BlenderAsPyModule
"""

# Before the plugin can be run, it needs to be registered
bms_blender_plugin.register()

# Opening a .blend file. If this is not used, the default .blend fil will be processed
bpy.ops.wm.open_mainfile(filepath="/home/richard/tmp/material_alternatives_test.blend")

# Set the export settings as desired
export_settings = ExportSettings(export_textures=False, export_parent_dat=True, compression=Compression.NONE)

# Export the BML
export_bml(bpy.context, bpy.context.scene.lod_list, "/home/richard/tmp", "material_alternatives_test", export_settings)


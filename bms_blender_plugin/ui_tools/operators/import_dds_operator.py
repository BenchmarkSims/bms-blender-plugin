import os

import bpy
from bpy.props import StringProperty, CollectionProperty
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper

from bms_blender_plugin.common.import_dds import load_dds


def import_dds_file(context, filepath):
    print("Importing:", filepath)
    load_dds(filepath)
    print(f"Imported DDS from {filepath}")

    return {'FINISHED'}


class ImportDdsOperator(Operator, ImportHelper):
    """Imports DDS files as textures for materials."""
    bl_idname = "bml.import_dds"
    bl_label = "DDS Texture Files (.dds)"

    # ImportHelper mixin class uses this
    filename_ext = ".dds"

    filter_glob: StringProperty(
        default="*.dds",
        options={'HIDDEN'},
        maxlen=1024,
    )

    files: CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'},
    )

    directory: StringProperty(
        subtype='DIR_PATH',
    )

    def execute(self, context):
        for current_file in self.files:
            filepath = os.path.join(self.directory, current_file.name)
            import_dds_file(context, filepath)
        return {'FINISHED'}


def menu_func_import(self, context):
    self.layout.operator(ImportDdsOperator.bl_idname, text="DDS Texture Files (.dds)")



def register():
    bpy.utils.register_class(ImportDdsOperator)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportDdsOperator)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

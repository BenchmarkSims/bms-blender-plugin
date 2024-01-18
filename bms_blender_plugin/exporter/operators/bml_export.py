import os.path
import subprocess
import traceback

import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
    EnumProperty,
    IntProperty,
)
from bpy_extras.io_utils import ExportHelper
from bpy_types import Operator, PropertyGroup

from bms_blender_plugin.common.blender_types import LodItem
from bms_blender_plugin.common.bml_structs import Compression
from bms_blender_plugin.common.export_settings import ExportSettings
from bms_blender_plugin.common.util import get_scripts
from bms_blender_plugin.exporter import bml_output
from bms_blender_plugin.exporter.export_materials import (
    get_texture_files_to_be_exported,
)


class BlenderExportSettings(PropertyGroup):
    """Export settings data class"""
    export_models: BoolProperty(
        name="Export models (.bml)",
        description="Exports the models as BML files",
        default=True,
    )

    export_materials_file: BoolProperty(
        name="Export Materials (Materials.mtl)",
        description="Exports the materials as Materials.mtl",
        default=True,
    )

    export_materials_sets: BoolProperty(
        name="Export Material Sets (.mti)",
        description="Exports the Material Sets as MTI files",
        default=True,
    )

    export_textures: BoolProperty(
        name="Export textures (.dds)",
        description="Exports the textures as DDS files",
        default=True,
    )

    allow_slow_texture_codecs: BoolProperty(
        name="Allow slow codecs",
        description="Allow slow CPU codecs for texture exports. Warning: export can take a long time!",
        default=False,
    )

    export_parent_dat: BoolProperty(
        name="Export Parent.dat",
        description="Exports the model data in the Parent.dat",
        default=True,
    )
    export_hotspots: BoolProperty(
        name="Export hotspots (3dButtons.dat)",
        description="If your model contains hotspots, export them in the 3dButtons.dat",
        default=True,
    )

    output_compression: EnumProperty(
        name="Compression",
        description="The compression algorithm to use",
        items=(
            # (Compression.LZ_4.name, "LZ-4", "LZ-4 (medium file size / medium performance)"),
            (
                Compression.LZMA.name,
                "LZMA",
                "LZMA (smallest file size / lowest performance)",
            ),
            (Compression.NONE.name, "None", "No compression"),
        ),
        default=Compression.LZMA.name,
    )

    output_format: EnumProperty(
        name="Format",
        description="The format of the model to output",
        items=(
            ("triangle_list", "Triangle List", "Export the model as triangle list"),
        ),
        default="triangle_list",
    )

    output_type: EnumProperty(
        name="Type",
        description="The type of data to output",
        items=(
            ("bml_v2", "BML Version 2", "Output the model in BML2 format (BMS 4.38+)"),
        ),
        default="bml_v2",
    )

    auto_smooth_value: IntProperty(
        name="Auto Smooth °",
        description="When merging objects with identical materials and one of them has Auto Smooth enabled,"
                    "all objects will receive Auto Smooth with this value",
        min=0,
        max=180,
        default=30,
    )

    scripts = []
    for script in get_scripts():
        scripts.append((str(script.number), script.name, ""))

    script: EnumProperty(
        name="Script",
        description="The underlying script to use",
        items=scripts,
        default="-1",
    )

    open_editor: BoolProperty(
        name="Open in BMS Editor after export",
        description="When the export is complete, open the BML in the BMS Editor",
        default=True,
    )

    export_unused_materials: BoolProperty(
        name="Export unused materials",
        description="Export materials which are defined in the Material Node Tree but are not used in the actual model",
        default=False,
    )


class ExportBML(Operator, ExportHelper):
    """Exports the active scene to the BMLv2 format"""

    bl_idname = "export.bml"
    bl_label = "Export"

    filename_ext = ""

    filter_glob: StringProperty(
        default=".",
        options={"HIDDEN"},
        maxlen=255,
    )

    def execute(self, context):
        file_directory = os.path.dirname(self.filepath)
        file_prefix = (os.path.basename(self.filepath)).replace(" ", "_")
        blender_export_settings = context.scene.bml_export_settings

        try:
            export_settings = ExportSettings(
                export_models=blender_export_settings.export_models,
                compression=Compression[blender_export_settings.output_compression],
                auto_smooth_value=blender_export_settings.auto_smooth_value,
                script=str(blender_export_settings.script),
                export_materials_file=blender_export_settings.export_materials_file,
                export_materials_sets=blender_export_settings.export_materials_sets,
                export_unused_materials=blender_export_settings.export_unused_materials,
                export_textures=blender_export_settings.export_textures,
                allow_slow_texture_codecs=blender_export_settings.allow_slow_texture_codecs,
                export_parent_dat=blender_export_settings.export_parent_dat,
                export_hotspots=blender_export_settings.export_hotspots,
            )

            lods = []
            for lod_item in bpy.context.scene.lod_list:
                if lod_item.collection:
                    lods.append(
                        LodItem(
                            lod_item.file_suffix,
                            lod_item.viewing_distance,
                            lod_item.collection,
                        )
                    )

            success_message, bml_file_list = bml_output.export_bml(
                context, lods, file_directory, file_prefix, export_settings
            )

            self.report({"INFO"}, success_message)

        except Exception as e:
            self.report({"WARNING"}, f"An error occured during export: {e}")
            traceback.print_exc()
            return {"CANCELLED"}

        editor_path = context.preferences.addons[
            "bms_blender_plugin"
        ].preferences.editor_path
        if blender_export_settings.open_editor and editor_path and len(bml_file_list) > 0:
            subprocess.Popen([editor_path, bml_file_list[0]])

        return {"FINISHED"}

    texture_export_file_list = []

    def invoke(self, context, event):
        # this operation is a bit more expensive, so don't populate the list in draw()
        self.texture_export_file_list = get_texture_files_to_be_exported()

        # we cannot update the settings in draw() so do it here
        if len(context.scene.bml_material_sets) < 2:
            context.scene.bml_export_settings.export_materials_sets_file = False

        return super().invoke(context, event)

    def draw(self, context):
        editor_path = context.preferences.addons[
            "bms_blender_plugin"
        ].preferences.editor_path
        layout = self.layout

        export_file_list = []
        file_directory = os.path.dirname(self.filepath)
        file_prefix = (os.path.basename(self.filepath)).replace(" ", "_")
        export_settings = context.scene.bml_export_settings

        """ Not in use
        #layout.prop(operator, "output_format")
        #layout.prop(operator, "output_type")
        """

        layout.prop(export_settings, "export_models")
        if export_settings.export_models:
            box = layout.box()
            box.prop(export_settings, "output_compression")
            box.prop(export_settings, "auto_smooth_value")
            box.prop(export_settings, "script")

            row = box.row()
            row.prop(export_settings, "open_editor")

            if export_settings.open_editor and (editor_path is None or editor_path == ""):
                row.enabled = False
                box.label(
                    text="Please set the BMS Editor path in the plugin preferences",
                    icon="INFO",
                )

        layout.separator()

        row = layout.row()

        if export_settings.export_models:
            row.prop(export_settings, "export_materials_sets")
            if len(context.scene.bml_material_sets) < 2:
                row.enabled = False

        if export_settings.export_materials_file:
            export_file_list.append("Materials.mtl")

        layout.separator()

        layout.prop(export_settings, "export_materials_file")

        layout.separator()

        layout.prop(export_settings, "export_textures")
        if export_settings.export_textures:
            box = layout.box()
            box.prop(export_settings, "allow_slow_texture_codecs")
            if export_settings.allow_slow_texture_codecs:
                box.label(text="This might take very long!", icon="ERROR")

            export_file_list.extend(self.texture_export_file_list)

        layout.separator()
        layout.prop(export_settings, "export_parent_dat")
        if export_settings.export_parent_dat:
            export_file_list.append("Parent.dat")
        layout.separator()

        layout.prop(export_settings, "export_hotspots")
        if export_settings.export_hotspots:
            export_file_list.append("3dButtons.dat")
        layout.separator()

        if export_settings.export_models and len(context.scene.lod_list) == 0:
            layout.row().label(text="Export Collection")
            box = layout.box()
            box.label(text=f"{context.collection.name}")
            export_file_name = f"{file_prefix}"
            if not export_file_name.endswith(".bml"):
                export_file_name += ".bml"
            export_file_list.append(export_file_name)

            if export_settings.export_materials_sets:
                export_file_list.append(export_file_name.replace(".bml", ".mti"))

        elif export_settings.export_models:
            layout.row().label(text="Export LODs")
            box = layout.box()
            for lod_item in context.scene.lod_list:
                if not lod_item.collection:
                    continue

                lod_file_name = (
                    f"{os.path.basename(self.filepath)}{lod_item.file_suffix}.bml"
                )
                lod_file_name = lod_file_name.replace(" ", "_")
                box.label(text=f"{lod_item.collection.name}: {lod_file_name}")
                export_file_list.append(lod_file_name)

                if export_settings.export_materials_sets:
                    export_file_list.append(f"{os.path.basename(self.filepath)}{lod_item.file_suffix}.mti")

        layout.separator()

        if len(export_file_list) > 0:
            layout.row().label(text=f"Files ({len(export_file_list)})")
            box = layout.box()

            # layout.row().label(text="Files to be exported")
            # layout.row().label(text="Spaces in the filename will be replaced by '_'")

            for filename in sorted(export_file_list, key=str.casefold):
                full_filepath = os.path.join(file_directory, filename)
                if os.path.exists(full_filepath):
                    box.row().label(
                        text=f"{filename} (overwrite)", icon="ERROR"
                    )
                else:
                    box.row().label(text=f"{filename}")
        else:
            layout.row().label(text="No files will be exported", icon="ERROR")


def menu_func_export(self, context):
    self.layout.operator(ExportBML.bl_idname, text="F4-BMS (.bml)")


def register():
    bpy.utils.register_class(BlenderExportSettings)
    bpy.types.Scene.bml_export_settings = bpy.props.PointerProperty(type=BlenderExportSettings)

    bpy.utils.register_class(ExportBML)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.utils.unregister_class(ExportBML)
    bpy.utils.unregister_class(BlenderExportSettings)

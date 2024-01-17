from bms_blender_plugin.common.bml_structs import Compression


class ExportSettings:
    """Internal data class for export settings (so we don't have to use the PropertyGroup)"""
    def __init__(
        self,
        export_models: bool = True,
        compression: Compression = Compression.LZMA,
        auto_smooth_value: int = 30,
        script: str = "-1",
        export_materials_file: bool = True,
        export_materials_sets: bool = True,
        export_unused_materials: bool = True,
        export_textures: bool = True,
        allow_slow_texture_codecs: bool = False,
        export_parent_dat: bool = True,
        export_hotspots: bool = True
    ):
        self.export_models = export_models
        self.compression = compression
        self.auto_smooth_value = auto_smooth_value
        self.script = script
        self.export_materials_file = export_materials_file
        self.export_materials_sets = export_materials_sets
        self.export_unused_materials = export_unused_materials
        self.export_textures = export_textures
        self.allow_slow_texture_codecs = allow_slow_texture_codecs
        self.export_parent_dat = export_parent_dat
        self.export_hotspots = export_hotspots

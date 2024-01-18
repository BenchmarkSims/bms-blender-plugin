from os import path

import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    EnumProperty,
    PointerProperty,
)

from bms_blender_plugin.common.bml_material import (
    Cull,
    BlendLocation,
    BlendOperation,
    MaterialTemplate,
)
from bms_blender_plugin.common.blender_types import BlenderEditorNodeType
from bms_blender_plugin.nodes_editor.material_base_node import MaterialBaseNode
from bms_blender_plugin.nodes_editor.material_nodes.material_util import create_shader_nodes_for_material, \
    get_armw_texture, get_dds_texture_export_file_name, get_albedo_texture, get_normal_texture, get_emissive_texture


class MaterialNode(MaterialBaseNode):
    """Representation of a BML material in the custom BMLMaterialTree. In short this is just a class to hold some data
    which can be exported as part of the Materials.mtl"""

    bl_label = "Material"

    def init(self, context):
        self.bml_node_type = str(BlenderEditorNodeType.MATERIAL)
        self.inputs.new("NodeSocketVirtual", "Parameters")
        self.width = 400

    def draw_buttons(self, context, layout):
        row = layout.row()
        if not self.material:
            row.label(text="Material required", icon="ERROR")
        layout.prop(self, "material", text="Material")

        layout.separator()
        layout.prop(self, "templates", text="Templates")
        row = layout.row()
        row.prop(self, "template_material_name")
        row.enabled = self.templates == "Custom"

        row = layout.row()
        row.prop(self, "template_file")
        row.enabled = self.templates == "Custom"

        layout.separator()

        box = layout.box()
        if self.material:
            box.prop(self.material.node_tree.nodes["Albedo Texture"], "image", text="Albedo Texture")
        if get_albedo_texture(self.material):
            box.label(text=f"Export as:\t\t{get_dds_texture_export_file_name(get_albedo_texture(self.material))}")
        else:
            box.prop(self, "albedo_texture_file", text="File")

        box = layout.box()
        if self.material:
            box.prop(self.material.node_tree.nodes["ARMW Texture"], "image", text="ARMW Texture")
        if get_armw_texture(self.material):
            box.label(text=f"Export as:\t\t{get_dds_texture_export_file_name(get_armw_texture(self.material))}")
        else:
            box.prop(self, "armw_texture_file", text="File")

        box = layout.box()
        if self.material:
            box.prop(self.material.node_tree.nodes["Normal Texture"], "image", text="Normal Texture")
        if get_normal_texture(self.material):
            box.label(text=f"Export as:\t\t{get_dds_texture_export_file_name(get_normal_texture(self.material))}")
        else:
            box.prop(self, "normal_map_texture_file", text="File")

        box = layout.box()
        if self.material and "Emissive Texture" in self.material.node_tree.nodes.keys():
            box.prop(self.material.node_tree.nodes["Emissive Texture"], "image", text="Emissive Texture")
        if get_emissive_texture(self.material):
            box.label(text=f"Export as:\t\t{get_dds_texture_export_file_name(get_emissive_texture(self.material))}")
        else:
            box.prop(self, "emissive_texture_file", text="File")

        row = layout.row()
        row.label(text="Flags")

        layout.prop(self, "cull")
        layout.prop(self, "slope_scaled_depth_bias")
        layout.prop(self, "depth_bias")
        layout.prop(self, "shadow_caster")

        layout.row()
        layout.prop(self, "blend_enabled", text="Enable Blend")
        if self.blend_enabled:
            layout.prop(self, "blend_src")
            layout.prop(self, "blend_dest")
            layout.prop(self, "blend_op")
            layout.separator()
            layout.prop(self, "blend_alpha_src")
            layout.prop(self, "blend_alpha_dest")
            layout.prop(self, "blend_alpha_op")


def normalize_file_paths(self, context):
    # note: this will be called again when the normalization is performed so make sure you have an abort criterion
    # ugly since it checks ALL textures on any update but the alternative would be separate methods for each texture
    if path.isabs(self.albedo_texture_file):
        self.albedo_texture_file = path.basename(self.albedo_texture_file)
    if path.isabs(self.armw_texture_file):
        self.armw_texture_file = path.basename(self.armw_texture_file)
    if path.isabs(self.normal_map_texture_file):
        self.normal_map_texture_file = path.basename(self.normal_map_texture_file)
    if path.isabs(self.emissive_texture_file):
        self.emissive_texture_file = path.basename(self.emissive_texture_file)
    if path.isabs(self.template_file):
        self.template_file = path.basename(self.template_file)


def refresh_material_label(self, context):
    if self.material is None:
        label = self.bl_label
    else:
        label = self.material.name
    self.label = label
    self.name = label

    if self.material:
        create_shader_nodes_for_material(self.material)


def update_template_fields(self, context):
    if self.templates != "Custom":
        material_template = MaterialTemplate.get_templates().get(self.templates)
        self.template_material_name = material_template.template_name
        self.template_file = material_template.template_file_name


def register():
    bpy.utils.register_class(MaterialNode)


def unregister():
    bpy.utils.unregister_class(MaterialNode)


bpy.types.Node.material = PointerProperty(name="Material", type=bpy.types.Material, update=refresh_material_label)


material_templates_enum_values = []
for index, material_template in enumerate(MaterialTemplate.get_templates().values()):
    material_templates_enum_values.append(
        (
            material_template.template_name,
            material_template.template_name,
            material_template.template_name,
        )
    )
material_templates_enum_values.append(("Custom", "Custom", "Custom"))

bpy.types.Node.templates = EnumProperty(
    name="Template",
    description="Built-In Templates",
    items=material_templates_enum_values,
    update=update_template_fields,
)

bpy.types.Node.template_file = StringProperty(
    name="File",
    description="File",
    default="BML",
    subtype="FILE_PATH",
    update=normalize_file_paths,
)

bpy.types.Node.template_material_name = StringProperty(
    default="BML-Default", name="Material"
)

bpy.types.Node.albedo_texture_file = StringProperty(
    name="Albedo Texture",
    description="Albedo Texture",
    default="",
    subtype="FILE_PATH",
    update=normalize_file_paths,
)

bpy.types.Node.armw_texture_file = StringProperty(
    name="ARMW Texture",
    description="Ambient, Roughness, Smooth, Metal, Wetness",
    default="",
    subtype="FILE_PATH",
    update=normalize_file_paths,
)

bpy.types.Node.normal_map_texture_file = StringProperty(
    name="Normal Texture",
    description="Normal Map",
    default="",
    subtype="FILE_PATH",
    update=normalize_file_paths,
)

bpy.types.Node.emissive_texture_file = StringProperty(
    name="Emissive Texture",
    description="Emissive",
    default="",
    subtype="FILE_PATH",
    update=normalize_file_paths,
)

bpy.types.Node.cull = EnumProperty(
    name="Cull",
    description="The way the model is culled",
    items=(
        (Cull.FRONT.name, "Front Face", "Front Face"),
        (Cull.BACK.name, "Back Face", "Back Face"),
        (Cull.NONE.name, "None", "No Cull"),
    ),
    default=Cull.BACK.name,
)

bpy.types.Node.depth_bias = IntProperty(default=0, name="Depth Bias")
bpy.types.Node.slope_scaled_depth_bias = IntProperty(
    default=0, name="Slope Scaled Depth Bias"
)
bpy.types.Node.shadow_caster = IntProperty(default=0, name="Shadow Caster")

bpy.types.Node.blend_enabled = BoolProperty(default=False)

blend_location_enum_items = [
    (BlendLocation.ZERO.name, "ZERO", "ZERO"),
    (BlendLocation.ONE.name, "ONE", "ONE"),
    (BlendLocation.SRC_COLOR.name, "SRC_COLOR", "SRC_COLOR"),
    (BlendLocation.INV_SRC_COLOR.name, "INV_SRC_COLOR", "INV_SRC_COLOR"),
    (BlendLocation.SRC_ALPHA.name, "SRC_ALPHA", "SRC_ALPHA"),
    (BlendLocation.INV_SRC_ALPHA.name, "INV_SRC_ALPHA", "INV_SRC_ALPHA"),
    (BlendLocation.DEST_ALPHA.name, "DEST_ALPHA", "DEST_ALPHA"),
    (BlendLocation.INV_DEST_ALPHA.name, "INV_DEST_ALPHA", "INV_DEST_ALPHA"),
    (BlendLocation.DEST_COLOR.name, "DEST_COLOR", "DEST_COLOR"),
    (BlendLocation.INV_DEST_COLOR.name, "INV_DEST_COLOR", "INV_DEST_COLOR"),
    (BlendLocation.SRC_ALPHA_SAT.name, "SRC_ALPHA_SAT", "SRC_ALPHA_SAT"),
    (BlendLocation.BLEND_FACTOR.name, "BLEND_FACTOR", "BLEND_FACTOR"),
    (BlendLocation.INV_BLEND_FACTOR.name, "INV_BLEND_FACTOR", "INV_BLEND_FACTOR"),
    (BlendLocation.SRC1_COLOR.name, "SRC1_COLOR", "SRC1_COLOR"),
    (BlendLocation.INV_SRC1_COLOR.name, "INV_SRC1_COLOR", "INV_SRC1_COLOR"),
    (BlendLocation.SRC1_ALPHA.name, "SRC1_ALPHA", "SRC1_ALPHA"),
    (BlendLocation.INV_SRC1_ALPHA.name, "INV_SRC1_ALPHA", "INV_SRC1_ALPHA"),
]

blend_operation_enum_items = [
    (BlendOperation.ADD.name, "ADD", "ADD"),
    (BlendOperation.SUBTRACT.name, "SUBTRACT", "SUBTRACT"),
    (BlendOperation.REVSUBTRACT.name, "REVSUBTRACT", "REVSUBTRACT"),
    (BlendOperation.MIN.name, "MIN", "MIN"),
    (BlendOperation.MAX.name, "MAX", "MAX"),
]

bpy.types.Node.blend_src = EnumProperty(
    name="Source",
    description="Source",
    items=blend_location_enum_items,
    default=BlendLocation.ONE.name,
)

bpy.types.Node.blend_dest = EnumProperty(
    name="Destination",
    description="Destination",
    items=blend_location_enum_items,
    default=BlendLocation.ONE.name,
)

bpy.types.Node.blend_op = EnumProperty(
    name="Operation",
    description="Operation",
    items=blend_operation_enum_items,
    default=BlendOperation.ADD.name,
)

bpy.types.Node.blend_alpha_src = EnumProperty(
    name="Alpha Source",
    description="Alpha Source",
    items=blend_location_enum_items,
    default=BlendLocation.ONE.name,
)

bpy.types.Node.blend_alpha_dest = EnumProperty(
    name="Alpha Destination",
    description="Alpha Destination",
    items=blend_location_enum_items,
    default=BlendLocation.ONE.name,
)

bpy.types.Node.blend_alpha_op = EnumProperty(
    name="Alpha Operation",
    description="Alpha Operation",
    items=blend_operation_enum_items,
    default=BlendOperation.ADD.name,
)

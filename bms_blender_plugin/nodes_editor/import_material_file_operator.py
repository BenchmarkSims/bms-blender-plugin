import json
import os.path
from json import JSONDecodeError

import bpy
from bpy.props import StringProperty, BoolProperty
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper

from bms_blender_plugin.common.bml_material import (
    Slot,
    ShaderUnit,
    BlendLocation,
    BlendOperation,
    MaterialTemplate,
)
from bms_blender_plugin.common.import_dds import load_dds
from bms_blender_plugin.ext.blender_dds_addon.directx.texconv import unload_texconv
from bms_blender_plugin.nodes_editor import MaterialNode, SamplerNode, ShaderNode
from bms_blender_plugin.nodes_editor.material_editor import MaterialNodeTree
from bms_blender_plugin.nodes_editor.material_nodes.material_util import create_shader_nodes_for_material, \
    set_albedo_texture, set_armw_texture, set_normal_texture, set_emissive_texture
from bms_blender_plugin.nodes_editor.util import (
    find_material_node_by_material,
    get_farthest_x_location,
)


class ImportMaterialFileOperator(Operator, ImportHelper):
    """Imports a BMS Material file"""

    bl_idname = "bml.import_material_file"
    bl_label = "BMS Material File (.mtl)"
    filename_ext = ".mtl"

    filter_glob: StringProperty(
        default="*.mtl",
        options={"HIDDEN"},
        maxlen=512,
    )

    import_textures: BoolProperty(
        name="Import DDS Textures",
        description="When a texture is found in the same directory as the .mtl, import it into Blender",
        default=True,
    )

    def execute(self, context):
        try:
            material_file = open(self.filepath, "r")
            json_data = json.loads(material_file.read())

            materials = json_data["Materials"]
            material_file.close()
        except JSONDecodeError as error:
            raise Exception(f"{self.filepath} contains malformed JSON: {error}")

        # make sure that we have a material tree
        if MaterialNodeTree.bl_label in bpy.data.node_groups.keys():
            material_node_tree = bpy.data.node_groups[MaterialNodeTree.bl_label]
        else:
            material_node_tree = bpy.data.node_groups.new(
                MaterialNodeTree.bl_label, MaterialNodeTree.__name__
            )

        last_location_x = get_farthest_x_location(material_node_tree)
        for material in materials:
            # create the material if we don't have it already
            scene_material = bpy.data.materials.get(material["Name"])
            if not scene_material:
                # create material
                scene_material = bpy.data.materials.new(name=material["Name"])

            # create a node for it if we don't have it already
            material_node = find_material_node_by_material(
                material_node_tree, scene_material
            )

            if not material_node:
                material_node = material_node_tree.nodes.new(MaterialNode.__name__)
                material_node.material = scene_material

                # create the shading node tree
                create_shader_nodes_for_material(scene_material)

                # layouting stuff
                last_location_x += 50 + material_node.width
                material_node.location.x = last_location_x

                # Template
                if "Template" in material:
                    templates = MaterialTemplate.get_templates()
                    imported_template_material = material["Template"]["Material"]
                    imported_template_file = material["Template"]["File"]

                    if (
                        imported_template_material in templates
                        and templates.get(imported_template_material).template_file_name
                        == imported_template_file
                    ):
                        material_node.templates = imported_template_material
                    else:
                        material_node.templates = "Custom"
                        material_node.template_file = imported_template_file
                        material_node.template_material_name = (
                            imported_template_material
                        )

                # Textures
                if "Textures" in material.keys():
                    for texture in material["Textures"]:
                        if texture["Slot"] == Slot.ALBEDO:
                            filename = os.path.join(os.path.dirname(self.filepath), texture["File"])
                            if self.import_textures and os.path.exists(filename):
                                dds_texture = load_dds(filename)
                                set_albedo_texture(scene_material, dds_texture)
                            else:
                                material_node.albedo_texture_file = texture["File"]

                        elif texture["Slot"] == Slot.ARMW:
                            filename = os.path.join(os.path.dirname(self.filepath), texture["File"])
                            if self.import_textures and os.path.exists(filename):
                                dds_texture = load_dds(filename)
                                set_armw_texture(scene_material, dds_texture)
                            else:
                                material_node.armw_texture_file = texture["File"]

                        elif texture["Slot"] == Slot.NORMAL_MAP:
                            filename = os.path.join(os.path.dirname(self.filepath), texture["File"])
                            if self.import_textures and os.path.exists(filename):
                                dds_texture = load_dds(filename)
                                set_normal_texture(scene_material, dds_texture)
                            else:
                                material_node.normal_map_texture_file = texture["File"]

                        elif texture["Slot"] == Slot.EMISSIVE:
                            filename = os.path.join(os.path.dirname(self.filepath), texture["File"])
                            if self.import_textures and os.path.exists(filename):
                                dds_texture = load_dds(filename)
                                set_emissive_texture(scene_material, dds_texture)
                            else:
                                material_node.emissive_texture_file = texture["File"]

                        else:
                            unload_texconv()
                            raise Exception(f"Unknown material slot: {texture['Slot']}")

                        unload_texconv()

                # Flags
                if "Flags" in material.keys():
                    flags = material["Flags"]

                    if "Cull" in flags.keys():
                        material_node.cull = flags["Cull"]

                    if "DepthBias" in flags.keys():
                        material_node.depth_bias = flags["DepthBias"]

                    if "ShadowCaster" in flags.keys():
                        material_node.shadow_caster = flags["ShadowCaster"]

                    if "SlopeScaledDepthBias" in flags.keys():
                        material_node.slope_scaled_depth_bias = flags[
                        "SlopeScaledDepthBias"
                        ]

                # Blend
                if "Blend" in material.keys():
                    material_node.blend_enabled = material["Blend"]["Enable"]
                    material_node.blend_src = BlendLocation(
                        material["Blend"]["Src"]
                    ).name
                    material_node.blend_dest = BlendLocation(
                        material["Blend"]["Dst"]
                    ).name
                    material_node.blend_op = BlendOperation(
                        material["Blend"]["Op"]
                    ).name

                    material_node.blend_alpha_src = BlendLocation(
                        material["Blend"]["SrcAlpha"]
                    ).name
                    material_node.blend_alpha_dest = BlendLocation(
                        material["Blend"]["DstAlpha"]
                    ).name
                    material_node.blend_alpha_op = BlendOperation(
                        material["Blend"]["OpAlpha"]
                    ).name

                # Samplers
                if "Samplers" in material.keys():
                    last_sampler_location = None
                    for sampler in material["Samplers"]:
                        sampler_node = material_node_tree.nodes.new(
                            SamplerNode.__name__
                        )
                        material_node_tree.links.new(
                            sampler_node.outputs[0],
                            material_node.inputs[0],
                        )

                        if not last_sampler_location:
                            last_sampler_location = material_node.location
                            last_sampler_location.y += material_node.height + 50

                        last_sampler_location.x += 50 + sampler_node.width

                        sampler_node.location = last_sampler_location

                        sampler_node.slot = Slot(sampler["Slot"]).name
                        sampler_node.filter = sampler["Filter"]
                        sampler_node.max_anisotropy = sampler["MaxAnisotropy"]
                        sampler_node.address = sampler["Address"]
                        sampler_node.unit = ShaderUnit(sampler["Unit"]).name

                # Shader Parameters
                if "ShaderParams" in material.keys():
                    for shader_param in material["ShaderParams"]:
                        shader_node = material_node_tree.nodes.new(ShaderNode.__name__)
                        material_node_tree.links.new(
                            shader_node.outputs[0],
                            material_node.inputs[0],
                        )

                        shader_node.layout_name = shader_param["Layout"]
                        shader_node.slot = Slot(shader_param["Slot"]).name
                        for unit in shader_param["Unit"]:
                            unit_enum = ShaderUnit(unit)
                            if unit_enum == ShaderUnit.VERTEX_SHADER:
                                shader_node.shader_unit_vertex = True
                            elif unit_enum == ShaderUnit.COMPUTE_SHADER:
                                shader_node.shader_unit_compute = True
                            elif unit_enum == ShaderUnit.HULL_SHADER:
                                shader_node.shader_unit_hull = True
                            elif unit_enum == ShaderUnit.DOMAIN_SHADER:
                                shader_node.shader_unit_domain = True
                            elif unit_enum == ShaderUnit.GEOMETRY_SHADER:
                                shader_node.shader_unit_geometry = True
                            elif unit_enum == ShaderUnit.PIXEL_SHADER:
                                shader_node.shader_unit_pixel = True
                            else:
                                raise Exception(f"Unknown shader unit: {unit}")

                        # Constants
                        if "Constants" in shader_param.keys():
                            shader_node.emission_intensity = shader_param["Constants"][
                                "emissionIntensity"
                            ]
                            shader_node.emission_callback = shader_param["Constants"][
                                "emissionCallback"
                            ]

        self.report({"INFO"}, f"Imported {len(materials)} Materials")
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        self.width = 600

        file = context.space_data
        operator = file.active_operator
        layout.prop(operator, "import_textures")


def menu_func_import(self, context):
    self.layout.operator(
        ImportMaterialFileOperator.bl_idname, text="BMS Material File (.mtl)"
    )


def register():
    bpy.utils.register_class(ImportMaterialFileOperator)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportMaterialFileOperator)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

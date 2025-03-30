import json
import os

import bpy

from bms_blender_plugin.common.bml_material import (
    Material,
    Flag,
    Template,
    Blend,
    ShaderParam,
    ShaderUnit,
    Slot,
    ShaderParamConstants,
    Sampler,
    SamplerFilter,
    SamplerAddress,
    BlendLocation,
    BlendOperation,
    Texture,
    MaterialRootObject,
)
from bms_blender_plugin.common.blender_types import (
    BlenderEditorNodeType,
    BlenderNodeTreeType,
)
from bms_blender_plugin.common.export_dds import save_dds
from bms_blender_plugin.common.export_settings import ExportSettings
from bms_blender_plugin.ext.blender_dds_addon.directx.texconv import unload_texconv
from bms_blender_plugin.nodes_editor.material_editor import MaterialNodeTree
from bms_blender_plugin.nodes_editor.material_nodes.material_util import (
    get_albedo_texture,
    get_dds_texture_export_file_name,
    get_armw_texture,
    get_normal_texture,
    get_emissive_texture,
)
from bms_blender_plugin.nodes_editor.util import (
    get_bml_node_type,
    get_bml_node_tree_type,
    get_incoming_nodes,
)


def get_all_materials():
    """Returns all materials which are defined in the custom BML material tree. Throws an exception if more than
    one tree is defined."""
    material_node_trees = 0

    for tree in bpy.data.node_groups.values():
        if get_bml_node_tree_type(tree) == BlenderNodeTreeType.MATERIAL_TREE:
            material_node_trees += 1
            if material_node_trees > 1:
                raise Exception("More than one Material Node Tree found, aborting")

            return get_materials(tree)

    # no material trees defined
    return []


def get_materials(material_node_tree: MaterialNodeTree):
    """Returns all custom materials of a single MaterialNodeTree as a serializable list of bml_material.Material"""
    if (
        not material_node_tree
        or get_bml_node_tree_type(material_node_tree) == BlenderNodeTreeType.DOF_TREE
    ):
        raise Exception(f"{material_node_tree.name} is not a MaterialNodeTree")

    materials = list()
    for material_node in material_node_tree.nodes:
        if get_bml_node_type(material_node) != BlenderEditorNodeType.MATERIAL:
            continue

        # we can not export material nodes with no materials
        if not material_node.material:
            continue
            
        # Check if we have transparent material settings that would benefit from alpha sorting
        needs_alpha_sorting = False
        if (material_node.blend_enabled and 
            material_node.blend_src == BlendLocation.SRC_ALPHA.name and 
            material_node.blend_dest == BlendLocation.INV_SRC_ALPHA.name):
            needs_alpha_sorting = True
        
        # Set alpha_sort_triangles by default for transparent materials if not explicitly set
        if needs_alpha_sorting and not hasattr(material_node, "alpha_sort_triangles"):
            material_node.alpha_sort_triangles = True

        # collect all shader and sampler nodes
        sampler_nodes = list()
        shader_parameter_nodes = list()
        for incoming_node in get_incoming_nodes(material_node):
            if (
                get_bml_node_type(incoming_node)
                == BlenderEditorNodeType.SHADER_PARAMETER
            ):
                shader_parameter_nodes.append(incoming_node)
            elif get_bml_node_type(incoming_node) == BlenderEditorNodeType.SAMPLER:
                sampler_nodes.append(incoming_node)
            else:
                raise Exception(
                    f"Unknown node type: {get_bml_node_type(incoming_node)}"
                )

        # Textures
        # Any Blender texture which might be exported as DDS will override the manual filename of the node
        textures = list()

        albedo_texture_filename = get_dds_texture_export_file_name(
            get_albedo_texture(material_node.material)
        )
        if not albedo_texture_filename:
            albedo_texture_filename = material_node.albedo_texture_file
        if albedo_texture_filename != "":
            textures.append(Texture(albedo_texture_filename, Slot.ALBEDO))

        armw_texture_filename = get_dds_texture_export_file_name(
            get_armw_texture(material_node.material)
        )
        if not armw_texture_filename:
            armw_texture_filename = material_node.armw_texture_file
        if armw_texture_filename != "":
            textures.append(Texture(armw_texture_filename, Slot.ARMW))

        normal_texture_filename = get_dds_texture_export_file_name(
            get_normal_texture(material_node.material)
        )
        if not normal_texture_filename:
            normal_texture_filename = material_node.normal_map_texture_file
        if normal_texture_filename != "":
            textures.append(Texture(normal_texture_filename, Slot.NORMAL_MAP))

        emissive_texture_filename = get_dds_texture_export_file_name(
            get_emissive_texture(material_node.material)
        )
        if not emissive_texture_filename:
            emissive_texture_filename = material_node.emissive_texture_file
        if emissive_texture_filename != "":
            textures.append(Texture(emissive_texture_filename, Slot.EMISSIVE))

        # Flag
        flag = Flag(
            material_node.cull,
            material_node.depth_bias,
            material_node.shadow_caster,
            material_node.slope_scaled_depth_bias,
        )

        # Shader Parameters
        shader_parameters = list()
        for shader_parameter_node in shader_parameter_nodes:
            shader_units = list()
            if shader_parameter_node.shader_unit_vertex:
                shader_units.append(ShaderUnit.VERTEX_SHADER)
            if shader_parameter_node.shader_unit_compute:
                shader_units.append(ShaderUnit.COMPUTE_SHADER)
            if shader_parameter_node.shader_unit_hull:
                shader_units.append(ShaderUnit.HULL_SHADER)
            if shader_parameter_node.shader_unit_domain:
                shader_units.append(ShaderUnit.DOMAIN_SHADER)
            if shader_parameter_node.shader_unit_geometry:
                shader_units.append(ShaderUnit.GEOMETRY_SHADER)
            if shader_parameter_node.shader_unit_pixel:
                shader_units.append(ShaderUnit.PIXEL_SHADER)

            shader_parameter = ShaderParam(
                shader_parameter_node.layout_name,
                Slot[shader_parameter_node.slot],
                shader_units,
                ShaderParamConstants(
                    shader_parameter_node.emission_intensity,
                    shader_parameter_node.emission_callback,
                ),
            )
            shader_parameters.append(shader_parameter)

        # Template
        template = Template(
            material_node.template_file, material_node.template_material_name
        )

        # Samplers
        samplers = list()
        for sampler_node in sampler_nodes:
            sampler = Sampler(
                Slot[sampler_node.slot],
                ShaderUnit[sampler_node.unit],
                SamplerFilter[sampler_node.filter],
                sampler_node.max_anisotropy,
                SamplerAddress[sampler_node.address],
            )
            samplers.append(sampler)

        # Blend
        blend = None
        if material_node.blend_enabled:
            blend = Blend(
                material_node.blend_enabled,
                BlendLocation(material_node.blend_src),
                BlendLocation(material_node.blend_dest),
                BlendOperation(material_node.blend_op),
                BlendLocation(material_node.blend_alpha_src),
                BlendLocation(material_node.blend_alpha_dest),
                BlendOperation(material_node.blend_alpha_op),
            )

        material = Material(
            material_node.material.name,
            textures,
            flag,
            shader_parameters,
            template,
            samplers,
            blend,
        )

        materials.append(material)

    return materials


def export_materials(
    material_names_in_model, file_directory, export_settings: ExportSettings
):
    """Exports all materials which are both defined in the model and the custom BML material tree as Material.mtl.
    Also exports all textures of those materials as DDS."""
    materials_to_export = MaterialRootObject(list())

    # represents all materials which are in the MaterialNodeTree
    materials_in_file_map = {
        material.Name: material for material in get_all_materials()
    }

    for material_name in material_names_in_model:
        material = materials_in_file_map.pop(material_name, None)
        if not material:
            # material was not defined by the user (e.g. the object didn't have a material slot) - use a safe fallback
            material = Material.get_default(material_name)

        materials_to_export.Materials.append(material)

    # we popped all used materials, only unused ones remain
    if export_settings.export_unused_materials:
        materials_to_export.Materials.extend(materials_in_file_map.values())

    if export_settings.export_materials_file:
        material_filepath = os.path.join(file_directory, "Materials.mtl")
        with open(material_filepath, "w") as material_file:
            material_file.write(
                json.dumps(
                    materials_to_export,
                    indent=2,
                    default=lambda o: dict(
                        (key, value)
                        for key, value in o.__dict__.items()
                        if value or value == 0
                    ),
                )
            )
        print(f"Exported materials file: {material_filepath}")

    # DDS texture export
    if export_settings.export_textures:
        for material_obj in materials_to_export.Materials:
            if material_obj.Name in bpy.data.materials.keys():
                blender_material = bpy.data.materials[material_obj.Name]

                textures_to_be_exported = [
                    (get_albedo_texture(blender_material), "BC7_UNORM_SRGB"),
                    (get_armw_texture(blender_material), "BC7_UNORM"),
                    (get_normal_texture(blender_material), "BC5_UNORM"),
                    (get_emissive_texture(blender_material), "BC7_UNORM"),
                ]

                for texture, texture_format in textures_to_be_exported:
                    if texture:
                        texture_filepath = os.path.join(
                            file_directory, get_dds_texture_export_file_name(texture)
                        )
                        print(f"Exporting DDS file: {texture_filepath} ...")

                        save_dds(
                            tex=texture,
                            file=texture_filepath,
                            dds_fmt=texture_format,
                            allow_slow_codec=export_settings.allow_slow_texture_codecs,
                        )

                    unload_texconv()


def export_material_sets(context, material_set_filepath, material_names_in_model):
    """Exports all material sets as .mti. Will only export those if more than 1 set is defined."""
    # no material sets or only base set
    if len(context.scene.bml_material_sets) < 2:
        print("No Material Sets in scene, skipping...")
        return

    # parse all material sets but only use the material names which are actually in the export
    # all material names have to stay in order!
    material_names_export = []

    for material_set in context.scene.bml_material_sets:
        material_names_dict = {
            m.base_material.name: m.alternative_material.name
            for m in material_set.material_alternatives
        }
        for model_material_name in material_names_in_model:
            material_names_export.append(material_names_dict[model_material_name])

    # sanity check - all material sets have to have the same length
    if len(material_names_export) != len(material_names_in_model) * len(
        context.scene.bml_material_sets
    ):
        print("Error: not all Material Sets have the same length! Skipping export...")

    with open(material_set_filepath, "w") as material_sets_file:
        for line in material_names_export:
            material_sets_file.write(f"{line}\n")

    print(f"Exported {len(context.scene.bml_material_sets)} material sets to file: {material_set_filepath}")


def get_texture_files_to_be_exported():
    """Grabs all texture files from the first MaterialNodeTree which is found. Throws an exception if more than one
    MaterialNodeTree is found."""
    texture_files_to_export = set()

    material_node_trees = 0
    for tree in bpy.data.node_groups.values():
        if get_bml_node_tree_type(tree) == BlenderNodeTreeType.MATERIAL_TREE:
            material_node_trees += 1
            if material_node_trees > 1:
                raise Exception("More than one Material Node Tree found, aborting")

            for node in tree.nodes:
                if (
                    get_bml_node_type(node) == BlenderEditorNodeType.MATERIAL
                    and node.material
                ):
                    texture_files_to_export.add(
                        get_dds_texture_export_file_name(
                            get_albedo_texture(node.material)
                        )
                    )
                    texture_files_to_export.add(
                        get_dds_texture_export_file_name(
                            get_armw_texture(node.material)
                        )
                    )
                    texture_files_to_export.add(
                        get_dds_texture_export_file_name(
                            get_normal_texture(node.material)
                        )
                    )
                    texture_files_to_export.add(
                        get_dds_texture_export_file_name(
                            get_emissive_texture(node.material)
                        )
                    )

    texture_files_to_export = list(filter(None, texture_files_to_export))
    return texture_files_to_export

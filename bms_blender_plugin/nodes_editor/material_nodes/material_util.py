import os

import bpy

from bpy.app.handlers import persistent


def create_shader_nodes_for_material(material):
    """Creates a Blender Shading node tree for a material in order to give a preview which looks close to the BMS engine
    """
    if not material:
        return

    material.use_nodes = True
    node_tree = material.node_tree

    # don't touch the shading nodes if they already have their BML material node
    if "BMS Material Preview Node" in material.node_tree.keys():
        return node_tree

    node_tree.nodes.clear()

    # Textures
    albedo_texture_node = node_tree.nodes.new("ShaderNodeTexImage")
    albedo_texture_node.label = "Albedo Texture"
    albedo_texture_node.name = "Albedo Texture"
    albedo_texture_node.location = (0, 300)

    armw_texture_node = node_tree.nodes.new("ShaderNodeTexImage")
    armw_texture_node.label = "ARMW Texture"
    armw_texture_node.name = "ARMW Texture"
    armw_texture_node.location = (0, 0)

    normal_texture_node = node_tree.nodes.new("ShaderNodeTexImage")
    normal_texture_node.label = "Normal Texture"
    normal_texture_node.name = "Normal Texture"
    normal_texture_node.location = (0, -300)

    emissive_texture_node = node_tree.nodes.new("ShaderNodeTexImage")
    emissive_texture_node.label = "Emissive Texture"
    emissive_texture_node.name = "Emissive Texture"
    emissive_texture_node.location = (0, -600)

    # BMS Preview Node Group
    get_bms_material_preview_node_group()

    bms_preview_node_group = node_tree.nodes.new("ShaderNodeGroup")
    bms_preview_node_group.node_tree = bpy.data.node_groups["BMS Material Preview Node"]
    bms_preview_node_group.location = (400, 0)
    bms_preview_node_group.name = "BMS Material Preview Node"
    bms_preview_node_group.label = "BMS Material Preview Node"

    # Output
    output_node = node_tree.nodes.new("ShaderNodeOutputMaterial")
    output_node.location = (600, 0)

    # Links
    # Albedo Texture -> Preview Node Group
    node_tree.links.new(albedo_texture_node.outputs["Color"], bms_preview_node_group.inputs["Albedo Texture"])
    node_tree.links.new(albedo_texture_node.outputs["Alpha"], bms_preview_node_group.inputs["Albedo Alpha"])

    # ARMW Texture -> Preview Node Group
    node_tree.links.new(armw_texture_node.outputs["Color"], bms_preview_node_group.inputs["ARMW Texture"])
    node_tree.links.new(armw_texture_node.outputs["Alpha"], bms_preview_node_group.inputs["ARMW Alpha"])

    # Normal Texture -> Preview Node Group
    node_tree.links.new(normal_texture_node.outputs["Color"], bms_preview_node_group.inputs["Normal Texture"])

    # Emissive Texture -> Preview Node Group
    node_tree.links.new(emissive_texture_node.outputs["Color"], bms_preview_node_group.inputs["Emissive Texture"])

    # Preview Node Group -> Output
    node_tree.links.new(bms_preview_node_group.outputs[0], output_node.inputs[0])

    return node_tree


def get_bms_material_preview_node_group():
    """Returns the BMS Material Preview Node Group. Creates it if it doesn't exist."""
    MATERIAL_NODE_GROUP_NAME = "BMS Material Preview Node"

    if MATERIAL_NODE_GROUP_NAME in bpy.data.node_groups:
        return bpy.data.node_groups[MATERIAL_NODE_GROUP_NAME]

    node_group = bpy.data.node_groups.new(MATERIAL_NODE_GROUP_NAME, "ShaderNodeTree")

    # Inputs
    input_albedo_texture = node_group.inputs.new("NodeSocketColor", "Albedo Texture")

    input_albedo_alpha = node_group.inputs.new("NodeSocketFloat", "Albedo Alpha")
    input_albedo_alpha.default_value = 1
    input_albedo_alpha.min_value = 0
    input_albedo_alpha.max_value = 1

    input_armw_texture = node_group.inputs.new("NodeSocketColor", "ARMW Texture")

    input_armw_alpha = node_group.inputs.new("NodeSocketFloat", "ARMW Alpha")
    input_armw_alpha.default_value = 0

    input_normal_texture = node_group.inputs.new("NodeSocketColor", "Normal Texture")

    input_emissive_texture = node_group.inputs.new("NodeSocketColor", "Emissive Texture")

    input_ao_factor = node_group.inputs.new("NodeSocketFloat", "AO Factor")
    input_ao_factor.default_value = 0
    input_ao_factor.min_value = 0
    input_ao_factor.max_value = 1

    input_wetness_factor = node_group.inputs.new("NodeSocketFloat", "Wetness Factor")
    input_wetness_factor.default_value = 0
    input_wetness_factor.min_value = 0
    input_wetness_factor.max_value = 1

    # Nodes
    group_input_node = node_group.nodes.new("NodeGroupInput")
    group_input_node.location = (-600, 0)

    seperate_color_node = node_group.nodes.new("ShaderNodeSeparateColor")
    seperate_color_node.location = (-300, 0)

    multiply_node_1 = node_group.nodes.new("ShaderNodeMix")
    multiply_node_1.data_type = "RGBA"
    multiply_node_1.blend_type = "MULTIPLY"
    multiply_node_1.location = (0, 300)
    multiply_node_1.label = "Multiply 1"

    multiply_node_2 = node_group.nodes.new("ShaderNodeMix")
    multiply_node_2.data_type = "RGBA"
    multiply_node_2.blend_type = "MULTIPLY"
    multiply_node_2.location = (0, 0)
    multiply_node_2.label = "Multiply 2"

    normal_map_node = node_group.nodes.new("ShaderNodeNormalMap")
    normal_map_node.location = (0, -300)

    bsdf_node = node_group.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf_node.location = (300, 0)

    # Output
    node_output = node_group.nodes.new("NodeGroupOutput")
    node_output.location = (600, 0)
    output_bsdf = node_group.outputs.new("NodeSocketShader", "BSDF")

    # Links
    # Group Input -> Separate Color
    node_group.links.new(group_input_node.outputs[input_armw_texture.name], seperate_color_node.inputs["Color"])

    # Group Input -> Multiply 1
    node_group.links.new(group_input_node.outputs[input_ao_factor.name], multiply_node_1.inputs["Factor"])
    # Note: for some reason, addressing Multiply sockets by name does not work - we have to work by index
    node_group.links.new(group_input_node.outputs[input_albedo_texture.name], multiply_node_1.inputs[6])

    # Group Input -> Multiply 2
    node_group.links.new(group_input_node.outputs[input_armw_alpha.name], multiply_node_2.inputs[7])
    node_group.links.new(group_input_node.outputs[input_wetness_factor.name], multiply_node_2.inputs["Factor"])

    # Group Input -> Normal Map
    node_group.links.new(group_input_node.outputs[input_normal_texture.name], normal_map_node.inputs["Color"])

    # Group Input -> BSDF
    node_group.links.new(group_input_node.outputs[input_emissive_texture.name], bsdf_node.inputs["Emission"])
    node_group.links.new(group_input_node.outputs[input_albedo_alpha.name], bsdf_node.inputs["Alpha"])

    # Separate Color -> Multiply 1
    node_group.links.new(seperate_color_node.outputs["Red"], multiply_node_1.inputs[7])

    # Separate Color -> Multiply 2
    node_group.links.new(seperate_color_node.outputs["Green"], multiply_node_2.inputs[6])

    # Separate Color -> BSDF
    node_group.links.new(seperate_color_node.outputs["Blue"], bsdf_node.inputs["Metallic"])

    # Multiply 1 -> BSDF
    node_group.links.new(multiply_node_1.outputs[2], bsdf_node.inputs["Base Color"])

    # Multiply 2 -> BSDF
    node_group.links.new(multiply_node_2.outputs[2], bsdf_node.inputs["Roughness"])

    # Normal Map -> BSDF
    node_group.links.new(normal_map_node.outputs["Normal"], bsdf_node.inputs["Normal"])

    # BSDF -> Output
    node_group.links.new(bsdf_node.outputs["BSDF"], node_output.inputs[output_bsdf.name])

    return node_group


def get_albedo_texture(material):
    if material and material.node_tree and "Albedo Texture" in material.node_tree.nodes.keys():
        return material.node_tree.nodes["Albedo Texture"].image
    return None


def set_albedo_texture(material, image):
    if material and image and material.node_tree and "Albedo Texture" in material.node_tree.nodes.keys():
        material.node_tree.nodes["Albedo Texture"].image = image


def get_armw_texture(material):
    if material and material.node_tree and "ARMW Texture" in material.node_tree.nodes.keys():
        return material.node_tree.nodes["ARMW Texture"].image
    return None


def get_dds_texture_export_file_name(texture):
    """Returns the file name of a texture without its path and with the DDS extension"""
    if not texture:
        return None
    else:
        # !! use bpy.path.basename instead of os.path.basename
        file_name, file_extension = os.path.splitext(bpy.path.basename(texture.filepath))
        if file_extension != ".dds":
            file_extension = ".dds"
        return file_name + file_extension


def set_armw_texture(material, image):
    if material and image and material.node_tree and "ARMW Texture" in material.node_tree.nodes.keys():
        material.node_tree.nodes["ARMW Texture"].image = image


def get_normal_texture(material):
    if material and material.node_tree and "Normal Texture" in material.node_tree.nodes.keys():
        return material.node_tree.nodes["Normal Texture"].image
    return None


def set_normal_texture(material, image):
    if material and image and material.node_tree and "Normal Texture" in material.node_tree.nodes.keys():
        material.node_tree.nodes["Normal Texture"].image = image


def get_emissive_texture(material):
    if material and material.node_tree and "Emissive Texture" in material.node_tree.nodes.keys():
        return material.node_tree.nodes["Emissive Texture"].image
    return None


def set_emissive_texture(material, image):
    if material and image and material.node_tree and "Emissive Texture" in material.node_tree.nodes.keys():
        material.node_tree.nodes["Emissive Texture"].image = image


@persistent
def load_handler(dummy):
    get_bms_material_preview_node_group()


def register():
    # Create the Preview Material Node Group in a post handler (bpy.data will be ready by then)
    if load_handler not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load_handler)

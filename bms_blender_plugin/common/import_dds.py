"""Source: https://github.com/matyalatte/Blender-DDS-Addon/blob/main/addons/blender_dds_addon/ui/import_dds.py"""

import bpy
import numpy as np

import os
import shutil
import tempfile

from bms_blender_plugin.ext.blender_dds_addon.directx.dds import DDSHeader, DDS
from bms_blender_plugin.ext.blender_dds_addon.directx.texconv import Texconv


def load_dds(file, invert_normals=False, cubemap_layout='h-cross', texconv=None):
    """Import a texture form .dds file.

    Args:
        file (string): file path to .dds file
        invert_normals (bool): Flip y axis if the texture is normal map.
        cubemap_layout (string): Layout for cubemap faces.
        texconv (Texconv): Texture converter for dds.

    Returns:
        tex (bpy.types.Image): loaded texture
    """
    tex_list = []
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = os.path.join(temp_dir, os.path.basename(file))
            shutil.copyfile(file, temp)

            if texconv is None:
                texconv = Texconv()

            dds_header = DDSHeader.read_from_file(temp)

            # Check dxgi_format
            if dds_header.is_srgb():
                color_space = 'sRGB'
            else:
                color_space = 'Non-Color'

            tga_list = []

            # Disassemble if it's a non-2D texture
            if dds_header.is_3d() or dds_header.is_array():
                dds = DDS.load(temp)
                dds_list = dds.get_disassembled_dds_list()
                base_name = os.path.basename(temp)
                for new_dds, i in zip(dds_list, range(len(dds_list))):
                    new_name = ".".join(base_name.split(".")[:-1])
                    if i >= 1:
                        new_name += f"-{i}"
                    new_name += ".dds"
                    new_path = os.path.join(temp_dir, new_name)
                    new_dds.save(new_path)
                    tga = texconv.convert_to_tga(new_path, out=temp_dir, cubemap_layout=cubemap_layout,
                                                 invert_normals=invert_normals)
                    tga_list.append(tga)
            else:
                tga = texconv.convert_to_tga(temp, out=temp_dir, cubemap_layout=cubemap_layout,
                                             invert_normals=invert_normals)
                tga_list = [tga]

            for tga in tga_list:
                if tga is None:
                    raise RuntimeError('Failed to convert texture.')

                # Load tga file
                tex = load_texture(tga, name=os.path.basename(tga)[:-4], color_space=color_space)
                tex_list.append(tex)

        tex = tex_list[0]

        for tex in tex_list:
            if cubemap_layout.endswith("-fnz"):
                # Flip -z face for cubemaps
                w, h = tex.size
                pix = np.array(tex.pixels).reshape((h, w, -1))
                if cubemap_layout[0] == "v":
                    pix[h//4 * 0: h//4 * 1, w//3 * 1: w//3 * 2] = \
                        (pix[h//4 * 0: h//4 * 1, w//3 * 1: w//3 * 2])[::-1, ::-1]
                else:
                    pix[h//3 * 1: h//3 * 2, w//4 * 3: w//4 * 4] = \
                        (pix[h//3 * 1: h//3 * 2, w//4 * 3: w//4 * 4])[::-1, ::-1]
                pix = pix.flatten()
                tex.pixels = list(pix)

            tex.update()

    except Exception as e:
        for tex in tex_list:
            if tex is not None:
                bpy.data.images.remove(tex)
        raise e

    return tex_list[0]


def load_texture(file, name, color_space='Non-Color'):
    """Load a texture file.

    Args:
        file (string): file path for tga
        name (string): object name for the texture
        color_space (string): color space

    Returns:
        tex (bpy.types.Image): loaded texture
    """
    tex = bpy.data.images.load(file)
    tex.colorspace_settings.name = color_space
    tex.name = name
    tex.pack()
    tex.filepath = os.path.join('//textures', tex.name + '.' + file.split('.')[-1])
    tex.filepath_raw = tex.filepath
    return tex

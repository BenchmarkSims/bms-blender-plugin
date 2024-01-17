"""Source: https://github.com/matyalatte/Blender-DDS-Addon/blob/main/addons/blender_dds_addon/ui/export_dds.py"""
import os
import shutil
import tempfile

import bpy
import numpy as np

from bms_blender_plugin.ext.blender_dds_addon.directx.dds import is_hdr, DDS
from bms_blender_plugin.ext.blender_dds_addon.directx.texconv import Texconv


def save_dds(tex, file, dds_fmt, invert_normals=False, no_mip=False,
             image_filter='LINEAR',
             allow_slow_codec=False,
             texture_type="2d",
             cubemap_layout='h-cross',
             extra_texture_list=[],
             texconv=None):
    """Export a texture as DDS.

    Args:
        tex (bpy.types.Image): an image object
        file (string): file path to .dds file
        dds_fmt (string): DXGI format (e.g. BC1_UNORM)
        invert_normals (bool): Flip y axis for BC5 textures.
        no_mip (bool): Disable mipmap generation.
        allow_slow_codec (bool): Allow CPU codec for BC6 and BC7.
        texture_type (string): Type. 2d, cube, 2d_array, cube_array, or volume.
        cubemap_layout (string): Layout for cubemap faces.
        extra_texture_list (list[bpy.types.Image]): extra textures for non-2D formats.
        texconv (Texconv): Texture converter for dds.

    Returns:
        tex (bpy.types.Image): saved texture
    """
    is_cube = "cube" in texture_type
    is_array = "array" in texture_type
    is_3d = texture_type == "volume"

    # Check color space
    color_space = tex.colorspace_settings.name
    if 'SRGB' in dds_fmt and color_space != 'sRGB':
        print("Warning: Specified DXGI format uses sRGB as a color space,"
              f"but the texture uses {color_space} in Blender")
    elif 'SRGB' not in dds_fmt and color_space not in ['Non-Color', 'Raw']:
        print("Warning: Specified DXGI format does not use any color space conversion,"
              f"but the texture uses {color_space} in Blender")

    if is_hdr(dds_fmt):
        ext = '.hdr'
        fmt = 'HDR'
    else:
        ext = '.tga'
        fmt = 'TARGA_RAW'

    w, h = tex.size

    if is_cube:
        # Check aspect ratio
        def gcd(m, n):
            r = m % n
            return gcd(n, r) if r else n

        face_size = gcd(w, h)
        w_ratio = w // face_size
        h_ratio = h // face_size

        expected_ratio_dict = {
            "h-cross": [4, 3],
            "v-cross": [3, 4],
            "h-cross-fnz": [4, 3],
            "v-cross-fnz": [3, 4],
            "h-strip": [6, 1],
            "v-strip": [1, 6]
        }

        expected_ratio = expected_ratio_dict[cubemap_layout]

        if w_ratio != expected_ratio[0] or h_ratio != expected_ratio[1]:
            raise RuntimeError((
                f"{cubemap_layout} expects {expected_ratio[0]}:{expected_ratio[1]} aspect ratio "
                f"but the actual ratio is {w_ratio}:{h_ratio}."
            ))

    def get_z_flipped(tex):
        if cubemap_layout == "h-cross-fnz":
            offset = [3, 1]
        elif cubemap_layout == "v-cross-fnz":
            offset = [1, 0]
        temp_tex = tex.copy()
        pix = np.array(tex.pixels).reshape(h, w, -1)
        x, y = [c * face_size for c in offset]
        pix[y: y + face_size, x: x + face_size] = pix[y: y + face_size, x: x + face_size][::-1, ::-1]
        temp_tex.pixels = list(pix.flatten())
        return temp_tex

    def save_temp_dds(tex, temp_dir, ext, fmt, texconv, verbose=True):
        temp = os.path.join(temp_dir, tex.name + ext)

        save_texture(tex, temp, fmt)

        temp_dds = texconv.convert_to_dds(temp, dds_fmt, out=temp_dir,
                                          invert_normals=invert_normals, no_mip=no_mip,
                                          image_filter=image_filter,
                                          export_as_cubemap=is_cube,
                                          cubemap_layout=cubemap_layout,
                                          allow_slow_codec=allow_slow_codec, verbose=verbose)
        if temp_dds is None:
            raise RuntimeError('Failed to convert texture.')
        return temp_dds

    tex_list = [tex]
    if is_array or is_3d:
        tex_list += extra_texture_list

        # check if all textures have the same size
        for extra_tex in extra_texture_list:
            if extra_tex is None:
                raise RuntimeError("Specify a texture for each element of texture list")
            width, height = extra_tex.size
            if w != width or h != height:
                raise RuntimeError(
                    f"Extra textures should have the same size as the selected texture. ({w}, {h})."
                )

    try:
        temp_tex = None
        texconv = Texconv()

        with tempfile.TemporaryDirectory() as temp_dir:
            dds_path_list = []
            for tex in tex_list:
                if is_cube and ('fnz' in cubemap_layout):
                    temp_tex = get_z_flipped(tex)
                    temp_dds = save_temp_dds(temp_tex, temp_dir, ext, fmt, texconv)
                    bpy.data.images.remove(temp_tex)
                else:
                    temp_dds = save_temp_dds(tex, temp_dir, ext, fmt, texconv)
                dds_path_list.append(temp_dds)

            if (is_array or is_3d) and len(dds_path_list) > 1:
                dds_list = [DDS.load(dds_path) for dds_path in dds_path_list]
                dds = DDS.assemble(dds_list, is_array=is_array)
                dds.save(file)
            else:
                shutil.copyfile(dds_path_list[0], file)

    except Exception as e:
        if temp_tex is not None:
            bpy.data.images.remove(temp_tex)
        raise e

    return tex


def save_texture(tex, file, fmt):
    """Save a texture.

    Args:
        tex (bpy.types.Image): an image object
        file (string): file path
        fmt (string): file format
    """
    file_format = tex.file_format
    filepath_raw = tex.filepath_raw

    try:
        tex.file_format = fmt
        tex.filepath_raw = file
        tex.save()

        tex.file_format = file_format
        tex.filepath_raw = filepath_raw

    except Exception as e:
        tex.file_format = file_format
        tex.filepath_raw = filepath_raw
        raise e

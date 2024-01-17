import bpy
import bmesh
import math
from mathutils import Vector

from bms_blender_plugin.common.bml_structs import (
    DofType,
    VertexPBR,
    Vector3,
    Vector2,
    VSInputLight,
)
from bms_blender_plugin.common.blender_types import BlenderNodeType
from bms_blender_plugin.common.util import (
    get_bml_type,
    to_bms_coords,
    get_non_translate_dof_parent,
)


def get_bml_mesh_data(obj, max_vertex_index):
    """Returns the raw mesh data in the BML format as a tuple of vertices and vertex indices"""
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(mesh)
    bm.free()

    uv_names = [uvlayer.name for uvlayer in mesh.uv_layers]
    if len(mesh.loops) > 0:
        mesh.calc_normals()
        for name in uv_names:
            mesh.calc_tangents(uvmap=name)

    pb_vertices = []
    pb_vertices_per_face = []
    vertex_indices = []

    # All DOF children inherit their position relative to their parents DOF.
    if get_bml_type(obj.parent) == BlenderNodeType.DOF and (
        obj.parent.dof_type == DofType.ROTATE.name
        or obj.parent.dof_type == DofType.SCALE.name
    ):
        world_coord = obj.parent.matrix_world.inverted()

    elif get_bml_type(obj.parent) == BlenderNodeType.DOF and obj.parent.dof_type == DofType.TRANSLATE.name:
        # The only exception is the TRANSLATE DOF which will always reside at (0,0,0) - therefore we have
        # to use its world position

        # are we the grandchild of another object? Then we have to use those relative coords
        non_translate_dof_parent = get_non_translate_dof_parent(obj.parent)
        if non_translate_dof_parent:
            world_coord = non_translate_dof_parent.matrix_world.inverted()

        else:
            # no grandchild, we will use our world coords
            world_coord = obj.matrix_world

    else:
        # Not child of a DOF, just use our world coords
        world_coord = obj.matrix_world

    world_normal = world_coord.inverted_safe().transposed().to_3x3()

    for face in mesh.polygons:
        # loop over face loop
        for vert in [mesh.loops[i] for i in face.loop_indices]:
            vertex_pbr = VertexPBR()
            vertex_index = vert.vertex_index
            vertex_indices.append(vert.index + max_vertex_index)

            # position
            object_global_coord = to_bms_coords(
                world_coord @ mesh.vertices[vertex_index].co
            )
            vertex_pbr.position = Vector3(
                object_global_coord.x, object_global_coord.y, object_global_coord.z
            )

            # normal
            object_global_normal = to_bms_coords(world_normal @ vert.normal)
            # normalize the vector to remove any rounding errors
            object_global_normal = object_global_normal.normalized()
            vertex_pbr.normal = Vector3(
                object_global_normal.x, object_global_normal.y, object_global_normal.z
            )

            # tangent & uv
            if mesh.uv_layers.active:
                object_global_tangent = to_bms_coords(vert.tangent)
                vertex_pbr.tangent = Vector3(
                    object_global_tangent.x,
                    object_global_tangent.y,
                    object_global_tangent.z,
                )
                vertex_pbr.handedness = vert.bitangent_sign

                uv = tuple(
                    to_bms_coords(tuple(mesh.uv_layers.active.data[vert.index].uv))
                )
                vertex_pbr.uv = Vector2(uv[0], uv[1])

            pb_vertices_per_face.append(vertex_pbr)

        # switch the handedness by swapping the vertices
        pb_vertices.append(pb_vertices_per_face[0])
        pb_vertices.append(pb_vertices_per_face[2])
        pb_vertices.append(pb_vertices_per_face[1])
        pb_vertices_per_face = []

    return {"vertices": pb_vertices, "vertex_indices": vertex_indices}


def get_pbr_light_data(obj, max_vertex_index):
    """Returns the BML specific data for a PBR billboard light (BBL)"""
    # lookup table for the signs of the uv2 coords in a rectangle
    uv2_sign_lookup = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
    bpy.ops.object.mode_set(mode="OBJECT")
    mesh = obj.data

    # do not triangulate here, blender will sort the tris non-adjacent

    world_coord = to_bms_coords(obj.matrix_world)
    world_normal = obj.matrix_world.inverted_safe().transposed().to_3x3()

    bbl_vertices = []
    vertex_indices = []

    vertex_index = max_vertex_index

    for face in mesh.polygons:
        # loop over face loop

        if len(face.vertices) != 4:
            raise Exception("BBLights can only consist of rectangular planes")

        # calculate width and height
        face_width = (
            mesh.vertices[face.vertices[0]].co - mesh.vertices[face.vertices[1]].co
        ).length
        face_height = (
            mesh.vertices[face.vertices[1]].co - mesh.vertices[face.vertices[2]].co
        ).length

        # load the stored colors and normals from the polygon layers
        color = (
            mesh.polygon_layers_float["bml_color_r"].data[face.index].value,
            mesh.polygon_layers_float["bml_color_g"].data[face.index].value,
            mesh.polygon_layers_float["bml_color_b"].data[face.index].value,
            mesh.polygon_layers_float["bml_color_a"].data[face.index].value,
        )

        normal = Vector(
            (
                mesh.polygon_layers_float["bml_normal_x"].data[face.index].value,
                mesh.polygon_layers_float["bml_normal_y"].data[face.index].value,
                mesh.polygon_layers_float["bml_normal_z"].data[face.index].value,
            )
        )

        current_light_position = world_coord @ face.center

        # the normal will already be set to [0, 0, 0] for omnidirectional lights by join_objects_with_same_materials()
        current_light_normal = to_bms_coords(world_normal @ normal)
        # normalize the vector to remove any rounding errors
        current_light_normal = current_light_normal.normalized()

        # for each poly, add two triangles (== 6 vertices)
        # blender iterates counter-clockwise, so the following vertex indices will form 2 adjacent triangles of a
        # rectangular poly

        for i in [1, 0, 3, 1, 3, 2]:
            vs_input_light = VSInputLight()
            vertex_indices.append(vertex_index)

            # the position is identical for all vertices of a BBL
            current_light_position_bms_coords = to_bms_coords(current_light_position)
            vs_input_light.position = Vector3(
                current_light_position_bms_coords.x,
                current_light_position_bms_coords.y,
                current_light_position_bms_coords.z,
            )

            # ... same as the normal
            vs_input_light.normal = Vector3(
                current_light_normal.x, current_light_normal.y, current_light_normal.z
            )

            # ... and its color
            color_bytes = (
                (from_blender_color(color[3]) << 24)
                + (from_blender_color(color[2]) << 16)
                + (from_blender_color(color[1]) << 8)
                + (from_blender_color(color[0]) << 0)
            )
            vs_input_light.color = color_bytes

            # uv1 - just a regular texture uv
            if mesh.uv_layers.active:
                uv = tuple(to_bms_coords(tuple(mesh.uv_layers.active.data[i].uv)))
                vs_input_light.uv1 = Vector2(uv[0], uv[1])

            # uv2 - extrude the 4 corners of the vertex from the center point as origin
            uv2_signs = uv2_sign_lookup[i]
            uv2 = Vector(
                (uv2_signs[0] * face_width / 2, uv2_signs[1] * face_height / 2)
            )
            vs_input_light.uv2 = Vector2(uv2[0], uv2[1])

            bbl_vertices.append(vs_input_light)
            vertex_index += 1

    return {"vertices": bbl_vertices, "vertex_indices": vertex_indices}


def from_blender_color(c):
    """Converts a single color channel from Blenders format to a standard 1-byte value"""
    """https://blender.stackexchange.com/questions/260956/convert-rgb-256-to-rgb-float"""
    color = (
        max(0.0, c * 12.92) if c < 0.0031308 else 1.055 * math.pow(c, 1.0 / 2.4) - 0.055
    )
    return max(min(int(color * 255 + 0.5), 255), 0)


def to_blender_color(c):
    """Converts a single byte color channel to Blenders color format"""
    c = min(max(0, c), 255) / 255
    return c / 12.92 if c < 0.04045 else math.pow((c + 0.055) / 1.055, 2.4)

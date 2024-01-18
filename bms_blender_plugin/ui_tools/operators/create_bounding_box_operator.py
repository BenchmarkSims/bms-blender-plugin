import bpy
import bmesh

from bpy.types import Operator
import mathutils
from bpy_extras import object_utils

from bms_blender_plugin.common.blender_types import BlenderNodeType
from bms_blender_plugin.common.util import get_bml_type


class CreateBoundingBox(Operator):
    bl_idname = "bml.create_bounding_box"
    bl_label = "Create Bounding Box"
    bl_description = "Adds a new bounding box to the scene or selects an existing one"

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        bounding_box = None
        for obj in context.scene.objects:
            if get_bml_type(obj) == BlenderNodeType.BBOX:
                bounding_box = obj

        if not bounding_box:
            bounding_box = group_bounding_box()

        bounding_box.hide_set(False)
        bpy.ops.object.select_all(action="DESELECT")
        bounding_box.select_set(True)
        bpy.context.view_layer.objects.active = bounding_box

        return {"FINISHED"}


def add_box(width, height, depth):
    verts = [
        (+1.0, +1.0, -1.0),
        (+1.0, -1.0, -1.0),
        (-1.0, -1.0, -1.0),
        (-1.0, +1.0, -1.0),
        (+1.0, +1.0, +1.0),
        (+1.0, -1.0, +1.0),
        (-1.0, -1.0, +1.0),
        (-1.0, +1.0, +1.0),
    ]

    faces = [
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (4, 0, 3, 7),
    ]

    # apply size
    for i, v in enumerate(verts):
        verts[i] = v[0] * width, v[1] * depth, v[2] * height

    return verts, faces


def group_bounding_box():
    min_x, min_y, min_z = (999999.0,) * 3
    max_x, max_y, max_z = (-999999.0,) * 3
    location = [
        0.0,
    ] * 3
    for obj in bpy.context.visible_objects:
        for vertex in obj.bound_box:
            v_world = obj.matrix_world @ mathutils.Vector(
                (vertex[0], vertex[1], vertex[2])
            )

            if v_world[0] < min_x:
                min_x = v_world[0]
            if v_world[0] > max_x:
                max_x = v_world[0]

            if v_world[1] < min_y:
                min_y = v_world[1]
            if v_world[1] > max_y:
                max_y = v_world[1]

            if v_world[2] < min_z:
                min_z = v_world[2]
            if v_world[2] > max_z:
                max_z = v_world[2]

    verts_loc, faces = add_box(
        (max_x - min_x) / 2, (max_z - min_z) / 2, (max_y - min_y) / 2
    )
    mesh = bpy.data.meshes.new("Bounding Box")
    bm = bmesh.new()
    for v_co in verts_loc:
        bm.verts.new(v_co)

    bm.verts.ensure_lookup_table()

    for f_idx in faces:
        bm.faces.new([bm.verts[i] for i in f_idx])

    bm.to_mesh(mesh)
    mesh.update()
    location[0] = min_x + ((max_x - min_x) / 2)
    location[1] = min_y + ((max_y - min_y) / 2)
    location[2] = min_z + ((max_z - min_z) / 2)
    bbox = object_utils.object_data_add(bpy.context, mesh, operator=None)
    bbox.location = location
    bbox.display_type = "BOUNDS"
    bbox.hide_render = True
    bbox.bml_type = str(BlenderNodeType.BBOX)
    constraint = bbox.constraints.new(type="LIMIT_ROTATION")
    constraint.use_limit_x = True
    constraint.min_x = constraint.max_x = 0
    constraint.use_limit_y = True
    constraint.min_y = constraint.max_y = 0
    constraint.use_limit_z = True
    constraint.min_z = constraint.max_z = 0

    bm.free()

    return bbox


def register():
    bpy.utils.register_class(CreateBoundingBox)


def unregister():
    bpy.utils.unregister_class(CreateBoundingBox)

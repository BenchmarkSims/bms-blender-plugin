import math

from mathutils import Matrix, Vector

from bms_blender_plugin.common.blender_types import BlenderNodeType
from bms_blender_plugin.common.bml_structs import Primitive, PrimitiveTopology, Vector3, Slot, D3DMatrix, Switch, \
    DofType, Dof
from bms_blender_plugin.common.hotspot import Hotspot, MouseButton, ButtonType
from bms_blender_plugin.common.util import get_bml_type, get_objcenter, get_switches, get_dofs, \
    get_non_translate_dof_parent
from bms_blender_plugin.exporter.bml_mesh import get_bml_mesh_data, get_pbr_light_data
from bms_blender_plugin.common.coordinates import to_bms_coords


class ParsedNodes:
    """Data class which holds a list of parsed nodes in the BML binary format."""
    vertex_data: bytes
    vertices_length: int
    vertices_size: int

    def __init__(self, vertex_data, vertices_length, vertices_size):
        super().__init__()
        self.vertex_data = vertex_data
        self.vertices_length = vertices_length
        self.vertices_size = vertices_size


def parse_mesh(
    obj, nodes, vertex_indices, material_names, vertex_index_offset, vertex_start_offset
):
    """Adds a mesh to the BML node list"""
    print(f"parsing mesh {obj.name}")

    # Prepare the mesh
    obj_data = get_bml_mesh_data(obj, vertex_index_offset)
    obj_vertices = obj_data["vertices"]
    obj_indices = obj_data["vertex_indices"]

    # get the material
    if obj.data.materials and obj.data.materials[0]:
        material_name = obj.data.materials[0].name
    else:
        material_name = "BML-Default"

    try:
        material_index = material_names.index(material_name)
    except ValueError:
        material_index = len(material_names)
        material_names.append(material_name)

    vertex_size = 48  # since we only support v2 Primitives

    obj_vertices_data = []
    for obj_vertex in obj_vertices:
        obj_vertices_data += obj_vertex.to_data()

    # DOF children use coordinates local to their DOF
    if get_bml_type(obj.parent) == BlenderNodeType.DOF and obj.parent.dof_type != DofType.TRANSLATE.name:
        reference_point = to_bms_coords((0, 0, 0))
    else:
        reference_point = get_objcenter(obj)

    node = Primitive(
        index=len(nodes),
        topology=PrimitiveTopology.TRIANGLE_LIST,
        z_bias=0,
        index_count=len(obj_indices),
        start_index=0,
        vertex_start_index=0,
        vertex_start_offset=vertex_start_offset,
        vertex_count=len(obj_vertices),
        vertex_size=vertex_size,
        reference_point=Vector3(
            reference_point.x, reference_point.y, reference_point.z
        ),
        use_reference_point=1,
        alpha_sort_triangles=0,
        material_index=material_index,
    )

    nodes.append(node)
    vertex_indices += obj_indices

    return ParsedNodes(
        vertex_data=obj_vertices_data,
        vertices_length=len(obj_vertices),
        vertices_size=len(obj_vertices) * vertex_size,
    )


def parse_bbl_light(
    obj,
    nodes,
    vertex_indices,
    material_names,
    vertex_index_offset,
    vertex_start_offset,
):
    """Adds a PBR billboard light to the BML node list"""
    print(f"parsing PBR BB light {obj.name}")

    # Prepare the mesh
    obj_data = get_pbr_light_data(obj, vertex_index_offset)
    obj_vertices = obj_data["vertices"]
    obj_indices = obj_data["vertex_indices"]

    # get the material
    if obj.data.materials and obj.data.materials[0]:
        material_name = obj.data.materials[0].name
    else:
        material_name = "BML-BillboardGlowLight"

    try:
        material_index = material_names.index(material_name)
    except ValueError:
        material_index = len(material_names)
        material_names.append(material_name)

    vertex_size = 44  # size for PBR BB light

    obj_vertices_data = []
    for obj_vertex in obj_vertices:
        obj_vertices_data += obj_vertex.to_data()

    reference_point = get_objcenter(obj)
    node = Primitive(
        index=len(nodes),
        topology=PrimitiveTopology.TRIANGLE_LIST,
        z_bias=0,
        index_count=len(obj_indices),
        start_index=0,
        vertex_start_index=0,
        vertex_start_offset=vertex_start_offset,
        vertex_count=len(obj_vertices),
        vertex_size=vertex_size,
        reference_point=Vector3(
            reference_point.x, reference_point.y, reference_point.z
        ),
        use_reference_point=1,
        alpha_sort_triangles=0,
        material_index=material_index,
    )

    nodes.append(node)
    vertex_indices += obj_indices

    return ParsedNodes(
        vertex_data=obj_vertices_data,
        vertices_length=len(obj_vertices),
        vertices_size=len(obj_vertices) * vertex_size,
    )


def parse_slot(obj, nodes):
    """Adds a BML Slot to the BML node list"""
    print(f"parsing Slot {obj.name}")

    location = to_bms_coords(obj.matrix_world.translation)
    rotation_matrix = to_bms_coords(obj.rotation_euler).to_matrix()

    nodes.append(
        Slot(
            index=len(nodes),
            slot_number=obj.bml_slot_number,
            rotation=D3DMatrix(rotation_matrix),
            origin=Vector3(location.x, location.y, location.z),
        )
    )

    return ParsedNodes(vertex_data=[], vertices_length=0, vertices_size=0)


def parse_switch(obj, nodes):
    """Adds a BML Switch to the BML node list"""
    print(f"{obj.name} is a SWITCH")
    switch = get_switches()[obj.switch_list_index]
    nodes.append(
        Switch(len(nodes), switch.switch_number, switch.branch, obj.switch_default_on)
    )
    return ParsedNodes(vertex_data=[], vertices_length=0, vertices_size=0)


def parse_dof(obj, nodes):
    """Adds a BML DOF to the BML node list"""
    print(f"{obj.name} is a DOF")
    # add the DOF start node

    dof = get_dofs()[obj.dof_list_index]

    obj_orig_rotation_mode = obj.rotation_mode
    obj.rotation_mode = "QUATERNION"

    # default values
    scale = Vector3(0, 0, 0)
    rotation_matrix = Matrix()
    rotation_matrix = D3DMatrix(rotation_matrix.to_3x3())
    dof_min = obj.dof_min_input
    dof_max = obj.dof_max_input

    # Set the translation
    # For TDOFs, this is not the actual position of the DOF in 3d but the matrix coordinates which are
    # entered by the user. The TDOF always resides at (0,0,0)
    if obj.dof_type == DofType.TRANSLATE.name:
        translation = Vector((obj.dof_x, obj.dof_y, obj.dof_z, 0.0))
        # calculate the objects translation in the space of its parent
        translation = obj.matrix_parent_inverse @ translation

    # Other DOFs need their position set relative to their parent
    elif obj.dof_type == DofType.ROTATE.name or obj.dof_type == DofType.SCALE.name:

        # However if they are the child of a TDOF, we can not use that position - we have to find the first non-TDOF
        # parent.
        if (obj.parent and
                get_bml_type(obj.parent) == BlenderNodeType.DOF and
                obj.parent.dof_type == DofType.TRANSLATE.name):
            non_translate_dof_parent = get_non_translate_dof_parent(obj.parent)
            if non_translate_dof_parent:
                # We have found such a parent, calculate the objects position in relation to that parent
                translation = (obj.matrix_world - non_translate_dof_parent.matrix_world).translation
            else:
                # We did not find such a parent - we can just use our world position
                translation = obj.matrix_world.translation

        else:
            translation = obj.matrix_parent_inverse @ obj.location

    if obj.dof_type == DofType.ROTATE.name:
        # calculate the objects rotation and translation in the space of its parent
        rotation_matrix = obj.rotation_quaternion.to_matrix()
        rotation_matrix = obj.matrix_parent_inverse @ rotation_matrix.to_4x4()

        # BMS uses row major, Blender uses column major -> transpose
        rotation_matrix_bms = (
            to_bms_coords(rotation_matrix.to_quaternion()).to_matrix().transposed()
        )
        rotation_matrix = D3DMatrix(rotation_matrix_bms)

        dof_min = math.radians(obj.dof_min)
        dof_max = math.radians(obj.dof_max)

    elif obj.dof_type == DofType.SCALE.name:
        scale_vector = to_bms_coords(Vector((obj.dof_x, obj.dof_y, obj.dof_z)))
        scale = Vector3(scale_vector.x, scale_vector.y, scale_vector.z)


    translation = to_bms_coords(translation)

    dof_flags = 0
    if obj.dof_check_limits:
        dof_flags |= 0x00000001
    if obj.dof_reverse:
        dof_flags |= 0x00000002
    if obj.dof_normalise:
        dof_flags |= 0x00000004

    # min/max, multiplier
    if obj.dof_multiply_min_max:
        min_max_multiplier = 1
    else:
        min_max_multiplier = 1 / obj.dof_multiplier
    dof_min *= min_max_multiplier
    dof_max *= min_max_multiplier

    obj.rotation_mode = obj_orig_rotation_mode

    nodes.append(
        Dof(
            node_index=len(nodes),
            dof_number=dof.dof_number,
            dof_type=DofType[obj.dof_type],
            min_z=dof_min,
            max_z=dof_max,
            multiplier_z=obj.dof_multiplier,
            flags_z=dof_flags,
            scale=scale,
            translation=Vector3(translation.x, translation.y, translation.z),
            rotation=rotation_matrix,
        )
    )


def parse_hotspot(obj, hotspots: dict):
    """Parses a HOTSPOT by converting all of its callbacks to the correct data structure.
    Ignores all duplicate callback names."""
    print(f"{obj.name} is a HOTSPOT")

    location = to_bms_coords(obj.matrix_world.translation)
    for callback in obj.bml_hotspot_callbacks:
        if callback.callback_name not in hotspots.keys():
            hotspot = Hotspot(
                callback.callback_name,
                location.x,
                location.y,
                location.z,
                obj.bml_hotspot_size,
                callback.sound_id,
                MouseButton[callback.mouse_button],
                ButtonType[callback.button_type],
            )
            hotspots[callback.callback_name] = hotspot

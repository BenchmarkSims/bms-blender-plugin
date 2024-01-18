import struct
from enum import IntEnum

from mathutils import Vector

"""Represents the BMLv2 file structure"""


class Vector3:
    px: float
    py: float
    pz: float

    def __init__(self, x, y, z):
        self.px = x
        self.py = y
        self.pz = z

    def __str__(self):
        return f"({self.px}, {self.py}, {self.pz})"

    def to_data(self):
        return struct.pack("<fff", self.px, self.py, self.pz)


class Vector2:
    u: float
    v: float

    def __init__(self, u, v):
        self.u = u
        self.v = v

    def __str__(self):
        return f"({self.u}, {self.v})"

    def to_data(self):
        return struct.pack("<ff", self.u, self.v)


class D3DMatrix:
    vectors: [Vector3] = []

    def __init__(self, vectors_arg: [Vector]):
        self.vectors = []
        if len(vectors_arg) != 3:
            raise Exception("D3DMatrix expects 3 vectors")
        else:
            for v in vectors_arg:
                self.vectors.append(Vector3(v.x, v.y, v.z))

        if len(self.vectors) != 3:
            raise Exception("D3DMatrix expects 3 vectors")

    def to_data(self):
        return b"".join(v.to_data() for v in self.vectors)

    def __str__(self):
        vector_str = ""
        for vector in self.vectors:
            vector_str += vector.__str__() + "\n"
        return vector_str


class IndexBufferFormat(IntEnum):
    FORMAT_16 = 1
    FORMAT_32 = 2


class PrimitiveTopology(IntEnum):
    TRIANGLE_LIST = 4


"""NODES"""


class NodeType(IntEnum):
    INVALID = 0
    PRIMITIVE = 1
    DOF = 2
    DOF_END = 3
    SWITCH = 4
    SWITCH_END = 5
    SLOT = 6
    SLOT_END = 7
    RENDER_CONTROL = 8
    NODE_TYPE_MAX = 9


class Node:
    node_type: NodeType
    node_index: int
    version: int

    def __init__(self, node_type, node_index, node_version):
        self.node_type = node_type
        self.node_index = node_index
        self.version = node_version

    def to_data(self):
        return struct.pack("<III", self.node_type, self.node_index, self.version)


class Primitive(Node):
    topology: PrimitiveTopology
    z_bias: float
    index_count: int
    start_index: int
    vertex_start_index: int
    vertex_start_offset: int
    vertex_count: int
    vertex_size: int
    material_index: int
    reference_point: Vector3
    use_reference_point: int
    alpha_sort_triangles: int

    def __init__(self, index, topology, z_bias, index_count, start_index, vertex_start_index, vertex_start_offset,
                 vertex_count, vertex_size, reference_point, use_reference_point, alpha_sort_triangles, material_index):
        super().__init__(NodeType.PRIMITIVE, index, 2)
        self.topology = topology
        self.z_bias = z_bias
        self.index_count = index_count
        self.start_index = start_index
        self.vertex_start_index = vertex_start_index
        self.vertex_start_offset = vertex_start_offset
        self.vertex_count = vertex_count
        self.vertex_size = vertex_size
        self.material_index = material_index
        self.reference_point = reference_point
        self.use_reference_point = use_reference_point
        self.alpha_sort_triangles = alpha_sort_triangles

    def to_data(self):
        data = super().to_data()
        data += struct.pack("<IfIIIIII", self.topology, self.z_bias, self.index_count, self.start_index,
                            self.vertex_start_index, self.vertex_start_offset, self.vertex_count, self.vertex_size)
        data += self.reference_point.to_data()
        data += struct.pack("<??H", self.use_reference_point, self.alpha_sort_triangles, self.material_index)
        return data


class Slot(Node):
    slot_number: int
    rotation: D3DMatrix
    origin: Vector3

    def __init__(self, index, slot_number, rotation, origin):
        super().__init__(NodeType.SLOT, index, 1)
        self.slot_number = slot_number
        self.rotation = rotation
        self.origin = origin

    def to_data(self):
        data = super().to_data()
        data += b''.join([struct.pack("<I", self.slot_number), self.rotation.to_data(), self.origin.to_data()])
        return data


class SlotEnd(Node):
    def __init__(self, index):
        super().__init__(NodeType.SLOT_END, index, 1)

    def to_data(self):
        return super().to_data()


class Switch(Node):
    switch_number: int
    switch_branch: int = 0
    starts_enabled: bool = False

    def __init__(self, node_index, switch_number, switch_branch, starts_enabled):
        super().__init__(node_type=NodeType.SWITCH, node_index=node_index, node_version=1)
        self.switch_number = switch_number
        self. switch_branch = switch_branch
        self.starts_enabled = starts_enabled

    def to_data(self):
        data = super().to_data()
        data += struct.pack("<II?", self.switch_number, self.switch_branch, self.starts_enabled)
        return data


class SwitchEnd(Node):
    def __init__(self, node_index):
        super().__init__(node_type=NodeType.SWITCH_END, node_index=node_index, node_version=1)

    def to_data(self):
        return super().to_data()


class DofType(IntEnum):
    ROTATE = 0,
    TRANSLATE = 1,
    SCALE = 2
    # no more X-Rotate


class Dof(Node):
    dof_number: int
    dof_type: DofType
    min_z: float
    max_z: float
    multiplier_z: float
    flags_z: int
    scale: Vector3
    translation: Vector3
    rotation: D3DMatrix

    def __init__(self, node_index, dof_number, dof_type, min_z, max_z, multiplier_z, flags_z, scale, translation,
                 rotation):
        # use v2 for sDOFs
        if dof_type == DofType.SCALE:
            node_version = 2
        else:
            node_version = 1

        super().__init__(NodeType.DOF, node_index, node_version)
        self.dof_number = dof_number
        self.dof_type = dof_type
        self.min_z = min_z
        self.max_z = max_z
        self.multiplier_z = multiplier_z
        self.flags_z = flags_z
        self.scale = scale
        self.translation = translation
        self.rotation = rotation

    def to_data(self):
        data = super().to_data()
        data += struct.pack("<IIfffI", self.dof_number, self.dof_type, self.min_z, self.max_z, self.multiplier_z,
                            self.flags_z)
        data += self.scale.to_data()
        data += self.translation.to_data()
        data += self.rotation.to_data()
        return data


class DofEnd(Node):
    def __init__(self, node_index):
        super().__init__(node_type=NodeType.DOF_END, node_index=node_index, node_version=1)

    def to_data(self):
        return super().to_data()


"""RENDER CONTROLS"""

RC_ARGUMENTS_LENGTH = 5

class ControlType(IntEnum):
    # ignore NOOP (0), why would the user set that
    Z_BIAS = 1
    DOF_MATH = 2


class MathOp(IntEnum):
    SET = 0
    ADD = 1
    SUBTRACT = 2
    MULTIPLY = 3
    DIVIDE = 4
    MODULUS = 5
    COS = 6
    ACOS = 7
    SIN = 8
    ASIN = 9
    TAN = 10
    ATAN = 11
    ATAN2 = 12
    ANGLE_FROM_ADJ_HYP = 13
    ANGLE_FROM_OPP_HYP = 14
    ANGLE_FROM_OPP_ADJ = 15
    LENGTHOFADJ_FROM_ANGLE_OPP = 16
    LENGTHOFOPP_FROM_ANGLE_ADJ = 17
    ANGLEA_FROM_ANGLEB_SIDEA_SIDEB = 18
    ANGLEA_FROM_ANGLEB_SIDEA_SIDEC = 19
    ANGLEA_FROM_SIDEA_SIDEB_SIDEC = 20
    SIDEA_FROM_ANGLEA_SIDEB_SIDEC = 21
    CLAMP = 22
    NORMALIZE = 23
    MULTFRAMETIME = 24
    STEP = 25


class ArgType(IntEnum):
    FLOAT = 0
    DOF_ID = 1
    SCRATCH_VARIABLE_ID = 2


class ResultType(IntEnum):
    # ignore the 0 as its basically NOOP
    DOF_ID = 1
    SCRATCH_VARIABLE_ID = 2


class RenderControlMath:

    math_op: MathOp
    arguments: [(ArgType, any)] = []
    result_type: ResultType
    result_id: int  # either a scratchpad variable or a DOF id

    def __init__(self, math_op, arguments, result_type, result_id):
        self.math_op = math_op
        self.arguments = arguments
        self.result_type = result_type
        self.result_id = result_id

    def to_data(self):
        # pad the arguments
        while len(self.arguments) < RC_ARGUMENTS_LENGTH:
            self.arguments.append((0, 0.0))

        data = struct.pack("<H", self.math_op)

        for arg in self.arguments:
            data += struct.pack("<c", arg[0].to_bytes(length=1, byteorder="little"))

        data += struct.pack("<cI", self.result_type.to_bytes(length=1, byteorder="little"), self.result_id)

        for arg in self.arguments:
            if arg[0] == ArgType.DOF_ID or arg[0] == ArgType.SCRATCH_VARIABLE_ID:
                if not isinstance(arg[1], int):
                    raise Exception("Invalid argument type for RenderControl")
                data += struct.pack("<I", arg[1])

            elif arg[0] == ArgType.FLOAT:
                if not isinstance(arg[1], float):
                    raise Exception("Invalid argument type for RenderControl")
                data += struct.pack("<f", arg[1])

        return data


class RenderControlNode(Node):
    control_type: ControlType
    rc_math: RenderControlMath

    def __init__(self, node_index):
        super().__init__(node_type=NodeType.RENDER_CONTROL, node_index=node_index, node_version=1)
        self.control_type = ControlType.DOF_MATH

    def to_data(self):
        data = super().to_data()
        data += struct.pack("<I", self.control_type)
        data += self.rc_math.to_data()
        return data


"""VERTEX TYPES"""


class VertexPBR:
    position: Vector3 = Vector3(0, 0, 0)
    normal: Vector3 = Vector3(0, 0, 0)
    tangent: Vector3 = Vector3(0, 0, 0)
    uv: Vector2 = Vector2(0, 0)
    handedness: float = 0

    def __repr__(self):
        return f"position: {self.position}" \
               f"normal: {self.normal}" \
               f"tangent: {self.tangent}" \
               f"uv: {self.uv}" \
               f"handedness: {self.handedness}"

    def to_data(self):
        return [self.position.to_data(), self.normal.to_data(), self.tangent.to_data(), self.uv.to_data(),
                struct.pack("<f", self.handedness)]


class VSInputLight:
    position: Vector3 = Vector3(0, 0, 0)
    normal: Vector3 = Vector3(0, 0, 0)
    color: int = 0
    uv1: Vector2 = Vector2(0, 0)
    uv2: Vector2 = Vector2(0, 0)

    def to_data(self):
        return [self.position.to_data(), self.normal.to_data(), struct.pack("<I", self.color), self.uv1.to_data(),
                self.uv2.to_data()]


""" HEADER """


class Compression(IntEnum):
    NONE = 0,
    LZ_4 = 1,
    LZMA = 2

    def to_data(self):
        return struct.pack("<I", self.value)


class Header:
    file_type = bytes("BML\0", "ascii")
    version: int
    payload_compressed_size: int
    payload_size: int
    compression: Compression

    def __init__(self, version, payload_size, payload_compressed_size, compression):
        self.version = version
        self.payload_size = payload_size
        self.payload_compressed_size = payload_compressed_size
        self.compression = compression

    def to_data(self):
        return self.file_type + struct.pack("<IIQQ", self.version, self.compression, self.payload_size,
                                            self.payload_compressed_size)

    @staticmethod
    def from_data(header_bytes):
        fields = struct.unpack("<IIQQ", header_bytes[4:])  # stripping the file_type
        return Header(version=fields[0],
                      compression=fields[1],
                      payload_size=fields[2],
                      payload_compressed_size=fields[3])

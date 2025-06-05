from mathutils import Vector, Matrix, Quaternion, Euler

# Define the matrices here - updated for correct BMS coordinate system (-Z forward, -X right, Y up)
BMS_SPACE_MATRIX = Matrix(((0, 0, -1, 0), (-1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
BMS_SPACE_MATRIX_INV = BMS_SPACE_MATRIX.inverted_safe()
""" 
Two different vector object types (bbox and hotspots) use an x=rearwards, y=left, z=up coordinate system, whereas blender uses an x=right, y=forward, z=up 
coordinate system. The following transformation matrix will output a vector [-blender_y, -blender_x, blender_z] which 
from our blender vector definitions is [-forward, -right, up] = [rearwards, left, up]
"""
BMS_VECTOR_TRANSFORM_MATRIX = Matrix(((0, -1, 0), (-1, 0, 0), (0, 0, 1)))


def to_bms_coords(data, space_mat=BMS_SPACE_MATRIX, space_mat_inv=BMS_SPACE_MATRIX_INV):
    """Transforms from Blender space to BMS space (-Z forward, -X right, Y up)."""
    # matrix
    if type(data) is Matrix:
        return space_mat @ data.to_4x4() @ space_mat_inv
    # quaternion
    elif type(data) is Quaternion:
        mat = data.to_matrix()
        return (space_mat @ mat.to_4x4() @ space_mat_inv).to_quaternion()
    elif type(data) is Euler:
        x_angle = data[0]
        y_angle = data[1]
        z_angle = data[2]
        return Euler((x_angle, z_angle, y_angle), "XYZ")

    # vector
    elif type(data) is Vector or len(data) == 3:
        vec = Vector(data)
        return vec @ space_mat
    # uv coordinate
    elif len(data) == 2:
        return data[0], 1 - data[1]
    # unknown
    else:
        raise NotImplementedError("Unknown data type encountered.")

def vector_to_bms_coords(data):
    # Transforms specific vectors correctly. Use cases so far are bounding boxes and hotspots.
    return data @ BMS_VECTOR_TRANSFORM_MATRIX
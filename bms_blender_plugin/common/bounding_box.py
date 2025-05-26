from bms_blender_plugin.common.coordinates import vector_to_bms_coords

class BoundingBox:
    """Represents a bounding box. Each instance is a single bounding box. Calculates core attributes on init."""

    def __init__(self,obj):
        self.blender_coords = self.get_blender_vertices(obj)
        self.bms_coords = self.transform_blender_vertices(self.blender_coords)
        self.min_bms_vertex = self.get_min_vertex(self.bms_coords)
        self.max_bms_vertex = self.get_max_vertex(self.bms_coords)

    def get_blender_vertices(self, obj):
        """Returns the vertices of the object in the world coordinate system"""
        vertices = [obj.matrix_world.inverted() @ vertex.co for vertex in obj.data.vertices]
        return vertices

    def transform_blender_vertices(self, blender_vertices):
        """Transforms the vertices of the object to the BMS coordinate system"""
        transformed_vertices = [vector_to_bms_coords(vertex) for vertex in blender_vertices]
        return transformed_vertices

    def get_min_vertex(self, bms_coords):
        """ Assuming a simple cube primitive, the min vertex will always be the one with the smallest sum of coordinates."""
        min_vector = bms_coords[0]
        for vector in bms_coords[1:]:
            if sum(min_vector) > sum(vector):
                min_vector = vector
        return min_vector

    def get_max_vertex(self, bms_coords):
        """ Assuming a simple cube primitive, the max vertex will always be the one with the largest sum of coordinates."""
        max_vector = bms_coords[0]
        for vector in bms_coords[1:]:
            if sum(max_vector) < sum(vector):
                max_vector = vector
        return max_vector

    def bbox_to_txtpb_format(self):
        """Returns a string representation of the bounding box in the correct format for <AC>.txtpb files."""
        return (f'bounding_box {{\n'
                f'  min {{\n'
                f'      x: {round(self.min_bms_vertex.x, 1)}\n'
                f'      y: {round(self.min_bms_vertex.y, 1)}\n'
                f'      z: {round(self.min_bms_vertex.z, 1)}\n'
                f'  }}\n'
                f'  max {{\n'
                f'      x: {round(self.max_bms_vertex.x, 1)}\n'
                f'      y: {round(self.max_bms_vertex.y, 1)}\n'
                f'      z: {round(self.max_bms_vertex.z, 1)}\n'
                f'  }}\n'
                f'}}\n')

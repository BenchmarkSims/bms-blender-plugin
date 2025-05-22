import unittest
from bms_blender_plugin.common.hotspot import *
from mathutils import Vector


class TestHotspotFunctions(unittest.TestCase):
    def setUp(self):
        """ Define a hotspot with dummy values for which we can easily calculate known values."""
        self.test_mb = MouseButton.LEFT_CLICK.value
        self.test_bt = ButtonType.PUSH_BUTTON.value
        self.test_obj = Hotspot("test", 1.2345678, 2.3456789, 3.4567891, 20, 10, self.test_mb, self.test_bt)

    def test_blender_coords(self):
        """Test that blender coords are ingested correctly.
        Mainly serves to eliminate a possible source of error in the tranformation function."""
        expected_vector = Vector((1.2345678, 2.3456789, 3.4567891))
        self.assertEqual(expected_vector, self.test_obj.blender_coords)

    def test_blender_bms_transformation(self):
        """Test that blender coords are transformed correctly to BMS coords"""
        expected_vector = Vector((-2.3456789, -1.2345678, 3.4567891))
        self.assertEqual(expected_vector, self.test_obj.bms_coords)

    def test_export_string_formatting(self):
        """Given a correct transformation, test that the export string is formatted correctly."""
        expected_string = "test                            -2.345679   -1.234568    3.456789    20    10    1    p"
        self.assertEqual(expected_string, self.test_obj.__str__())


if __name__ == '__main__':
    unittest.main()


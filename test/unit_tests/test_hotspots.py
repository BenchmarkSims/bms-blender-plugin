import unittest
from bms_blender_plugin.common.hotspot import *
from mathutils import Vector


class TestHotspots(unittest.TestCase):
    def setup(self):
        self.test_mb = MouseButton(1, "p")
        self.test_bt = ButtonType(1, "p")
        self.test_obj = Hotspot("test", 1, 2, 3, 20, 10, self.test_mb, self.test_bt)

    def test_blender_coords(self):
        self.assertEqual(self.test_obj.blender_coords, Vector(1, 2, 3))

    def test_blender_bms_transformation(self):
        self.assertEqual(self.test_obj.bms_coords, Vector(1, 2, 3))

    def test_export_string_formatting(self):
        self.assertEqual(self.test_obj, "Noise")

    def tearDown(self):
        self.test_mb.dispose()
        self.test_bt.dispose()
        self.test_obj.dispose()

if __name__ == '__main__':
    unittest.main()

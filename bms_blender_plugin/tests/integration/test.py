"""Registration smoke test: blender --background --factory-startup --python-exit-code 1 --python tests/integration/test.py."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import bpy
import bms_blender_plugin

bms_blender_plugin.register()
assert hasattr(bpy.types.WindowManager, 'bml_statistics_include_hidden')
assert not bpy.context.window_manager.bml_statistics_include_hidden
assert bpy.ops.bml.calculate_statistics(scope='COLLECTION') == {'FINISHED'}
assert bpy.context.window_manager.bml_statistics_collection.triangles == 12
assert bpy.ops.bml.print_usage_report(kind='DOF') == {'FINISHED'}
bms_blender_plugin.unregister()
assert not hasattr(bpy.types.WindowManager, 'bml_statistics_include_hidden')
print('Full addon registration, statistics calculation, report and teardown passed')

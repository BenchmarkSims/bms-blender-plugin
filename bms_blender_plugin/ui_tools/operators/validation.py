import bpy
from bpy.types import Operator

from bms_blender_plugin.common.scene_validation import (
    run_basic_validation,
    store_scene_validation_report,
)

# Operator to run scene validation and store report in scene property
class BMS_OT_run_scene_validation(Operator):
    bl_idname = "bms.run_scene_validation"
    bl_label = "Run Scene Validation"
    bl_description = "Analyze scene (Switches & DOFs) for ID / index mismatches"
    bl_options = {"INTERNAL"}

    def execute(self, context):
        report = run_basic_validation(context)
        store_scene_validation_report(report)
        switches = report['switches']['counts']
        dofs = report['dofs']['counts']
        self.report({'INFO'}, f"Scene validation done. Switch issues: {sum(switches.values())}  DOF issues: {sum(dofs.values())}")
        print("[BMS Scene Validation] Switch counts:", switches)
        print("[BMS Scene Validation] DOF counts:", dofs)
        return {'FINISHED'}


def register():
    bpy.utils.register_class(BMS_OT_run_scene_validation)


def unregister():
    try:
        bpy.utils.unregister_class(BMS_OT_run_scene_validation)
    except Exception:
        pass


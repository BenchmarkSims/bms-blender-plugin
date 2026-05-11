import json
import bpy
from bpy.types import Panel


class BMS_PT_scene_validation(Panel):
    bl_idname = "BMS_PT_scene_validation"
    bl_label = "BMS Scene Validation"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BMS'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("bms.run_scene_validation", icon='FILE_REFRESH')
        data_raw = getattr(context.scene, 'bml_scene_validation_report', '')
        if not data_raw:
            layout.label(text="No report yet.")
            return
        try:
            data = json.loads(data_raw)
        except Exception:
            layout.label(text="Report parse error.")
            return
        layout.label(text=f"Generated: {data.get('generated_at','')}")

        switches = data.get('switches', {})
        dofs = data.get('dofs', {})
        sw_counts = switches.get('counts', {})
        dof_counts = dofs.get('counts', {})

        box = layout.box()
        box.label(text="Switches")
        box.label(text=f"Scene List: {switches.get('scene_count',0)}  Disk List: {switches.get('disk_count',0)}")
        tail_defs = switches.get('scene_only_definition_count', 0)
        if tail_defs:
            box.label(text=f"Scene-only defs beyond disk: {tail_defs}")
            tail_objs = switches.get('scene_only_objects', [])
            if tail_objs:
                box.label(text=f"Objects on scene-only indices: {len(tail_objs)}")
        if sw_counts:
            row = box.row()
            row.label(text=f"Unassigned: {sw_counts.get('UNASSIGNED_PERSISTENT_ID',0)}  Drift: {sw_counts.get('INDEX_DRIFT',0)}")
            row = box.row()
            row.label(text=f"Unknown: {sw_counts.get('UNKNOWN_PERSISTENT_ID',0)}  Zombie: {sw_counts.get('ZOMBIE_INDEX',0)}")
            row = box.row()
            row.label(text=f"List Label: {sw_counts.get('LIST_LABEL_MISMATCH',0)}  Obj Label: {sw_counts.get('OBJECT_LABEL_MISMATCH',0)}")

        box = layout.box()
        box.label(text="DOFs")
        box.label(text=f"Scene List: {dofs.get('scene_count',0)}  Disk List: {dofs.get('disk_count',0)}")
        tail_defs = dofs.get('scene_only_definition_count', 0)
        if tail_defs:
            box.label(text=f"Scene-only defs beyond disk: {tail_defs}")
            tail_objs = dofs.get('scene_only_objects', [])
            if tail_objs:
                box.label(text=f"Objects on scene-only indices: {len(tail_objs)}")
        if dof_counts:
            row = box.row()
            row.label(text=f"Unassigned: {dof_counts.get('UNASSIGNED_PERSISTENT_ID',0)}  Drift: {dof_counts.get('INDEX_DRIFT',0)}")
            row = box.row()
            row.label(text=f"Unknown: {dof_counts.get('UNKNOWN_PERSISTENT_ID',0)}  Zombie: {dof_counts.get('ZOMBIE_INDEX',0)}")
            row = box.row()
            row.label(text=f"List Label: {dof_counts.get('LIST_LABEL_MISMATCH',0)}  Obj Label: {dof_counts.get('OBJECT_LABEL_MISMATCH',0)}")

        issues_preview = []
        issues_preview.extend(switches.get('object_issues', [])[:6])
        issues_preview.extend(dofs.get('object_issues', [])[:6])
        if issues_preview:
            box = layout.box()
            box.label(text="Sample Issues")
            for item in issues_preview[:10]:
                cat = ','.join(item.get('categories', [])[:2])
                box.label(text=f"{cat} - {item.get('object','?')}")
            if len(issues_preview) > 10:
                box.label(text="(More not shown)")


def register():
    bpy.utils.register_class(BMS_PT_scene_validation)


def unregister():
    try:
        bpy.utils.unregister_class(BMS_PT_scene_validation)
    except Exception:
        pass


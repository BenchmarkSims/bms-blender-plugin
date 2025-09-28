"""
Export validation dialog operators.

Provides user-friendly dialogs for resolving validation issues before export.
"""

import bpy
from bpy.props import EnumProperty, StringProperty, BoolProperty
from bpy.types import Operator

from bms_blender_plugin.exporter.export_validation import (
    ValidationIssue,
    select_objects_from_issues,
    validate_export_readiness,
    get_out_of_range_issues,
    get_missing_persistent_id_issues,
)
from bms_blender_plugin.ui_tools.operators.assign_from_index import assign_persistent_ids_to_objects


def _collect_objects_from_collection(coll):
    result = set()
    def _recurse(c):
        for o in c.objects:
            result.add(o)
        for ch in c.children:
            _recurse(ch)
    _recurse(coll)
    return list(result)


def _export_scope_objects(context, use_lods=False):
    """Return objects in the active export collection hierarchy."""
    if use_lods and hasattr(context.scene, 'lod_list') and len(context.scene.lod_list) > 0:
        objs = set()
        for li in context.scene.lod_list:
            coll = getattr(li, 'collection', None)
            if coll:
                for o in _collect_objects_from_collection(coll):
                    objs.add(o)
        return list(objs)
    # Fallback to active collection
    alc = context.view_layer.active_layer_collection
    coll = alc.collection if alc else None
    if not coll:
        return []
    return _collect_objects_from_collection(coll)


class BML_OT_ValidationOutOfRangeDialog(Operator):
    """Dialog for handling out-of-range XML reference issues."""
    
    bl_idname = "bml.validation_out_of_range_dialog"
    bl_label = "Export Validation Warning"
    bl_description = "Resolve out-of-range XML reference issues"
    
    # Store the validation issues and context for the dialog
    issues_data: StringProperty(default="")  # type: ignore[misc]
    use_lods: BoolProperty(default=False)  # type: ignore[misc]  # whether to scope validation to all LOD collections
    
    action: EnumProperty(  # type: ignore[misc]
        name="Action",
        description="Choose how to handle the out-of-range issues",
        items=[
            ('SELECT', 'Select Objects & Cancel', 'Select problematic objects and cancel export for manual fixing'),
            ('RELOAD', 'Reload XML & Retry', 'Reload XML files and retry validation'),
            ('CONTINUE', 'Continue Export', 'Proceed with export using fallback values (may cause incorrect behavior)')
        ],
        default='SELECT'
    )
    
    def draw(self, context):
        layout = self.layout
        
        layout.label(text="⚠️ Export Validation Warning", icon='ERROR')
        layout.separator()
        
        # Recompute issues; avoid relying on temporary scene properties
        issues = validate_export_readiness(context, _export_scope_objects(context, self.use_lods))
        out_of_range_issues = get_out_of_range_issues(issues)
        
        if out_of_range_issues:
            total_objects = sum(len(issue.objects) for issue in out_of_range_issues)
            layout.label(text=f"Found {total_objects} objects with out-of-range XML references:")
            
            box = layout.box()
            for issue in out_of_range_issues:
                box.label(text=f"• {issue.issue_type.value.replace('_', ' ').title()}")
                object_names = [obj.name for obj in issue.objects[:3]]  # Show first 3
                if len(issue.objects) > 3:
                    object_names.append(f"... and {len(issue.objects) - 3} more")
                box.label(text=f"  Objects: {', '.join(object_names)}")
        
        layout.separator()
        layout.label(text="This usually means your XML files are outdated.")
        layout.separator()
        
        layout.prop(self, "action", expand=True)
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=500)
    
    def execute(self, context):
        # Recompute on execute to reflect current state
        issues = validate_export_readiness(context, _export_scope_objects(context, self.use_lods))
        out_of_range_issues = get_out_of_range_issues(issues)
        
        if self.action == 'SELECT':
            select_objects_from_issues(out_of_range_issues)
            self.report({'INFO'}, f"Selected {sum(len(issue.objects) for issue in out_of_range_issues)} problematic objects")
            
        elif self.action == 'RELOAD':
            try:
                # Use existing reload operators from preferences.py
                # These handle proper cache clearing and repopulation
                bpy.ops.bml.reload_switch_list()
                bpy.ops.bml.reload_dof_list()
                self.report({'INFO'}, "XML files reloaded. Re-run export.")
                
            except Exception as e:
                self.report({'ERROR'}, f"Failed to reload XML files: {str(e)}")
                
        elif self.action == 'CONTINUE':
            self.report({'WARNING'}, "Continuing export with fallback behavior")
            # Don't set any flags - let export continue
        
        return {'FINISHED'}
    
    def _cleanup_scene_properties(self, context):
        """Clean up temporary scene properties used by validation system."""
        if hasattr(context.scene, '_bml_validation_issues'):
            delattr(context.scene, '_bml_validation_issues')
        if hasattr(context.scene, '_bml_export_cancelled'):
            delattr(context.scene, '_bml_export_cancelled')
        if hasattr(context.scene, '_bml_export_retry'):
            delattr(context.scene, '_bml_export_retry')


class BML_OT_ValidationMissingIDDialog(Operator):
    """Dialog for handling missing persistent ID issues.

    Updated: Inline confirmation (no secondary pop-up) and clearer, action-focused labels.
    """
    
    bl_idname = "bml.validation_missing_id_dialog" 
    bl_label = "DOF/Switch IDs Missing"
    bl_description = "Assign persistent DOF / Switch IDs before continuing export"
    use_lods: BoolProperty(default=False)  # type: ignore[misc]
    
    action: EnumProperty(  # type: ignore[misc]
        name="Action",
        description="Choose how to handle missing persistent IDs",
        items=[
            ('SELECT', 'Select & Cancel', 'Select objects and cancel export so you can assign IDs manually'),
            ('AUTO_ASSIGN', 'Assign IDs & Continue', 'Automatically assign persistent IDs (recommended) and continue export'),
            ('IGNORE', 'Ignore & Continue', 'Continue export without assigning (falls back to legacy index resolution; risky)')
        ],
        default='SELECT'
    )
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="Persistent IDs Required", icon='INFO')
        layout.separator()

        # Recompute issues to reflect current state
        issues = validate_export_readiness(context, _export_scope_objects(context, self.use_lods))
        missing_id_issues = get_missing_persistent_id_issues(issues)

        if missing_id_issues:
            total_objects = sum(len(issue.objects) for issue in missing_id_issues)
            layout.label(text=f"Found {total_objects} objects using legacy indices without persistent IDs:")

            box = layout.box()
            for issue in missing_id_issues:
                issue_type = issue.issue_type.value.replace('_', ' ').title()
                box.label(text=f"• {issue_type}: {len(issue.objects)} objects")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Objects are still using legacy list indices.", icon='ERROR')
        col.label(text="Assigning persistent IDs prevents future XML changes from breaking exports.")
        col.label(text="Recommended: Assign IDs & Continue.")
        layout.separator()

        layout.prop(self, "action", expand=True)
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=500)
    
    def execute(self, context):
        # Recompute on execute to reflect current state
        issues = validate_export_readiness(context, _export_scope_objects(context, self.use_lods))
        missing_id_issues = get_missing_persistent_id_issues(issues)
        
        if self.action == 'SELECT':
            select_objects_from_issues(missing_id_issues)
            self.report({'INFO'}, f"Selected {sum(len(issue.objects) for issue in missing_id_issues)} objects needing persistent IDs")
            
        elif self.action == 'AUTO_ASSIGN':
            total_objects = sum(len(issue.objects) for issue in missing_id_issues)
            switch_count, dof_count = self._auto_assign_persistent_ids(missing_id_issues)
            total_assigned = switch_count + dof_count

            # Console summary (acts as log)
            print(f"[BML][AUTO_ASSIGN] Target Objects: {total_objects} | Switches Assigned: {switch_count} | DOFs Assigned: {dof_count}")

            if total_assigned == total_objects:
                self.report({'INFO'}, f"Successfully assigned persistent IDs to all {total_assigned} objects")
            elif total_assigned > 0:
                self.report({'WARNING'}, f"Assigned persistent IDs to {total_assigned} of {total_objects} objects (some may have out-of-range indices)")
            else:
                self.report({'ERROR'}, "Failed to assign any persistent IDs - check console for details")
            # Continue with export
            
        elif self.action == 'IGNORE':
            self.report({'WARNING'}, "Continuing without assigning persistent IDs (legacy index fallback)")
            # Continue with export
        
        return {'FINISHED'}
    
    def _auto_assign_persistent_ids(self, issues):
        """Auto-assign persistent IDs to specific objects from validation issues."""
        # Collect all objects from the issues that need persistent ID assignment
        target_objects = []
        for issue in issues:
            target_objects.extend(issue.objects)
        
        if not target_objects:
            return 0, 0
            
        try:
            # Use targeted assignment that only processes the specific objects, returns (switches_assigned, dofs_assigned)
            return assign_persistent_ids_to_objects(bpy.context, target_objects)
        except Exception as e:
            # If assignment fails, fallback gracefully
            print(f"Persistent ID auto-assignment failed: {e}")
            return 0, 0


# Registration
def register():
    bpy.utils.register_class(BML_OT_ValidationOutOfRangeDialog)
    bpy.utils.register_class(BML_OT_ValidationMissingIDDialog)


def unregister():
    bpy.utils.unregister_class(BML_OT_ValidationMissingIDDialog) 
    bpy.utils.unregister_class(BML_OT_ValidationOutOfRangeDialog)
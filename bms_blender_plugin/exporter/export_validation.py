"""
Export validation module for pre-flight checks before BML export.

Validates scene state to catch common issues that could cause export failures
or silent data corruption, providing clear feedback and resolution options. 
Import LodItem type.

To add a new validation check:
1. Add an issue type to ValidationIssueType enum if required
2. Add a grouping property to ValidationIssue dataclass
3. Add a new _check_*_issues() method to ExportValidator class
4. Call your new method from validate_scene()

...for issues that need user input for resolution (not just collecting stats):
5. Add filter function(s) like get_*_issues() if resolution of the issue needs special dialog handling
6. Create dialog operator in validation_dialogs.py if needed - eg. user choice required for resolution
7. Update run_validation_with_dialogs() to handle your new issue type with dialogs

Example: Adding a "missing material" validation check:
# Step 1: Add to ValidationIssueType enum
MATERIAL_MISSING = "material_missing"

# Step 2: Add grouping property to ValidationIssue
@property
def is_material_issue(self) -> bool:
    return self.issue_type == ValidationIssueType.MATERIAL_MISSING

# Step 3: Add validation method to ExportValidator
def _check_material_issues(self, context) -> List[ValidationIssue]:
    issues = []
    for obj in context.scene.objects:
        if not obj.material_slots:
            issues.append(ValidationIssue(
                ValidationIssueType.MATERIAL_MISSING,
                [obj],
                f"Object '{obj.name}' has no materials assigned"
            ))
    return issues

# Step 4: Call from validate_scene()
issues.extend(self._check_material_issues(context))

# Steps 5-7: Add dialog handling if needed
"""

import bpy
from dataclasses import dataclass
from typing import List, Optional, Iterable
from enum import Enum

from bms_blender_plugin.common.blender_types import BlenderNodeType, LodItem
from bms_blender_plugin.common.util import get_bml_type, get_dofs, get_switches


class ValidationIssueType(Enum):
    """Types of validation issues that can be detected."""
    DOF_OUT_OF_RANGE = "dof_out_of_range"
    SWITCH_OUT_OF_RANGE = "switch_out_of_range"
    DOF_MISSING_PERSISTENT_ID = "dof_missing_persistent_id"
    SWITCH_MISSING_PERSISTENT_ID = "switch_missing_persistent_id"


@dataclass
class ValidationIssue:
    """Represents a single validation issue found in the scene."""
    """Contains properties to identify groups of issue types for batch handling."""
    issue_type: ValidationIssueType
    objects: List[bpy.types.Object]
    description: str
    
    @property
    def is_out_of_range_issue(self) -> bool:
        """True if this is an out-of-range XML reference issue."""
        return self.issue_type in (
            ValidationIssueType.DOF_OUT_OF_RANGE,
            ValidationIssueType.SWITCH_OUT_OF_RANGE
        )
    
    @property
    def is_missing_persistent_id_issue(self) -> bool:
        """True if this is a missing persistent ID issue."""
        return self.issue_type in (
            ValidationIssueType.DOF_MISSING_PERSISTENT_ID, 
            ValidationIssueType.SWITCH_MISSING_PERSISTENT_ID
        )


class ExportValidator:
    """Validates scene state before export to catch common issues."""
    
    def validate_scene(self, context, objects: Optional[Iterable[bpy.types.Object]] = None) -> List[ValidationIssue]:
        """
        Returns list of validation issues found in scene.
        
        Add new validation method calls here:
        issues.extend(self._check_your_new_validation(context))
        """
        issues = []
        issues.extend(self._check_dof_issues(context, objects))
        issues.extend(self._check_switch_issues(context, objects))
        # Add new validation checks here
        return issues
    
    def _get_dof_max_index(self, context) -> int:
        """Prefer cached Scene DOF list; fallback to util cache."""
        try:
            if hasattr(context.scene, 'dof_list') and len(context.scene.dof_list) > 0:
                return len(context.scene.dof_list) - 1
        except Exception:
            pass
        try:
            available_dofs = get_dofs()
            return len(available_dofs) - 1
        except Exception:
            return -1

    def _get_switch_max_index(self, context) -> int:
        """Prefer cached Scene Switch list; fallback to util cache."""
        try:
            if hasattr(context.scene, 'switch_list') and len(context.scene.switch_list) > 0:
                return len(context.scene.switch_list) - 1
        except Exception:
            pass
        try:
            available_switches = get_switches()
            return len(available_switches) - 1
        except Exception:
            return -1

    def _iter_target_objects(self, context, objects: Optional[Iterable[bpy.types.Object]]):
        if objects is not None:
            # Ensure we iterate once over a stable list
            return list(objects)
        return list(context.scene.objects)

    def _check_dof_issues(self, context, objects: Optional[Iterable[bpy.types.Object]]) -> List[ValidationIssue]:
        """Check for DOF-related validation issues."""
        issues = []
        max_dof_index = self._get_dof_max_index(context)
        if max_dof_index < 0:
            # No list available; skip checks safely
            return issues
        
        out_of_range_objects = []
        missing_persistent_id_objects = []
        
        for obj in self._iter_target_objects(context, objects):
            if get_bml_type(obj) != BlenderNodeType.DOF:
                continue
                
            persistent_id = getattr(obj, "bml_dof_number", -1)
            list_index = getattr(obj, "dof_list_index", 0)
            
            if persistent_id < 0:
                # No persistent ID assigned
                if list_index > max_dof_index:
                    # List index is out of range - XML mismatch issue
                    out_of_range_objects.append(obj)
                else:
                    # Valid list index but no persistent ID - migration needed
                    missing_persistent_id_objects.append(obj)
        
        # Create issues for out-of-range objects
        if out_of_range_objects:
            description = (
                f"Found {len(out_of_range_objects)} DOF(s) referencing XML entries "
                f"not found in current DOF.xml (max index: {max_dof_index}). "
                "This usually means your DOF.xml file is outdated."
            )
            issues.append(ValidationIssue(
                ValidationIssueType.DOF_OUT_OF_RANGE,
                out_of_range_objects,
                description
            ))
        
        # Create issues for missing persistent IDs
        if missing_persistent_id_objects:
            description = (
                f"Found {len(missing_persistent_id_objects)} DOF(s) using legacy list indices "
                "without persistent IDs. These will work for export but may break "
                "if DOF.xml files are reordered."
            )
            issues.append(ValidationIssue(
                ValidationIssueType.DOF_MISSING_PERSISTENT_ID,
                missing_persistent_id_objects,
                description
            ))
        
        return issues
    
    def _check_switch_issues(self, context, objects: Optional[Iterable[bpy.types.Object]]) -> List[ValidationIssue]:
        """Check for Switch-related validation issues.""" 
        issues = []
        max_switch_index = self._get_switch_max_index(context)
        if max_switch_index < 0:
            return issues
        
        out_of_range_objects = []
        missing_persistent_id_objects = []
        
        for obj in self._iter_target_objects(context, objects):
            if get_bml_type(obj) != BlenderNodeType.SWITCH:
                continue
                
            persistent_number = getattr(obj, "bml_switch_number", -1)
            persistent_branch = getattr(obj, "bml_switch_branch", -1) 
            list_index = getattr(obj, "switch_list_index", 0)
            
            if persistent_number < 0 or persistent_branch < 0:
                # No persistent ID assigned
                if list_index > max_switch_index:
                    # List index is out of range - XML mismatch issue
                    out_of_range_objects.append(obj)
                else:
                    # Valid list index but no persistent ID - migration needed
                    missing_persistent_id_objects.append(obj)
        
        # Create issues for out-of-range objects
        if out_of_range_objects:
            description = (
                f"Found {len(out_of_range_objects)} Switch(es) referencing XML entries "
                f"not found in current Switch.xml (max index: {max_switch_index}). "
                "This usually means your Switch.xml file is outdated."
            )
            issues.append(ValidationIssue(
                ValidationIssueType.SWITCH_OUT_OF_RANGE,
                out_of_range_objects, 
                description
            ))
        
        # Create issues for missing persistent IDs
        if missing_persistent_id_objects:
            description = (
                f"Found {len(missing_persistent_id_objects)} Switch(es) using legacy list indices "
                "without persistent IDs. These will work for export but may break "
                "if Switch.xml files are reordered."
            )
            issues.append(ValidationIssue(
                ValidationIssueType.SWITCH_MISSING_PERSISTENT_ID,
                missing_persistent_id_objects,
                description
            ))
        
        return issues


def validate_export_readiness(context, objects: Optional[Iterable[bpy.types.Object]] = None) -> List[ValidationIssue]:
    """
    Main entry point for export validation.
    
    Returns list of validation issues that should be addressed before export.
    Empty list means scene is ready for export.
    """
    validator = ExportValidator()
    return validator.validate_scene(context, objects)


def get_out_of_range_issues(issues: List[ValidationIssue]) -> List[ValidationIssue]:
    """Filter issues to only out-of-range XML reference problems."""
    return [issue for issue in issues if issue.is_out_of_range_issue]


def get_missing_persistent_id_issues(issues: List[ValidationIssue]) -> List[ValidationIssue]:
    """Filter issues to only missing persistent ID problems.""" 
    return [issue for issue in issues if issue.is_missing_persistent_id_issue]


def select_objects_from_issues(issues: List[ValidationIssue]):
    """Select all objects referenced in the given validation issues."""
    bpy.ops.object.select_all(action='DESELECT')
    
    for issue in issues:
        for obj in issue.objects:
            obj.select_set(True)
    
    # Set first object as active if any were selected
    selected_objects = [obj for issue in issues for obj in issue.objects]
    if selected_objects:
        bpy.context.view_layer.objects.active = selected_objects[0]


def run_validation_with_dialogs(context) -> bool:
    """
    DEPRECATED: Asynchronous dialogs cannot be orchestrated reliably here.
    Kept for backward compatibility; returns True as a no-op.
    Use validate_export_readiness() + show_validation_dialog_if_needed() instead.
    """
    return True


def _collect_objects_from_collection(coll: bpy.types.Collection) -> List[bpy.types.Object]:
    result = set()
    def _rec(c):
        for o in c.objects:
            result.add(o)
        for ch in c.children:
            _rec(ch)
    _rec(coll)
    return list(result)


def _collect_objects_from_active_collection(context) -> List[bpy.types.Object]:
    alc = context.view_layer.active_layer_collection
    coll = alc.collection if alc else None
    if not coll:
        return []
    return _collect_objects_from_collection(coll)


def _collect_objects_from_lods(lods: Iterable[LodItem]) -> List[bpy.types.Object]:
    objs = set()
    for li in lods:
        coll = getattr(li, 'collection', None)
        if coll:
            for o in _collect_objects_from_collection(coll):
                objs.add(o)
    return list(objs)


def show_validation_dialog_export(
    context,
    objects: Optional[Iterable[bpy.types.Object]] = None,
    lods: Optional[Iterable[LodItem]] = None,
) -> bool:
    """
    Stateless helper to show the appropriate validation dialog if issues exist.
    Returns True if a dialog was invoked (export should be cancelled by caller),
    False if no issues were found.
    """
    # Determine the validation scope if not explicitly provided
    if objects is None:
        if lods:
            objects = _collect_objects_from_lods(lods)
        else:
            objects = _collect_objects_from_active_collection(context)

    issues = validate_export_readiness(context, objects)
    if not issues:
        return False
    # Prioritize out-of-range (schema mismatches) over missing IDs
    use_lods_flag = bool(lods)
    if get_out_of_range_issues(issues):
        bpy.ops.bml.validation_out_of_range_dialog('INVOKE_DEFAULT', use_lods=use_lods_flag)
        return True
    if get_missing_persistent_id_issues(issues):
        bpy.ops.bml.validation_missing_id_dialog('INVOKE_DEFAULT', use_lods=use_lods_flag)
        return True
    return False
    
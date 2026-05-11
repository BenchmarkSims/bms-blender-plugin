import json
from datetime import datetime, timezone

import bpy

from .util import get_switches, get_dofs, get_bml_type
from .blender_types import BlenderNodeType


CATEGORY_UNASSIGNED = "UNASSIGNED_PERSISTENT_ID"
CATEGORY_INDEX_DRIFT = "INDEX_DRIFT"
CATEGORY_UNKNOWN = "UNKNOWN_PERSISTENT_ID"
CATEGORY_ZOMBIE = "ZOMBIE_INDEX"
CATEGORY_LIST_LABEL_MISMATCH = "LIST_LABEL_MISMATCH"
CATEGORY_OBJECT_LABEL_MISMATCH = "OBJECT_LABEL_MISMATCH"

ALL_CATEGORIES = [
    CATEGORY_UNASSIGNED,
    CATEGORY_INDEX_DRIFT,
    CATEGORY_UNKNOWN,
    CATEGORY_ZOMBIE,
    CATEGORY_LIST_LABEL_MISMATCH,
    CATEGORY_OBJECT_LABEL_MISMATCH,
]

# Helper to strip Blender's auto-duplicate suffixes for name comparisons
def _strip_dup_suffix(name: str) -> str:
    # Blender auto-duplicates like Name.001, Name.002 etc.
    if not name:
        return name
    parts = name.rsplit('.', 1)
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0]
    return name

# Simple name match (case-sensitive)
def _names_match(actual: str, expected: str) -> bool:
    return actual == expected


def _validate_switch_objects(scene):
    scene_switches = list(getattr(scene, 'switch_list', []))
    disk_switches = get_switches(force_disk=True)
    scene_lookup = {(s.switch_number, s.branch_number): s for s in scene_switches}

    issues = []  # per object
    counts = {k: 0 for k in ALL_CATEGORIES}

    for obj in bpy.data.objects:
        if get_bml_type(obj) != BlenderNodeType.SWITCH:
            continue
        obj_cats = []
        sn = getattr(obj, 'bml_switch_number', -1)
        sb = getattr(obj, 'bml_switch_branch', -1)
        idx = getattr(obj, 'switch_list_index', -1)

        # UNASSIGNED - Object has no valid persistent ID
        if sn < 0 or sb < 0:
            obj_cats.append(CATEGORY_UNASSIGNED)

        # ZOMBIE INDEX - Object switch index is out of range of scene cached list <0 or >=len
        if idx < 0 or idx >= len(scene_switches):
            obj_cats.append(CATEGORY_ZOMBIE)

        # INDEX DRIFT - Object has PID and index, but index in cached xml list corresponds to different cached xml switch than PID does
        if (sn >= 0 and sb >= 0 and 0 <= idx < len(scene_switches)):
            entry = scene_switches[idx]
            if not (entry.switch_number == sn and entry.branch_number == sb):
                obj_cats.append(CATEGORY_INDEX_DRIFT)

        # UNKNOWN PERSISTENT ID - Object has PID, but no such PID in scene cached list
        if (sn >= 0 and sb >= 0 and (sn, sb) not in scene_lookup):
            obj_cats.append(CATEGORY_UNKNOWN)

        # OBJECT LABEL MISMATCH (only if we have matching definition in scene list)
        if (sn, sb) in scene_lookup:
            expected_label = getattr(scene_lookup[(sn, sb)], 'label', '')
            actual_base = _strip_dup_suffix(obj.name)
            if expected_label and not _names_match(actual_base, expected_label):
                obj_cats.append(CATEGORY_OBJECT_LABEL_MISMATCH)

        if obj_cats:
            for c in obj_cats:
                counts[c] += 1
            issues.append({
                'object': obj.name,
                'categories': obj_cats,
                'switch_number': sn,
                'branch': sb,
                'index': idx,
            })

    # LIST LABEL MISMATCHES comparing overlapping indices
    list_label_mismatches = []
    overlap = min(len(scene_switches), len(disk_switches))
    for i in range(overlap):
        s_item = scene_switches[i]
        d_item = disk_switches[i]
        s_label = getattr(s_item, 'label', '')
        d_label = getattr(d_item, 'label', '')
        if s_label != d_label:
            list_label_mismatches.append({
                'index': i,
                'scene_label': s_label,
                'disk_label': d_label,
            })
    counts[CATEGORY_LIST_LABEL_MISMATCH] = len(list_label_mismatches)

    return {
        'object_issues': issues,
        'list_label_mismatches': list_label_mismatches,
        'counts': counts,
        'scene_count': len(scene_switches),
        'disk_count': len(disk_switches),
    }


def _validate_dof_objects(scene):
    scene_dofs = list(getattr(scene, 'dof_list', []))
    disk_dofs = get_dofs(force_disk=True)
    scene_lookup = {d.dof_number: d for d in scene_dofs}

    issues = []
    counts = {k: 0 for k in ALL_CATEGORIES}

    for obj in bpy.data.objects:
        if get_bml_type(obj) != BlenderNodeType.DOF:
            continue
        obj_cats = []
        dn = getattr(obj, 'bml_dof_number', -1)
        idx = getattr(obj, 'dof_list_index', -1)

        # Persistent ID unassigned
        if dn < 0:
            obj_cats.append(CATEGORY_UNASSIGNED)

        # Zombie index - Object DOF index is out of range of scene cached list <0 or >=len
        if idx < 0 or idx >= len(scene_dofs):
            obj_cats.append(CATEGORY_ZOMBIE)

        # Index drift - Object has PID and index, but index in cached xml list corresponds to different cached xml DOF than PID does
        if (dn >= 0 and 0 <= idx < len(scene_dofs)):
            entry = scene_dofs[idx]
            if entry.dof_number != dn:
                obj_cats.append(CATEGORY_INDEX_DRIFT)

        if (dn >= 0 and dn not in scene_lookup):
            obj_cats.append(CATEGORY_UNKNOWN)

        # Object NAME does not match expected label in cached scene list (if match exists)
        if dn in scene_lookup:
            expected_label = getattr(scene_lookup[dn], 'label', '')
            actual_base = _strip_dup_suffix(obj.name)
            if expected_label and not _names_match(actual_base, expected_label):
                obj_cats.append(CATEGORY_OBJECT_LABEL_MISMATCH)

        if obj_cats:
            for c in obj_cats:
                counts[c] += 1
            issues.append({
                'object': obj.name,
                'categories': obj_cats,
                'dof_number': dn,
                'index': idx,
            })

    list_label_mismatches = []
    overlap = min(len(scene_dofs), len(disk_dofs))
    for i in range(overlap):
        s_item = scene_dofs[i]
        d_item = disk_dofs[i]
        s_label = getattr(s_item, 'label', '')
        d_label = getattr(d_item, 'label', '')
        if s_label != d_label:
            list_label_mismatches.append({
                'index': i,
                'scene_label': s_label,
                'disk_label': d_label,
            })
    counts[CATEGORY_LIST_LABEL_MISMATCH] = len(list_label_mismatches)

    return {
        'object_issues': issues,
        'list_label_mismatches': list_label_mismatches,
        'counts': counts,
        'scene_count': len(scene_dofs),
        'disk_count': len(disk_dofs),
    }


def run_basic_validation(context=None):
    scene = context.scene if context else bpy.context.scene
    report = {
        'switches': _validate_switch_objects(scene),
        'dofs': _validate_dof_objects(scene),
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'version': 1,
    }
    return report


def store_validation_report(report):
    try:
        as_json = json.dumps(report, indent=2)
        bpy.context.scene.bml_validation_report = as_json
    except Exception:
        pass


def register():  # called by addon auto-loader
    from bpy.props import StringProperty
    bpy.types.Scene.bml_validation_report = StringProperty(
        name="BMS Validation Report",
        description="JSON data for last BMS validation run",
        default=""
    )


def unregister():
    try:
        del bpy.types.Scene.bml_validation_report
    except Exception:
        pass

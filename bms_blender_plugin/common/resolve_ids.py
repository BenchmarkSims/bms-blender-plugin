"""Central helpers for resolving DOF / Switch persistent IDs or safe fallbacks.

All systems (validation, nodes, mediator, exporter) should use these helpers
instead of directly indexing into list indices. This ensures consistent
resolution order and prevents IndexError crashes when XML/cached lists change.

Resolution order:
1. Persistent ID properties (authoritative) if set.
2. Scene cached list (context.scene.dof_list / switch_list) if index in range.
3. Global cached XML data via get_dofs() / get_switches().
4. Fallback: return None (caller decides how to proceed gracefully).
"""
from __future__ import annotations
from typing import Optional, Tuple
import bpy

from bms_blender_plugin.common.blender_types import BlenderNodeType
from bms_blender_plugin.common.util import get_dofs, get_switches, get_bml_type


def resolve_dof_number(obj) -> Optional[int]:
    """Return persistent DOF number for a DOF object or None if unresolved.

    Safe: never raises IndexError.
    """
    if not obj:
        return None
    if get_bml_type(obj) != BlenderNodeType.DOF:
        return None

    pid = getattr(obj, "bml_dof_number", -1)
    if isinstance(pid, int) and pid >= 0:
        return pid

    idx = getattr(obj, "dof_list_index", -1)
    if not isinstance(idx, int) or idx < 0:
        return None

    # Scene cached list first
    scene_list = getattr(bpy.context.scene, "dof_list", None)
    if scene_list and 0 <= idx < len(scene_list):
        item = scene_list[idx]
        return getattr(item, "dof_number", None)

    # Global cache fallback
    try:
        dofs = get_dofs()
        if 0 <= idx < len(dofs):
            return dofs[idx].dof_number
    except Exception:
        pass
    return None


def resolve_switch_id(obj) -> Tuple[Optional[int], Optional[int]]:
    """Return (switch_number, branch) for a Switch object or (None, None) if unresolved."""
    if not obj:
        return None, None
    if get_bml_type(obj) != BlenderNodeType.SWITCH:
        return None, None

    num = getattr(obj, "bml_switch_number", -1)
    br = getattr(obj, "bml_switch_branch", -1)
    if isinstance(num, int) and num >= 0 and isinstance(br, int) and br >= 0:
        return num, br

    idx = getattr(obj, "switch_list_index", -1)
    if not isinstance(idx, int) or idx < 0:
        return None, None

    scene_list = getattr(bpy.context.scene, "switch_list", None)
    if scene_list and 0 <= idx < len(scene_list):
        item = scene_list[idx]
        return getattr(item, "switch_number", None), getattr(item, "branch_number", None)

    try:
        switches = get_switches()
        if 0 <= idx < len(switches):
            sw = switches[idx]
            return sw.switch_number, sw.branch
    except Exception:
        pass
    return None, None

__all__ = ["resolve_dof_number", "resolve_switch_id"]

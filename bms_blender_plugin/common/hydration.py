"""Hydration/load_post handler.

Ensures that on .blend load the scene cached switch/DOF lists (if avail) become the
authoritative source for switch / DOF lists until the user explicitly
reloads from disk XML via UI.
    - Allows seamless switching between .blend files with different XML snapshots
    - Ensures UI lists reflect the loaded .blend's snapshot immediately
    - Primary use case: user working with a foreign blend file created using different XMLs
"""
from __future__ import annotations
import bpy
from bpy.app.handlers import persistent


@persistent
def bml_hydrate_after_load(_):
    try:
        import bms_blender_plugin.common.util as util
        util.switches = []
        util.dofs = []
        util._switches_hydrated = False
        util._dofs_hydrated = False
        # Trigger early hydration so UI immediately reflects snapshot
        util.get_switches()
        util.get_dofs()
    except Exception:
        pass


def register():
    if bml_hydrate_after_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(bml_hydrate_after_load)


def unregister():
    if bml_hydrate_after_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(bml_hydrate_after_load)
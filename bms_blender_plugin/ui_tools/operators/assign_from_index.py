import bpy

from bms_blender_plugin.common.util import get_switches, get_dofs, get_bml_type, get_parent_dof_or_switch
from bms_blender_plugin.common.blender_types import BlenderNodeType
from bms_blender_plugin.ui_tools.dof_behaviour import update_switch_or_dof_name


class BML_OT_assign_switch_from_index(bpy.types.Operator):
    # Populate persistent Switch number and branch from the currently selected list entry - useful if object was created before persistent ID properties added
    # If the index out of range, nothing changed and a warning report issued

    bl_idname = "bml.assign_switch_from_index"
    bl_label = "Assign from Index"
    bl_description = (
        "Assign persistent Switch Number and Branch from the current switch list selection. "
        "Uses switch_list_index; overwrites existing persistent IDs."
    )
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not obj:
            return False
        target = get_parent_dof_or_switch(obj)
        return target is not None and get_bml_type(target) == BlenderNodeType.SWITCH

    def execute(self, context):
        obj = get_parent_dof_or_switch(context.active_object)
        switches = get_switches()
        idx = getattr(obj, "switch_list_index", -1)
        try:
            print(f"[DEBUG] assign_switch_from_index.pre: obj={getattr(obj,'name',None)} index={idx} switches_len={len(switches)}")
        except Exception:
            pass
        if 0 <= idx < len(switches):
            sw = switches[idx]
            obj.bml_switch_number = sw.switch_number
            obj.bml_switch_branch = sw.branch
            update_switch_or_dof_name(obj, context)
            try:
                print(f"[DEBUG] assign_switch_from_index.post: obj={getattr(obj,'name',None)} assigned={sw.switch_number}:{sw.branch} from_index={idx}")
            except Exception:
                pass
            self.report({'INFO'}, f"Assigned Switch #{sw.switch_number} Branch {sw.branch} from index {idx}")
            return {'FINISHED'}
        try:
            print(f"[DEBUG] assign_switch_from_index.out_of_range: obj={getattr(obj,'name',None)} index={idx} len={len(switches)}")
        except Exception:
            pass
        self.report({'WARNING'}, (
            f"Switch list index {idx} out of range; no assignment performed. "
            f"List may be stale or truncated – reload switch.xml (disable/enable addon) or refresh definitions."
        ))
        return {'CANCELLED'}


class BML_OT_assign_dof_from_index(bpy.types.Operator):
    # Populate persistent DOF number from the currently selected list entry - useful if object was created before persistent ID properties added

    bl_idname = "bml.assign_dof_from_index"
    bl_label = "Assign from Index"
    bl_description = (
        "Assign persistent DOF Number from the current DOF list selection. "
        "Uses dof_list_index; overwrites existing persistent ID."
    )
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not obj:
            return False
        target = get_parent_dof_or_switch(obj)
        return target is not None and get_bml_type(target) == BlenderNodeType.DOF

    def execute(self, context):
        obj = get_parent_dof_or_switch(context.active_object)
        dofs = get_dofs()
        idx = getattr(obj, "dof_list_index", -1)
        if 0 <= idx < len(dofs):
            de = dofs[idx]
            obj.bml_dof_number = de.dof_number
            update_switch_or_dof_name(obj, context)
            self.report({'INFO'}, f"Assigned DOF #{de.dof_number} from index {idx}")
            return {'FINISHED'}
        self.report({'WARNING'}, (
            f"DOF list index {idx} out of range; no assignment performed. "
            f"List may be stale or truncated – reload DOF.xml (disable/enable addon) or refresh definitions."
        ))
        return {'CANCELLED'}


class BML_OT_reassign_all_ids(bpy.types.Operator):
    # Batch assign persistent switch/dof ID/branch from current list indices (convert legacy index-based method to persistent property method)
    # Scope: entire scene or only active collection hierarchy
    # Reassign each for consistency
    

    bl_idname = "bml.reassign_all_ids"
    bl_label = "Re-Assign All IDs"
    bl_description = (
        "Batch assign persistent Switch / DOF IDs from current list indices across the chosen scope. "
        "Overwrites existing persistent IDs. Use wrapper operators in UI for specific targets."
    )
    bl_options = {"UNDO"}

    scope = bpy.props.EnumProperty(
        name="Scope",
        items=(
            ("SCENE", "Whole Scene", "Process every object in the scene"),
            ("ACTIVE_COLLECTION", "Active Collection", "Process only objects in the active collection (recursive)"),
        ),
        default="SCENE",
    )

    target_types = bpy.props.EnumProperty(
        name="Target",
        items=(
            ("BOTH", "Switches & DOFs", "Assign both"),
            ("SWITCH", "Switches Only", "Assign only switches"),
            ("DOF", "DOFs Only", "Assign only dofs"),
        ),
        default="BOTH",
    )

    confirm = bpy.props.BoolProperty(default=True)

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def _collect_objects(self, context):
        if self.scope == "SCENE":
            return list(context.scene.objects)
        # ACTIVE_COLLECTION path
        coll = context.view_layer.active_layer_collection.collection if context.view_layer.active_layer_collection else None
        if not coll:
            return []
        result = set()

        def _recurse(c):
            for obj in c.objects:
                result.add(obj)
            for child in c.children:
                _recurse(child)

        _recurse(coll)
        return list(result)

    def execute(self, context):
        switches_enum = get_switches()
        dofs_enum = get_dofs()
        processed_switches = 0
        processed_dofs = 0
        objs = self._collect_objects(context)
        for obj in objs:
            bml_type = get_bml_type(obj)
            if self.target_types in {"BOTH", "SWITCH"} and bml_type == BlenderNodeType.SWITCH:
                idx = getattr(obj, "switch_list_index", -1)
                if 0 <= idx < len(switches_enum):
                    sw = switches_enum[idx]
                    obj.bml_switch_number = sw.switch_number
                    obj.bml_switch_branch = sw.branch
                    update_switch_or_dof_name(obj, context)
                    processed_switches += 1
            if self.target_types in {"BOTH", "DOF"} and bml_type == BlenderNodeType.DOF:
                idx = getattr(obj, "dof_list_index", -1)
                if 0 <= idx < len(dofs_enum):
                    de = dofs_enum[idx]
                    obj.bml_dof_number = de.dof_number
                    update_switch_or_dof_name(obj, context)
                    processed_dofs += 1
        self.report({'INFO'}, f"Re-assigned IDs - Switches: {processed_switches}, DOFs: {processed_dofs}")
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Internal shared helper for wrapper batch operators (simpler popup usage)
# ---------------------------------------------------------------------------
def _batch_reassign(context, scope: str, target: str, target_objects=None):
    """
    Batch assign persistent IDs from list indices.
    
    Args:
        target_objects: Optional list of specific objects to process. 
                       If None, processes all objects in scope.
    """
    switches_enum = get_switches()
    dofs_enum = get_dofs()
    processed_switches = 0
    processed_dofs = 0

    def collect(scope_mode):
        if scope_mode == "SCENE":
            return list(context.scene.objects)
        coll = context.view_layer.active_layer_collection.collection if context.view_layer.active_layer_collection else None
        if not coll:
            return []
        result = set()
        def _rec(c):
            for o in c.objects:
                result.add(o)
            for ch in c.children:
                _rec(ch)
        _rec(coll)
        return list(result)

    # Use target_objects if provided, otherwise collect from scope
    if target_objects is not None:
        objs = target_objects
    else:
        objs = collect(scope)
    
    for obj in objs:
        bml_type = get_bml_type(obj)
        if target in {"SWITCH", "BOTH"} and bml_type == BlenderNodeType.SWITCH:
            idx = getattr(obj, "switch_list_index", -1)
            if 0 <= idx < len(switches_enum):
                sw = switches_enum[idx]
                obj.bml_switch_number = sw.switch_number
                obj.bml_switch_branch = sw.branch
                update_switch_or_dof_name(obj, context)
                processed_switches += 1
        if target in {"DOF", "BOTH"} and bml_type == BlenderNodeType.DOF:
            idx = getattr(obj, "dof_list_index", -1)
            if 0 <= idx < len(dofs_enum):
                de = dofs_enum[idx]
                obj.bml_dof_number = de.dof_number
                update_switch_or_dof_name(obj, context)
                processed_dofs += 1
    return processed_switches, processed_dofs


def assign_persistent_ids_to_objects(context, objects):
    """
    Assign persistent IDs to specific objects only.
    
    Returns (switches_assigned, dofs_assigned) counts.
    Used by validation dialogs for targeted assignment.
    """
    return _batch_reassign(context, "SCENE", "BOTH", target_objects=objects)


class BML_OT_reassign_switches_scene(bpy.types.Operator):
    bl_idname = "bml.reassign_switches_scene"
    bl_label = "Re-Assign All Switches (Scene)"
    bl_description = (
        "Batch assign persistent IDs for every SWITCH in the entire scene "
        "from its switch_list_index."
    )
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        ps, _ = _batch_reassign(context, "SCENE", "SWITCH")
        self.report({'INFO'}, f"Re-assigned {ps} switches (scene)")
        return {'FINISHED'}


class BML_OT_reassign_switches_collection(bpy.types.Operator):
    bl_idname = "bml.reassign_switches_collection"
    bl_label = "Re-Assign All Switches (Active Collection)"
    bl_description = (
        "Batch assign persistent IDs for every SWITCH in active collection (recursive) "
        "from their switch_list_index."
    )
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        ps, _ = _batch_reassign(context, "ACTIVE_COLLECTION", "SWITCH")
        self.report({'INFO'}, f"Re-assigned {ps} switches (active collection)")
        return {'FINISHED'}


class BML_OT_reassign_dofs_scene(bpy.types.Operator):
    bl_idname = "bml.reassign_dofs_scene"
    bl_label = "Re-Assign All DOFs (Scene)"
    bl_description = (
        "Batch assign persistent ID for every DOF in the entire scene from its dof_list_index."
    )
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        _, pd = _batch_reassign(context, "SCENE", "DOF")
        self.report({'INFO'}, f"Re-assigned {pd} DOFs (scene)")
        return {'FINISHED'}


class BML_OT_reassign_dofs_collection(bpy.types.Operator):
    bl_idname = "bml.reassign_dofs_collection"
    bl_label = "Re-Assign All DOFs (Active Collection)"
    bl_description = (
        "Batch assign persistent ID for DOFs under the active collection (recursive) from dof_list_index."
    )
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        _, pd = _batch_reassign(context, "ACTIVE_COLLECTION", "DOF")
        self.report({'INFO'}, f"Re-assigned {pd} DOFs (active collection)")
        return {'FINISHED'}


class BML_OT_assign_switch_popup(bpy.types.Operator):
    # Popup to choose scope for assigning switch persistent IDs.
    bl_idname = "bml.assign_switch_popup"
    bl_label = "Assign Switch IDs"
    bl_description = (
        "Assign persistent IDs for switch(es)."
    )

    def invoke(self, context, event):
        def draw_fn(self_, ctx):
            self_.layout.label(text="Assign persistent Switch IDs:")
            col = self_.layout.column(align=True)
            col.operator("bml.assign_switch_from_index", text="This Switch Only", icon='OBJECT_DATA')
            col.operator("bml.reassign_switches_scene", icon='SEQUENCE_COLOR_04')
            col.operator("bml.reassign_switches_collection", icon='SEQUENCE_COLOR_02')
            self_.layout.separator()
            self_.layout.label(text="Esc or click outside to cancel")
        context.window_manager.popup_menu(draw_fn, title="Switch ID Assignment", icon='OUTLINER_OB_EMPTY')
        return {'FINISHED'}


class BML_OT_assign_dof_popup(bpy.types.Operator):
    # Popup to choose scope for assigning DOF persistent IDs.
    bl_idname = "bml.assign_dof_popup"
    bl_label = "Assign DOF IDs"
    bl_description = (
        "Assign persistent IDs for DOF(s)."
    )

    def invoke(self, context, event):
        def draw_fn(self_, ctx):
            self_.layout.label(text="Assign persistent DOF IDs:")
            col = self_.layout.column(align=True)
            col.operator("bml.assign_dof_from_index", text="This DOF Only", icon='EMPTY_ARROWS')
            col.operator("bml.reassign_dofs_scene", icon='SEQUENCE_COLOR_04')
            col.operator("bml.reassign_dofs_collection", icon='SEQUENCE_COLOR_02')
            self_.layout.separator()
            self_.layout.label(text="Esc or click outside to cancel")
        context.window_manager.popup_menu(draw_fn, title="DOF ID Assignment", icon='EMPTY_ARROWS')
        return {'FINISHED'}


def register():
    bpy.utils.register_class(BML_OT_assign_switch_from_index)
    bpy.utils.register_class(BML_OT_assign_dof_from_index)
    bpy.utils.register_class(BML_OT_reassign_all_ids)
    bpy.utils.register_class(BML_OT_reassign_switches_scene)
    bpy.utils.register_class(BML_OT_reassign_switches_collection)
    bpy.utils.register_class(BML_OT_reassign_dofs_scene)
    bpy.utils.register_class(BML_OT_reassign_dofs_collection)
    bpy.utils.register_class(BML_OT_assign_switch_popup)
    bpy.utils.register_class(BML_OT_assign_dof_popup)


def unregister():
    bpy.utils.unregister_class(BML_OT_assign_dof_popup)
    bpy.utils.unregister_class(BML_OT_assign_switch_popup)
    bpy.utils.unregister_class(BML_OT_reassign_dofs_collection)
    bpy.utils.unregister_class(BML_OT_reassign_dofs_scene)
    bpy.utils.unregister_class(BML_OT_reassign_switches_collection)
    bpy.utils.unregister_class(BML_OT_reassign_switches_scene)
    bpy.utils.unregister_class(BML_OT_reassign_all_ids)
    bpy.utils.unregister_class(BML_OT_assign_dof_from_index)
    bpy.utils.unregister_class(BML_OT_assign_switch_from_index)

from math import floor, log

import bpy

from bms_blender_plugin.common.blender_types import BlenderNodeType
from bms_blender_plugin.common.util import get_bml_type
from bms_blender_plugin.ui_tools.panels.base_panel import BasePanel


class StatisticsPanel(BasePanel, bpy.types.Panel):
    """The 'Statistics' panel - keeping it open might be expensive, so have it closed by default"""
    bl_label = "Statistics"
    bl_idname = "BML_PT_Statistics"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def human_format(cls, number):
        """Formats big numbers with suffixes (K, M, ...)"""
        """source https://stackoverflow.com/questions/579310/formatting-long-numbers-as-strings"""
        if not number or number == 0:
            return 0
        elif number < 1000:
            return str(number)

        units = ["", "K", "M", "G", "T", "P"]
        k = 1000.0
        magnitude = int(floor(log(number, k)))
        return "%.2f%s" % (number / k**magnitude, units[magnitude])

    @classmethod
    def get_draw_calls(cls, collection):
        materials = set()
        unmerged_objects = 0
        bbl_lights_present = False

        def _parse_collection_recursive(coll):
            nonlocal materials
            nonlocal unmerged_objects
            nonlocal bbl_lights_present

            if coll.hide_render:
                return

            for obj in coll.objects:
                if obj.hide_render:
                    continue
                if len(obj.material_slots) > 0:
                    materials.add(obj.material_slots[0].name)
                else:
                    materials.add("Default Material")

                if obj.bml_do_not_merge:
                    unmerged_objects += 1
                if get_bml_type(obj) == BlenderNodeType.PBR_LIGHT:
                    bbl_lights_present = True
                if get_bml_type(obj) == BlenderNodeType.DOF or get_bml_type(obj) == BlenderNodeType.SWITCH:
                    unmerged_objects += 1

            for child in coll.children:
                _parse_collection_recursive(child)

        _parse_collection_recursive(collection)

        draw_calls = len(materials) + unmerged_objects
        if bbl_lights_present:
            draw_calls += 1

        return draw_calls

    @classmethod
    def get_triangles(cls, collection):
        triangles = 0
        if collection.hide_render:
            return 0

        for coll_obj in collection.objects:
            triangles += cls.get_triangles_for_object_recursive(coll_obj)

        for child in collection.children:
            triangles += cls.get_triangles(child)

        return triangles

    @classmethod
    def get_triangles_for_object_recursive(cls, obj):
        triangles = 0
        if obj.hide_render:
            return 0

        if obj.type == "MESH":
            obj.data.calc_loop_triangles()
            triangles += len(obj.data.loop_triangles)
        elif get_bml_type(obj) == BlenderNodeType.PBR_LIGHT:
            triangles += 2
        for obj_child in obj.children:
            triangles += cls.get_triangles_for_object_recursive(obj_child)

        return triangles

    @classmethod
    def poll(cls, context):
        return context.view_layer.active_layer_collection.collection

    def draw(self, context):
        layout = self.layout
        active_object = context.active_object
        active_collection = context.view_layer.active_layer_collection.collection

        if active_object:
            row = layout.row()
            row.label(text=f"Object {active_object.name}")
            box = layout.box()
            row = box.row()
            col = row.column()
            vertices = StatisticsPanel.human_format(
                StatisticsPanel.get_triangles_for_object_recursive(active_object) * 3
            )
            col.label(text="Vertices")
            col = row.column()
            col.label(text=f"{vertices}")
            layout.separator()

        row = layout.row()
        row.label(text=f"Collection {active_collection.name}")
        box = layout.box()
        row = box.row()
        col = row.column()
        draw_calls = StatisticsPanel.get_draw_calls(active_collection)
        col.label(text="Estimated draw calls")
        col = row.column()
        col.label(text=f"{draw_calls}")
        row = box.row()

        col = row.column()
        vertices = StatisticsPanel.human_format(
            StatisticsPanel.get_triangles(active_collection) * 3
        )
        col.label(text="Vertices")
        col = row.column()
        col.label(text=f"{vertices}")


def register():
    bpy.utils.register_class(StatisticsPanel)


def unregister():
    bpy.utils.unregister_class(StatisticsPanel)

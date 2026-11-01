from math import floor, log
from time import strftime

import bpy
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, IntProperty, PointerProperty, StringProperty
from bpy_extras.io_utils import ExportHelper

from bms_blender_plugin.common.statistics import (
    build_usage_report, calculate_statistics, collection_objects, object_subtree,
    print_usage_report, write_usage_xml,
)
from bms_blender_plugin.ui_tools.panels.base_panel import BasePanel


REPORT_KINDS = [('SWITCH', 'Switches', 'Switch usage'), ('DOF', 'DOFs', 'DOF usage')]


def active_collection(context):
    return context.view_layer.active_layer_collection.collection


class StatisticsSnapshot(bpy.types.PropertyGroup):
    scene: PointerProperty(type=bpy.types.Scene)
    view_layer_name: StringProperty()
    collection: PointerProperty(type=bpy.types.Collection)
    object: PointerProperty(type=bpy.types.Object)
    include_hidden: BoolProperty()
    triangles: IntProperty()
    vertices: IntProperty()
    draw_calls: IntProperty()
    calculated_at: StringProperty()


class CalculateStatistics(bpy.types.Operator):
    bl_idname = 'bml.calculate_statistics'
    bl_label = 'Calculate Statistics'
    bl_description = 'Calculate a snapshot; click again to reflect later edits'
    scope: EnumProperty(items=[('OBJECT', 'Object', ''), ('COLLECTION', 'Collection', ''), ('SCENE', 'Scene', '')])

    def execute(self, context):
        if self.scope == 'OBJECT' and not context.active_object:
            self.report({'WARNING'}, 'Select an object first')
            return {'CANCELLED'}
        include_hidden = context.window_manager.bml_statistics_include_hidden
        target = (context.active_object if self.scope == 'OBJECT' else
                  active_collection(context) if self.scope == 'COLLECTION' else context.scene)
        objects = (object_subtree(target, include_hidden, context.view_layer) if self.scope == 'OBJECT' else
                   collection_objects(target if self.scope == 'COLLECTION' else target.collection,
                                      include_hidden, context.view_layer))
        values = calculate_statistics(objects)
        snapshot = getattr(context.window_manager, 'bml_statistics_' + self.scope.lower())
        for key, value in values.items():
            setattr(snapshot, key, value)
        snapshot.scene = context.scene
        snapshot.view_layer_name = context.view_layer.name
        snapshot.collection = target if self.scope == 'COLLECTION' else None
        snapshot.object = target if self.scope == 'OBJECT' else None
        snapshot.include_hidden = include_hidden
        snapshot.calculated_at = strftime('%H:%M:%S')
        return {'FINISHED'}


class PrintUsageReport(bpy.types.Operator):
    bl_idname = 'bml.print_usage_report'
    bl_label = 'Print Collection Usage'
    bl_description = 'Print one line per control with its ID, branch and scoped child counts to the system console'
    kind: EnumProperty(items=REPORT_KINDS)

    def execute(self, context):
        report = build_usage_report(active_collection(context), self.kind,
                                    context.window_manager.bml_statistics_include_hidden, context.view_layer)
        print_usage_report(report)
        self.report({'INFO'}, f"Printed {len(report['controls'])} {self.kind} objects to the system console")
        return {'FINISHED'}


class ExportUsageReport(bpy.types.Operator, ExportHelper):
    bl_idname = 'bml.export_usage_report'
    bl_label = 'Export Collection Usage XML'
    bl_description = 'Export IDs, branches, child counts and the full child hierarchy within this collection'
    filename_ext = '.xml'
    filter_glob: StringProperty(default='*.xml', options={'HIDDEN'})
    kind: EnumProperty(items=REPORT_KINDS)
    collection_name: StringProperty(options={'HIDDEN'})
    source_scene_name: StringProperty(options={'HIDDEN'})
    is_scene_collection: BoolProperty(options={'HIDDEN'})
    include_hidden: BoolProperty(name='Include Hidden Objects', default=False)

    def invoke(self, context, event):
        self.collection_name = active_collection(context).name
        self.source_scene_name = context.scene.name
        self.is_scene_collection = active_collection(context) == context.scene.collection
        self.include_hidden = context.window_manager.bml_statistics_include_hidden
        self.filepath = bpy.path.clean_name(self.collection_name) + '_' + self.kind.lower() + '_usage.xml'
        return super().invoke(context, event)

    def execute(self, context):
        if self.is_scene_collection:
            scene = bpy.data.scenes.get(self.source_scene_name)
            collection = scene.collection if scene else None
        else:
            collection = (bpy.data.collections.get(self.collection_name) if self.collection_name
                          else active_collection(context))
        if collection is None:
            self.report({'ERROR'}, 'The report collection no longer exists')
            return {'CANCELLED'}
        try:
            report = build_usage_report(collection, self.kind, self.include_hidden, context.view_layer)
            write_usage_xml(report, self.filepath)
        except (OSError, ValueError) as error:
            self.report({'ERROR'}, f'Could not write usage report: {error}')
            return {'CANCELLED'}
        self.report({'INFO'}, f"Exported {len(report['controls'])} {self.kind} objects to {self.filepath}")
        return {'FINISHED'}


class UsageTreeRow(bpy.types.PropertyGroup):
    object_name: StringProperty()
    details: StringProperty()
    depth: IntProperty()
    parent_index: IntProperty(default=-1)
    has_children: BoolProperty()
    expanded: BoolProperty(default=False)


class BML_UL_usage_tree(bpy.types.UIList):
    def draw_filter(self, context, layout):
        layout.prop(self, 'filter_name', text='', icon='VIEWZOOM')

    def filter_items(self, context, data, propname):
        rows = getattr(data, propname)
        visible = []
        for item in rows:
            visible.append(item.parent_index < 0 or
                           (visible[item.parent_index] and rows[item.parent_index].expanded))
        query = self.filter_name.casefold().strip()
        if query:
            visible = [query in (item.object_name + ' ' + item.details).casefold() for item in rows]
            # Matching descendants reveal their ancestors even when those rows are collapsed.
            for index in range(len(rows) - 1, -1, -1):
                parent = rows[index].parent_index
                if visible[index] and parent >= 0:
                    visible[parent] = True
        return [self.bitflag_filter_item if value else 0 for value in visible], []

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        if item.depth:
            row.separator(factor=min(item.depth, 20))
        if item.has_children:
            row.prop(item, 'expanded', text='', emboss=False,
                     icon='TRIA_DOWN' if item.expanded else 'TRIA_RIGHT')
        else:
            row.label(text='', icon='BLANK1')
        row.label(text=item.object_name, icon='OUTLINER_OB_EMPTY' if item.depth == 0 else 'OBJECT_DATA')
        row.label(text=item.details)


class SelectUsageObject(bpy.types.Operator):
    bl_idname = 'bml.select_usage_object'
    bl_label = 'Select Object'
    bl_description = 'Select this report object in the current view layer'
    bl_options = {'UNDO'}
    object_name: StringProperty()

    def execute(self, context):
        obj = context.view_layer.objects.get(self.object_name)
        if obj is None or obj.hide_get() or obj.hide_select or not obj.visible_get():
            self.report({'WARNING'}, 'Object is hidden, excluded, deleted, or not selectable in this view layer')
            return {'CANCELLED'}
        for selected in context.selected_objects:
            selected.select_set(False)
        obj.select_set(True)
        context.view_layer.objects.active = obj
        return {'FINISHED'}


class BrowseUsageReport(bpy.types.Operator):
    bl_idname = 'bml.browse_usage_report'
    bl_label = 'Collection Usage Browser'
    bl_description = 'Build an expandable tree of controls and their children within this collection'
    kind: EnumProperty(items=REPORT_KINDS)
    rows: CollectionProperty(type=UsageTreeRow)
    active_index: IntProperty(default=0)
    collection_name: StringProperty()
    control_count: IntProperty()
    include_hidden: BoolProperty()

    def invoke(self, context, event):
        report = build_usage_report(active_collection(context), self.kind,
                                    context.window_manager.bml_statistics_include_hidden, context.view_layer)
        self.collection_name = report['collection']
        self.control_count = len(report['controls'])
        self.include_hidden = report['include_hidden']
        self.rows.clear()
        self.active_index = 0
        pending = [(entry, 0, -1) for entry in reversed(report['controls'])]
        while pending:
            entry, depth, parent_index = pending.pop()
            index = len(self.rows)
            row = self.rows.add()
            row.object_name = entry['name']
            row.depth = depth
            row.parent_index = parent_index
            row.has_children = bool(entry['children'])
            if depth == 0:
                number = entry['number'] if entry['number'] is not None else 'unresolved'
                branch = f" / branch {entry['branch']}" if self.kind == 'SWITCH' else ''
                row.details = (f"#{number}{branch} | {entry['child_count']} children, "
                               f"{entry['descendant_count']} descendants")
            else:
                row.details = entry['object_type']
            if entry['hide_render']:
                row.details += ' | hidden from render'
            if entry['hide_viewport'] or entry['hide_eye']:
                row.details += ' | hidden in viewport'
            if depth and entry['parent'] != self.rows[parent_index].object_name:
                row.details += ' | parent: ' + entry['parent']
            pending.extend((child, depth + 1, index) for child in reversed(entry['children']))
        return context.window_manager.invoke_props_dialog(self, width=900)

    def draw(self, context):
        layout = self.layout
        layout.label(text=f'{self.collection_name}: {self.control_count} {self.kind} objects')
        layout.label(text='Selected collection and subcollections only. Hidden objects: ' +
                     ('included' if self.include_hidden else 'excluded'))
        if not self.rows:
            layout.label(text='No matching controls in this collection or its subcollections.')
            return
        layout.template_list('BML_UL_usage_tree', '', self, 'rows', self, 'active_index', rows=16)
        if 0 <= self.active_index < len(self.rows):
            item = self.rows[self.active_index]
            layout.label(text=item.object_name + ': ' + item.details)
            layout.operator(SelectUsageObject.bl_idname).object_name = item.object_name

    def execute(self, context):
        return {'FINISHED'}


class StatisticsPanel(BasePanel, bpy.types.Panel):
    """Only display snapshots; geometry and hierarchy work always requires a button."""
    bl_label = 'Statistics'
    bl_idname = 'BML_PT_Statistics'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def human_format(cls, number):
        if number < 1000:
            return str(number)
        units = ['', 'K', 'M', 'G', 'T', 'P']
        magnitude = min(int(floor(log(number, 1000))), len(units) - 1)
        return '%.2f%s' % (number / 1000 ** magnitude, units[magnitude])

    @classmethod
    def get_draw_calls(cls, collection):
        return calculate_statistics(collection_objects(collection))['draw_calls']

    @classmethod
    def get_triangles(cls, collection):
        return calculate_statistics(collection_objects(collection))['triangles']

    @classmethod
    def get_triangles_for_object_recursive(cls, obj):
        return calculate_statistics(object_subtree(obj))['triangles']

    @classmethod
    def poll(cls, context):
        return context.view_layer is not None

    def draw(self, context):
        layout = self.layout
        include_hidden = context.window_manager.bml_statistics_include_hidden
        layout.prop(context.window_manager, 'bml_statistics_include_hidden')
        layout.label(text='Snapshots: calculate again after edits.', icon='INFO')
        targets = [('OBJECT', context.active_object), ('COLLECTION', active_collection(context)),
                   ('SCENE', context.scene)]
        for scope, target in targets:
            if target is None:
                continue
            box = layout.box()
            box.label(text=f'{scope.title()}: {target.name}')
            box.operator(CalculateStatistics.bl_idname, text='Calculate ' + scope.title()).scope = scope
            snapshot = getattr(context.window_manager, 'bml_statistics_' + scope.lower())
            matches = (snapshot.scene == context.scene and snapshot.include_hidden == include_hidden
                       and snapshot.view_layer_name == context.view_layer.name)
            if scope == 'OBJECT':
                matches = matches and snapshot.object == target
            elif scope == 'COLLECTION':
                matches = matches and snapshot.collection == target
            if matches and snapshot.calculated_at:
                box.label(text='Calculated at ' + snapshot.calculated_at)
                for label, value in [('Triangles', snapshot.triangles), ('Triangle vertices', snapshot.vertices),
                                     ('Estimated draw calls', snapshot.draw_calls)]:
                    box.label(text=f'{label}: {StatisticsPanel.human_format(value)}')
        layout.label(text='Collection usage (includes subcollections)')
        layout.label(text='Child counts follow collection and visibility filters.')
        for kind, label, _ in REPORT_KINDS:
            box = layout.box()
            box.label(text=label)
            box.operator(PrintUsageReport.bl_idname, text='Print List to Console', icon='CONSOLE').kind = kind
            box.operator(ExportUsageReport.bl_idname, text='Export XML Report', icon='EXPORT').kind = kind
            box.operator(BrowseUsageReport.bl_idname, text='Browse Child Tree', icon='OUTLINER').kind = kind


CLASSES = (StatisticsSnapshot, CalculateStatistics, PrintUsageReport, ExportUsageReport,
           UsageTreeRow, BML_UL_usage_tree, SelectUsageObject, BrowseUsageReport, StatisticsPanel)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    for scope in ('object', 'collection', 'scene'):
        setattr(bpy.types.WindowManager, 'bml_statistics_' + scope,
                PointerProperty(type=StatisticsSnapshot, options={'SKIP_SAVE'}))
    bpy.types.WindowManager.bml_statistics_include_hidden = BoolProperty(
        name='Include Hidden Objects', default=False, options={'SKIP_SAVE'},
        description='Include objects hidden in viewport or render, and hidden or excluded collections')


def unregister():
    del bpy.types.WindowManager.bml_statistics_include_hidden
    for scope in ('object', 'collection', 'scene'):
        delattr(bpy.types.WindowManager, 'bml_statistics_' + scope)
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)

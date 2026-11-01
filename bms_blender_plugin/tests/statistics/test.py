"""Run with Blender: blender --background --factory-startup --python-exit-code 1 --python tests/statistics/test.py."""
import importlib
import io
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
import tempfile
from time import perf_counter
import xml.etree.ElementTree as ET
from unittest.mock import patch

import bpy

# Load the feature without the addon's unrelated registration side effects.
root = Path(__file__).resolve().parents[2]
package = ModuleType('bms_blender_plugin')
package.__path__ = [str(root)]
sys.modules[package.__name__] = package
panel = importlib.import_module('bms_blender_plugin.ui_tools.panels.statistics_panel')
stats = importlib.import_module('bms_blender_plugin.common.statistics')


class Layout:
    def __getattr__(self, name):
        return lambda *args, **kwargs: self


class StatisticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bpy.types.Object.bml_type = bpy.props.StringProperty(default='none')
        bpy.types.Object.bml_do_not_merge = bpy.props.BoolProperty()
        for key in ('bml_dof_number', 'bml_switch_number', 'bml_switch_branch'):
            setattr(bpy.types.Object, key, bpy.props.IntProperty(default=-1))
        panel.register()
        bpy.types.WindowManager.bml_test_usage_rows = bpy.props.CollectionProperty(type=panel.UsageTreeRow)

    @classmethod
    def tearDownClass(cls):
        del bpy.types.WindowManager.bml_test_usage_rows
        panel.unregister()
        for key in ('bml_type', 'bml_do_not_merge', 'bml_dof_number', 'bml_switch_number', 'bml_switch_branch'):
            delattr(bpy.types.Object, key)

    def setUp(self):
        for obj in list(bpy.data.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        for coll in list(bpy.data.collections):
            bpy.data.collections.remove(coll)
        self.collection = bpy.data.collections.new('Export collection')
        bpy.context.scene.collection.children.link(self.collection)
        self.subcollection = bpy.data.collections.new('Subcollection')
        self.collection.children.link(self.subcollection)
        self.outside = bpy.data.collections.new('Dead objects')
        bpy.context.scene.collection.children.link(self.outside)
        bpy.context.view_layer.update()
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[self.collection.name]
        bpy.context.window_manager.bml_statistics_include_hidden = False

    def object(self, name, collection=None, parent=None, kind='none', number=-1, branch=-1, mesh=False):
        data = None
        if mesh:
            data = bpy.data.meshes.new(name + ' mesh')
            data.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [], [(0, 1, 2, 3)])
        obj = bpy.data.objects.new(name, data)
        (collection or self.collection).objects.link(obj)
        obj.parent = parent
        obj.bml_type = kind
        obj.bml_dof_number = number
        obj.bml_switch_number = number
        obj.bml_switch_branch = branch
        bpy.context.view_layer.update()
        return obj

    def test_redraw_does_not_calculate_statistics(self):
        obj = self.object('Selected', mesh=True)
        bpy.context.view_layer.objects.active = obj
        context = bpy.context
        view = SimpleNamespace(layout=Layout())
        with patch.object(panel.StatisticsPanel, 'get_triangles_for_object_recursive',
                          side_effect=AssertionError('Redraw traversed object geometry')), \
             patch.object(panel.StatisticsPanel, 'get_triangles',
                          side_effect=AssertionError('Redraw traversed collection geometry')), \
             patch.object(panel.StatisticsPanel, 'get_draw_calls',
                          side_effect=AssertionError('Redraw traversed collection objects')), \
             patch.object(panel, 'calculate_statistics', side_effect=AssertionError('Redraw calculated statistics')), \
             patch.object(panel, 'collection_objects', side_effect=AssertionError('Redraw scanned collection')), \
             patch.object(panel, 'build_usage_report', side_effect=AssertionError('Redraw built usage report')):
            start = perf_counter()
            for _ in range(100):
                panel.StatisticsPanel.draw(view, context)
            print(f'100 panel redraws: {perf_counter() - start:.4f}s; no geometry or report calculations')

    def test_counts_unique_objects_without_following_out_of_scope_children(self):
        parent = self.object('Parent DOF', kind='dof', number=7)
        mesh = self.object('Child mesh', parent=parent, mesh=True)
        self.subcollection.objects.link(mesh)
        self.object('Outside mesh', self.outside, parent=parent, mesh=True)
        self.object('Nested mesh', self.subcollection, parent=mesh, mesh=True)
        result = stats.calculate_statistics(stats.collection_objects(self.collection))
        self.assertEqual(result['triangles'], 4)
        self.assertEqual(result['vertices'], 12)
        self.assertEqual(result['draw_calls'], 2)

    def test_hidden_filters_and_defaults(self):
        visible = self.object('Visible', kind='dof', number=1)
        render_hidden = self.object('Render hidden', kind='dof', number=2)
        render_hidden.hide_render = True
        viewport_hidden = self.object('Viewport hidden', kind='dof', number=3)
        viewport_hidden.hide_viewport = True
        eye_hidden = self.object('Eye hidden', kind='dof', number=4)
        eye_hidden.hide_set(True)
        self.object('Excluded collection', self.subcollection, kind='dof', number=5)
        layer = bpy.context.view_layer.layer_collection.children[self.collection.name]
        layer.children[self.subcollection.name].exclude = True
        report = stats.build_usage_report(self.collection, 'DOF')
        self.assertEqual([item['name'] for item in report['controls']], [visible.name])
        all_report = stats.build_usage_report(self.collection, 'DOF', include_hidden=True)
        self.assertEqual(len(all_report['controls']), 5)
        self.assertFalse(bpy.context.window_manager.bml_statistics_include_hidden)

    def test_hidden_collection_excludes_children(self):
        self.object('Nested', self.subcollection, kind='switch', number=1, branch=0)
        for attr in ('hide_render', 'hide_viewport'):
            setattr(self.subcollection, attr, True)
            self.assertEqual(stats.build_usage_report(self.collection, 'SWITCH')['controls'], [])
            self.assertEqual(len(stats.build_usage_report(self.collection, 'SWITCH', True)['controls']), 1)
            setattr(self.subcollection, attr, False)

    def test_visible_descendant_of_hidden_parent_remains_in_report(self):
        control = self.object('Root', kind='dof', number=1)
        hidden = self.object('Hidden intermediary', parent=control)
        hidden.hide_render = True
        self.object('Visible grandchild', parent=hidden)
        entry = stats.build_usage_report(self.collection, 'DOF')['controls'][0]
        self.assertEqual(entry['child_count'], 0)
        self.assertEqual(entry['descendant_count'], 1)
        self.assertEqual(entry['children'][0]['name'], 'Visible grandchild')
        self.assertEqual(entry['children'][0]['parent'], hidden.name)

    def test_hidden_path_does_not_leak_from_a_visible_collection_link(self):
        self.object('Shared object', self.subcollection, kind='dof', number=1)
        self.outside.children.link(self.subcollection)
        layer = bpy.context.view_layer.layer_collection.children[self.collection.name]
        layer.children[self.subcollection.name].hide_viewport = True
        self.assertEqual(stats.build_usage_report(self.collection, 'DOF')['controls'], [])
        self.assertEqual(len(stats.build_usage_report(self.outside, 'DOF')['controls']), 1)

    def test_switch_usage_scope_ids_counts_and_xml(self):
        parent = self.object('Switch <7> & "open"', kind='switch', number=7, branch=2)
        child = self.object('Child <&>', parent=parent)
        self.object('Grandchild', self.subcollection, parent=child)
        hidden = self.object('Hidden child', parent=parent)
        hidden.hide_render = True
        self.object('Outside child', self.outside, parent=parent)
        self.object('Outside switch', self.outside, kind='switch', number=99, branch=0)
        self.object('Empty switch', kind='switch', number=8, branch=1)
        self.object('Unresolved switch', kind='switch')
        report = stats.build_usage_report(self.collection, 'SWITCH')
        self.assertEqual(len(report['controls']), 3)
        entry = report['controls'][0]
        self.assertEqual((entry['number'], entry['branch'], entry['child_count'], entry['descendant_count']), (7, 2, 1, 2))
        self.assertEqual(report['controls'][1]['child_count'], 0)
        self.assertIsNone(report['controls'][2]['number'])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'report.xml'
            stats.write_usage_xml(report, path)
            root = ET.parse(path).getroot()
            self.assertEqual(root.get('include_hidden'), 'false')
            self.assertEqual(root[0].get('name'), parent.name)
            self.assertEqual(root[0][0].get('name'), child.name)
            self.assertEqual(root[0][0][0].get('name'), 'Grandchild')
            self.assertNotIn('Outside child', path.read_text())
        output = io.StringIO()
        with patch('sys.stdout', output):
            stats.print_usage_report(report)
        lines = [line for line in output.getvalue().splitlines() if line.startswith('SWITCH ')]
        self.assertEqual(len(lines), 4)  # Header plus one line per control.
        self.assertIn('branch=2', lines[1])
        self.assertIn('children=1 descendants=2', lines[1])

    def test_calculate_operator_stores_snapshot_and_respects_visibility(self):
        obj = self.object('Quad', mesh=True)
        hidden = self.object('Hidden quad', mesh=True)
        hidden.hide_render = True
        bpy.context.view_layer.objects.active = obj
        for scope in ('OBJECT', 'COLLECTION', 'SCENE'):
            self.assertEqual(bpy.ops.bml.calculate_statistics(scope=scope), {'FINISHED'})
            result = getattr(bpy.context.window_manager, 'bml_statistics_' + scope.lower())
            self.assertEqual(result.triangles, 2)
            self.assertEqual(result.vertices, 6)
            self.assertFalse(result.include_hidden)
            self.assertTrue(result.calculated_at)
        bpy.context.window_manager.bml_statistics_include_hidden = True
        bpy.ops.bml.calculate_statistics(scope='COLLECTION')
        self.assertEqual(bpy.context.window_manager.bml_statistics_collection.triangles, 4)

    def test_browser_builds_expandable_snapshot_without_recalculating_on_draw(self):
        parent = self.object('Root DOF', kind='dof', number=42)
        child = self.object('Child', parent=parent)
        self.object('Grandchild', parent=child)
        self.object('Empty DOF', kind='dof', number=43)
        rows = bpy.context.window_manager.bml_test_usage_rows
        operator = SimpleNamespace(rows=rows, kind='DOF')
        manager = SimpleNamespace(bml_statistics_include_hidden=False,
                                  invoke_props_dialog=lambda *args, **kwargs: {'RUNNING_MODAL'})
        context = SimpleNamespace(window_manager=manager, view_layer=bpy.context.view_layer)
        self.assertEqual(panel.BrowseUsageReport.invoke(operator, context, None), {'RUNNING_MODAL'})
        self.assertEqual(operator.control_count, 2)
        self.assertEqual([row.depth for row in operator.rows], [0, 1, 2, 0])
        list_view = SimpleNamespace(bitflag_filter_item=1, filter_name='')
        flags, _ = panel.BML_UL_usage_tree.filter_items(list_view, context, operator, 'rows')
        self.assertEqual(flags, [1, 0, 0, 1])
        list_view.filter_name = 'grandchild'
        flags, _ = panel.BML_UL_usage_tree.filter_items(list_view, context, operator, 'rows')
        self.assertEqual(flags, [1, 1, 1, 0])
        list_view.filter_name = ''
        operator.rows[0].expanded = True
        operator.rows[1].expanded = True
        flags, _ = panel.BML_UL_usage_tree.filter_items(list_view, context, operator, 'rows')
        self.assertEqual(flags, [1, 1, 1, 1])
        operator.rows[0].expanded = False
        flags, _ = panel.BML_UL_usage_tree.filter_items(list_view, context, operator, 'rows')
        self.assertEqual(flags, [1, 0, 0, 1])
        with patch.object(panel, 'build_usage_report', side_effect=AssertionError('Dialog redrew scene')):
            view = SimpleNamespace(layout=Layout(), rows=operator.rows, active_index=0,
                                   collection_name=operator.collection_name, control_count=2,
                                   kind='DOF', include_hidden=False)
            panel.BrowseUsageReport.draw(view, context)

    def test_xml_operator_keeps_requested_collection_and_hidden_filter(self):
        self.object('Scoped DOF', kind='dof', number=3)
        hidden = self.object('Hidden DOF', kind='dof', number=4)
        hidden.hide_render = True
        self.object('Dead DOF', self.outside, kind='dof', number=99)
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[self.outside.name]
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / 'operator_report.xml')
            result = bpy.ops.bml.export_usage_report(
                filepath=path, collection_name=self.collection.name, kind='DOF')
            self.assertEqual(result, {'FINISHED'})
            root = ET.parse(path).getroot()
            self.assertEqual([entry.get('number') for entry in root], ['3'])
            bpy.ops.bml.export_usage_report(filepath=path, collection_name=self.collection.name,
                                            kind='DOF', include_hidden=True)
            root = ET.parse(path).getroot()
            self.assertEqual([entry.get('number') for entry in root], ['3', '4'])


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(StatisticsTests))
    if not result.wasSuccessful():
        raise RuntimeError('Statistics tests failed')

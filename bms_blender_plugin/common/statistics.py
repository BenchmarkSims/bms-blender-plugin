"""On-demand statistics and collection usage snapshots."""
from collections import defaultdict
from datetime import datetime
import xml.etree.ElementTree as ET

import bpy

from bms_blender_plugin.common.blender_types import BlenderNodeType
from bms_blender_plugin.common.resolve_ids import resolve_dof_number, resolve_switch_id
from bms_blender_plugin.common.util import get_bml_type


def collection_objects(collection, include_hidden=False, view_layer=None):
    """Yield unique members of the selected collection and its subcollections only."""
    view_layer = view_layer or bpy.context.view_layer
    visible_collections = set()
    if not include_hidden:
        root = view_layer.layer_collection
        pending = [(root, root.collection == collection)]
        while pending:
            layer, in_scope = pending.pop()
            coll = layer.collection
            if layer.exclude or layer.hide_viewport or coll.hide_render or coll.hide_viewport:
                continue
            if in_scope:
                visible_collections.add(coll)
            pending.extend((child, in_scope or child.collection == collection) for child in layer.children)
    pending = [collection]
    seen_collections, seen_objects = set(), set()
    while pending:
        coll = pending.pop()
        if coll in seen_collections or (not include_hidden and coll not in visible_collections):
            continue
        seen_collections.add(coll)
        pending.extend(coll.children)
        for obj in coll.objects:
            if obj in seen_objects:
                continue
            seen_objects.add(obj)
            if include_hidden or not (obj.hide_render or obj.hide_viewport or obj.hide_get(view_layer=view_layer)):
                yield obj


def filtered_child_map(members, scope):
    """Retain visible descendants behind omitted hidden parents, without crossing scope."""
    children = defaultdict(list)
    for obj in members:
        parent = obj.parent
        while parent in scope and parent not in members:
            parent = parent.parent
        if parent in members:
            children[parent].append(obj)
    return children


def object_subtree(obj, include_hidden=False, view_layer=None):
    """Object statistics are restricted to the current scene."""
    view_layer = view_layer or bpy.context.view_layer
    eligible = set(collection_objects(bpy.context.scene.collection, include_hidden, view_layer))
    children = filtered_child_map(eligible | {obj}, set(bpy.context.scene.collection.all_objects))
    pending = [obj]
    while pending:
        current = pending.pop()
        if current in eligible:
            yield current
        pending.extend(children[current])


def calculate_statistics(objects):
    triangles = 0
    materials = set()
    unmerged_objects = 0
    lights_present = False
    mesh_triangles = {}
    for obj in objects:
        bml_type = get_bml_type(obj)
        if obj.type == 'MESH':
            mesh = obj.data
            if mesh not in mesh_triangles:
                mesh.calc_loop_triangles()
                mesh_triangles[mesh] = len(mesh.loop_triangles)
            triangles += mesh_triangles[mesh]
        elif bml_type == BlenderNodeType.PBR_LIGHT:
            triangles += 2
        materials.add(obj.material_slots[0].name if obj.material_slots else 'Default Material')
        if obj.bml_do_not_merge:
            unmerged_objects += 1
        if bml_type in {BlenderNodeType.DOF, BlenderNodeType.SWITCH}:
            unmerged_objects += 1
        lights_present |= bml_type == BlenderNodeType.PBR_LIGHT
    return {'triangles': triangles, 'vertices': triangles * 3,
            'draw_calls': len(materials) + unmerged_objects + int(lights_present)}


def _object_details(obj, view_layer=None):
    bml_type = get_bml_type(obj)
    return {'name': obj.name, 'object_type': obj.type,
            'bml_type': str(bml_type) if bml_type else '',
            'parent': obj.parent.name if obj.parent else '',
            'hide_render': obj.hide_render, 'hide_viewport': obj.hide_viewport,
            'hide_eye': obj.hide_get(view_layer=view_layer or bpy.context.view_layer),
            'children': []}


def build_usage_report(collection, kind, include_hidden=False, view_layer=None):
    """Keep controls and descendants strictly within the collection's eligible members.

    Hidden objects and collections are excluded by default. Child counts refer to
    the filtered scope, and empty controls and unresolved IDs remain in the report.
    """
    wanted = BlenderNodeType(kind.lower())
    if wanted not in {BlenderNodeType.SWITCH, BlenderNodeType.DOF}:
        raise ValueError('Usage reports support switches and DOFs')
    members = set(collection_objects(collection, include_hidden, view_layer))
    children = filtered_child_map(members, set(collection.all_objects))
    controls = []
    for obj in members:
        if get_bml_type(obj) != wanted:
            continue
        number, branch = (resolve_switch_id(obj) if wanted == BlenderNodeType.SWITCH
                          else (resolve_dof_number(obj), None))
        entry = _object_details(obj, view_layer)
        entry.update(number=number, branch=branch,
                     child_count=sum(child.parent == obj for child in children[obj]), descendant_count=0)
        pending = [(obj, entry)]
        while pending:
            parent, parent_entry = pending.pop()
            for child in sorted(children[parent], key=lambda item: item.name.casefold()):
                child_entry = _object_details(child, view_layer)
                parent_entry['children'].append(child_entry)
                pending.append((child, child_entry))
                entry['descendant_count'] += 1
        controls.append(entry)
    controls.sort(key=lambda item: (
        item['number'] is None, item['number'] if item['number'] is not None else -1,
        item['branch'] if item['branch'] is not None else -1, item['name'].casefold()))
    return {'collection': collection.name, 'kind': kind.upper(), 'include_hidden': include_hidden,
            'generated': datetime.now().isoformat(timespec='seconds'), 'controls': controls}


def print_usage_report(report):
    print(f"\n{report['kind']} usage: {report['collection']} "
          f"({len(report['controls'])} objects; include_hidden={report['include_hidden']})")
    for control in report['controls']:
        number = control['number'] if control['number'] is not None else 'UNRESOLVED'
        branch = ''
        if report['kind'] == 'SWITCH':
            branch = f" branch={control['branch'] if control['branch'] is not None else 'UNRESOLVED'}"
        print(f"{report['kind']} {number}{branch} name={control['name']!r} "
              f"children={control['child_count']} descendants={control['descendant_count']}")


def write_usage_xml(report, filepath):
    root = ET.Element('bms_usage_report', {
        'collection': report['collection'], 'kind': report['kind'],
        'generated': report['generated'], 'control_count': str(len(report['controls'])),
        'include_hidden': str(report['include_hidden']).lower(),
        'scope': 'Selected collection and subcollections only; counts use the same visibility filter',
    })
    for control in report['controls']:
        element = ET.SubElement(root, report['kind'].lower(), {
            'name': control['name'],
            'number': str(control['number']) if control['number'] is not None else 'unresolved',
            'child_count': str(control['child_count']),
            'descendant_count': str(control['descendant_count']),
            'hide_render': str(control['hide_render']).lower(),
            'hide_viewport': str(control['hide_viewport']).lower(),
            'hide_eye': str(control['hide_eye']).lower(),
        })
        if report['kind'] == 'SWITCH':
            element.set('branch', str(control['branch']) if control['branch'] is not None else 'unresolved')
        pending = [(element, control)]
        while pending:
            parent_element, parent_entry = pending.pop()
            for child in parent_entry['children']:
                child_element = ET.SubElement(parent_element, 'object', {
                    key: str(child[key]).lower() if isinstance(child[key], bool) else child[key]
                    for key in ('name', 'object_type', 'bml_type', 'parent', 'hide_render', 'hide_viewport', 'hide_eye')
                })
                pending.append((child_element, child))
    ET.indent(root)
    ET.ElementTree(root).write(filepath, encoding='utf-8', xml_declaration=True)

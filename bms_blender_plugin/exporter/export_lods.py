import os
import struct

import bpy

from bms_blender_plugin.common.blender_types import BlenderNodeType
from bms_blender_plugin.common.bml_structs import (
    Compression,
    Header,
    SwitchEnd,
    DofEnd,
    SlotEnd,
    IndexBufferFormat,
)
from bms_blender_plugin.common.export_settings import ExportSettings
from bms_blender_plugin.common.util import (
    copy_collection_flat,
    apply_all_modifiers,
    compress_lz_4,
    compress_lzma,
    get_bml_type,
    force_auto_smoothing_on_object,
)
from bms_blender_plugin.exporter.export_materials import export_material_sets
from bms_blender_plugin.exporter.export_render_controls import get_render_control_nodes
from bms_blender_plugin.exporter.parser import (
    parse_mesh,
    parse_bbl_light,
    parse_slot,
    parse_switch,
    parse_dof,
    parse_hotspot,
)
from bms_blender_plugin.ui_tools.panels.material_sets_panel import revert_to_base_material_set


def export_lods(
    context, file_directory, file_prefix, lod_list, scale_factor, export_settings: ExportSettings
):
    """Exports multiple LODs to single *.bml files and their material sets to *.mti files.
    Returns a list of exported files, a list of all material names and
    a list of all hotspots."""
    all_exported_bmls = []
    all_material_names = set()
    all_hotspots = dict()
    for lod in lod_list:
        print(f"Exporting LOD {lod.collection.name}...\n")
        lod.file_suffix = lod.file_suffix.replace(" ", "_")
        bml_file_path = os.path.join(file_directory, file_prefix + lod.file_suffix + ".bml")

        material_names, hotspots = export_single_collection(
            context, lod.collection, scale_factor, export_settings, bml_file_path
        )

        material_set_filepath = bml_file_path.replace(".bml", ".mti")

        if export_settings.export_materials_sets:
            export_material_sets(context, material_set_filepath, material_names)

        all_exported_bmls.append(bml_file_path)

        for material_name in material_names:
            all_material_names.add(material_name)

        for hotspot in hotspots.values():
            if hotspot.callback_id not in all_hotspots.keys():
                all_hotspots[hotspot.callback_id] = hotspot
            else:
                raise Exception(f"Duplicate hotspot detected: {hotspot.name}")

    return all_exported_bmls, all_material_names, all_hotspots


def export_single_collection(
    context, collection, scale_factor, export_settings: ExportSettings, file_path
):
    """Exports a single Blender collection to a BML file."""
    # create a temporary collection and copy the current collection's visible objects into it
    collection_copy_root = bpy.data.collections.new(collection.name + "_export")
    bpy.context.scene.collection.children.link(collection_copy_root)
    copy_collection_flat(
        collection,
        collection_copy_root,
        [collection_copy_root],
        scale_factor,
    )

    apply_all_modifiers(collection_copy_root)

    # make sure we are on the base texture set
    revert_to_base_material_set(context, collection_copy_root)

    # get the data of the root collection
    nodes_output = get_nodes(
        context,
        collection_copy_root,
        export_settings.script,
        export_settings.auto_smooth_value,
    )
    payload = nodes_output["data"]
    material_names = nodes_output["material_names"]
    hotspots = nodes_output["hotspots"]

    payload_size = len(payload)

    if export_settings.compression == Compression.NONE:
        payload_compressed_size = payload_size
    elif export_settings.compression == Compression.LZ_4:
        payload = compress_lz_4(payload)
        payload_compressed_size = len(payload)
    elif export_settings.compression == Compression.LZMA:
        payload = compress_lzma(payload)
        payload_compressed_size = len(payload)
    else:
        raise Exception("Unknown compression exception")

    header = Header(
        2, payload_size, payload_compressed_size, export_settings.compression
    )
    data = header.to_data() + payload

    if export_settings.export_models:
        with open(file_path, "wb") as bml_file:
            bml_file.write(data)
            print(
                f"Finished exporting LOD with {nodes_output['nodes_amount']} nodes to {file_path}...\n"
            )

    # delete the copied collection and its children
    if (
        "bms_blender_plugin" in context.preferences.addons.keys()
        and not context.preferences.addons[
            "bms_blender_plugin"
        ].preferences.do_not_delete_export_collection
    ):
        for obj in collection_copy_root.objects:
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(collection_copy_root)

    return material_names, hotspots


def get_nodes(context, root_collection, script, auto_smooth_value):
    """Recursively builds the BML node list for a given collection with all of its elements
    (refer to the BMLv2 format definition).
    Returns a triple of the nodes in binary format, the material list and the amount of nodes
    """
    material_names = []
    nodes = []
    current_vertices_index = 0
    current_vertices_size = 0
    vertices_data = []  # raw byte data
    vertex_indices = []
    hotspots = dict()

    # puts all render control nodes before any of the DOFs or primitives - this simplifies things a lot.
    # we only need to make sure that the nodes are in order
    nodes = get_render_control_nodes()

    def _recursively_parse_nodes(objects):
        nonlocal current_vertices_index
        nonlocal current_vertices_size

        # merge all objects with the same material in the current collection
        if (
            "bms_blender_plugin" in context.preferences.addons.keys()
            and context.preferences.addons[
                "bms_blender_plugin"
            ].preferences.do_not_join_materials
        ):
            prepared_objects = objects
        else:
            prepared_objects = join_objects_with_same_materials(
                objects, dict(), auto_smooth_value
            )

        # parse all objects of the current collection
        for obj in prepared_objects:
            parsed_nodes = None
            if obj.type == "MESH" and get_bml_type(obj) is None:
                parsed_nodes = parse_mesh(
                    obj,
                    nodes,
                    vertex_indices,
                    material_names,
                    current_vertices_index,
                    current_vertices_size,
                )

            elif get_bml_type(obj) == BlenderNodeType.PBR_LIGHT:
                parsed_nodes = parse_bbl_light(
                    obj,
                    nodes,
                    vertex_indices,
                    material_names,
                    current_vertices_index,
                    current_vertices_size,
                )

            elif get_bml_type(obj) == BlenderNodeType.SLOT:  # Slots can be empty
                parsed_nodes = parse_slot(obj, nodes)

            elif get_bml_type(obj) == BlenderNodeType.SWITCH:
                if len(obj.children) > 0:  # ignore empty Switches
                    parse_switch(obj, nodes)
            elif get_bml_type(obj) == BlenderNodeType.DOF:
                if len(obj.children) > 0:  # ignore empty DOFs
                    parse_dof(obj, nodes)
            elif get_bml_type(obj) == BlenderNodeType.HOTSPOT:
                parse_hotspot(obj, hotspots)

            # end of parsing, append parsed data to the nodes list
            if parsed_nodes:
                vertices_data.extend(parsed_nodes.vertex_data)
                current_vertices_index += parsed_nodes.vertices_length
                current_vertices_size += parsed_nodes.vertices_size

            """
            Certain nodes (dofs, switches) require an _END node which requires the same node index as the "START" node
            The above steps have added +1 to the index count, and so we take the len(nodes) -1 to obtain the parent index
            If I was going to refactor this I would explicitely calculate the node_index and avoid calculating it in each
            Node definition.
            """
            parent_node_index = len(nodes) -1

            # recursively iterate over all children
            if obj.children:
                _recursively_parse_nodes(obj.children)

            # append the end nodes for Switches, DOFs and Slots
            if get_bml_type(obj) == BlenderNodeType.SWITCH and len(obj.children) > 0:
                nodes.append(SwitchEnd(parent_node_index))
            elif get_bml_type(obj) == BlenderNodeType.DOF and len(obj.children) > 0:
                nodes.append(DofEnd(parent_node_index))
            elif get_bml_type(obj) == BlenderNodeType.SLOT:
                nodes.append(SlotEnd(parent_node_index))

    # parse all nodes of the root collection
    root_objects = []
    for collection_object in root_collection.objects:
        if collection_object.parent is None:
            root_objects.append(collection_object)

    _recursively_parse_nodes(root_objects)

    if int(script) == -1:
        # TODO - seems fishy
        script_no = 0
    else:
        script_no = int(script)

    material_count = len(material_names)
    data = struct.pack("<II", script_no, material_count)
    for material_name in material_names:
        data += struct.pack("<i", len(material_name))
        data += bytes(material_name, "ascii")

    if len(vertex_indices) < 256:
        index_buffer_format = IndexBufferFormat.FORMAT_16
        vertex_indices_data = struct.pack("%sH" % len(vertex_indices), *vertex_indices)
        vertex_indices_data_size = 2 * len(vertex_indices)
    else:
        index_buffer_format = IndexBufferFormat.FORMAT_32
        vertex_indices_data = struct.pack("%sI" % len(vertex_indices), *vertex_indices)
        vertex_indices_data_size = 4 * len(vertex_indices)

    # ibFormat, TotalIndices, TotalVertices, NodeCount
    data += struct.pack(
        "<IIII",
        index_buffer_format.value,
        len(vertex_indices),
        current_vertices_index,
        len(nodes),
    )

    # nodes
    for node in nodes:
        data += node.to_data()

    # ibNextIndex
    data += struct.pack("<I", vertex_indices_data_size)

    # ib
    data += vertex_indices_data

    # vbNextIndex
    data += struct.pack("<I", current_vertices_size)

    # vb
    data += b"".join(vertices_data)

    return {
        "data": data,
        "material_names": material_names,
        "nodes_amount": len(nodes),
        "hotspots": hotspots,
    }


def join_objects_with_same_materials(objects, materials_objects, auto_smooth_value):
    """Joins objects of the same BML node level (i.e. not separated by DOFs, Switches or Slots)
    to a single Blender object. This is critical to reduce draw calls"""
    object_names = []
    for obj in objects:
        if obj:
            object_names.append(obj.name)

    for obj_name in object_names:
        obj = bpy.data.objects[obj_name]


        if obj.type == "MESH":
            # regular meshes
            # "do not merge" flag - just use a custom material name which will never be looked up
            if obj.bml_do_not_merge:
                materials_objects[obj.name] = [obj]
                continue

            if len(obj.material_slots) > 0:
                material_name = obj.material_slots[0].name
            else:
                material_name = "BML-Default"

            # if the object is a child of a switch, prepend the switch name, so they are only merged with materials
            # within their switch level
            if get_bml_type(obj.parent) is BlenderNodeType.SWITCH:
                material_name += obj.parent.name + "_" + material_name

            # before we join the lights into a common object, we need to store their individual object values in
            # separate face variables, so we can create their vertices later
            # the keys of all stored values is their face index

            if get_bml_type(obj) == BlenderNodeType.PBR_LIGHT:
                # make sure we only join lights with other lights - simply change the key
                material_name = "BML_BBL_" + material_name

                # create the data layers - these will be kept in the merged object
                layer_normal_x = obj.data.polygon_layers_float.new(name="bml_normal_x")
                layer_normal_y = obj.data.polygon_layers_float.new(name="bml_normal_y")
                layer_normal_z = obj.data.polygon_layers_float.new(name="bml_normal_z")

                layer_color_r = obj.data.polygon_layers_float.new(name="bml_color_r")
                layer_color_g = obj.data.polygon_layers_float.new(name="bml_color_g")
                layer_color_b = obj.data.polygon_layers_float.new(name="bml_color_b")
                layer_color_a = obj.data.polygon_layers_float.new(name="bml_color_a")

                for face in obj.data.polygons:
                    # assert that each light has only one face and 4 verts
                    if len(face.vertices) != 4:
                        raise Exception(
                            f"Object '{obj.name}' is a malformed light (needs exactly 4 vertices per face)"
                        )
                    # normal
                    if obj.bml_light_directional:
                        # directional light
                        layer_normal_x.data[face.index].value = face.normal.x
                        layer_normal_y.data[face.index].value = face.normal.y
                        layer_normal_z.data[face.index].value = face.normal.z

                    else:
                        # omnidirectional
                        layer_normal_x.data[face.index].value = 0
                        layer_normal_y.data[face.index].value = 0
                        layer_normal_z.data[face.index].value = 0

                    # color
                    layer_color_r.data[face.index].value = obj.color[0]
                    layer_color_g.data[face.index].value = obj.color[1]
                    layer_color_b.data[face.index].value = obj.color[2]
                    layer_color_a.data[face.index].value = obj.color[3]

            object_with_same_material_list = materials_objects.get(material_name)

            # join objects with the same material name
            if object_with_same_material_list is not None:
                if len(object_with_same_material_list) != 1:
                    raise Exception("Invalid length of material list objects")

                object_with_same_material = object_with_same_material_list[0]

                # force autosmooth on the objects to be merged (reason: when joining, Blender will override the
                # smoothing options to the last object selected)
                if (
                    object_with_same_material.data.use_auto_smooth
                    or obj.data.use_auto_smooth
                ):
                    force_auto_smoothing_on_object(
                        object_with_same_material, auto_smooth_value
                    )
                    force_auto_smoothing_on_object(obj, auto_smooth_value)

                bpy.ops.object.select_all(action="DESELECT")
                obj.select_set(True)
                object_with_same_material.select_set(True)
                bpy.context.view_layer.objects.active = object_with_same_material
                bpy.ops.object.join()

            else:
                # no entries found, add material and obj as new entries
                materials_objects[material_name] = [obj]

        # make sure that DOFs, Switches and Slots are never joined
        elif obj.type == "EMPTY" and (
            get_bml_type(obj) == BlenderNodeType.DOF
            or get_bml_type(obj) == BlenderNodeType.SWITCH
            or get_bml_type(obj) == BlenderNodeType.SLOT
            # we can also add hotspots here so their children will be parsed as well
            or get_bml_type(obj) == BlenderNodeType.HOTSPOT
        ):
            materials_objects["_DOF_OR_SWITCH_OR_SLOT_OR_HOTSPOT_" + obj.name] = [obj]

        elif obj.type == "EMPTY":
            # add default empties as well so their children can be parsed
            materials_objects["_EMPTY_" + obj.name] = [obj]
    
    return [item for sublist in materials_objects.values() for item in sublist]

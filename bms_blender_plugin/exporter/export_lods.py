"""
Performance Notes:
- Material batching optimization gives ~10-12% improvement in DOF/switch heavy scenes
- Mesh-heavy scenes should see higher gains (~50%?)
- Further perf improvements: batch DOF processing, reduce object selection calls
"""

import os
import struct
from contextlib import nullcontext

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
    context, file_directory, file_prefix, lod_list, scale_factor, export_settings: ExportSettings, export_profiler=None
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
            context, lod.collection, scale_factor, export_settings, bml_file_path, export_profiler
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
    context, collection, scale_factor, export_settings: ExportSettings, file_path, export_profiler=None
):
    """Exports a single Blender collection to a BML file."""
    # create a temporary collection and copy the current collection's visible objects into it
    collection_copy_root = bpy.data.collections.new(collection.name + "_export")
    bpy.context.scene.collection.children.link(collection_copy_root)
    with export_profiler.stage("lod: copy collection") if export_profiler else nullcontext():
        copy_collection_flat(
            collection,
            collection_copy_root,
            [collection_copy_root],
            scale_factor,
            export_profiler,
        )

    with export_profiler.stage("lod: apply modifiers") if export_profiler else nullcontext():
        apply_all_modifiers(collection_copy_root, export_profiler)

    # make sure we are on the base texture set
    with export_profiler.stage("lod: revert material set") if export_profiler else nullcontext():
        revert_to_base_material_set(context, collection_copy_root)

    # get the data of the root collection
    with export_profiler.stage("lod: build payload") if export_profiler else nullcontext():
        nodes_output = get_nodes(
            context,
            collection_copy_root,
            export_settings.script,
            export_settings.auto_smooth_value,
            export_profiler,
        )
    payload = nodes_output["data"]
    material_names = nodes_output["material_names"]
    hotspots = nodes_output["hotspots"]

    payload_size = len(payload)

    with export_profiler.stage("lod: final compression") if export_profiler else nullcontext():
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

    with export_profiler.stage("lod: assemble file") if export_profiler else nullcontext():
        header = Header(
            2, payload_size, payload_compressed_size, export_settings.compression
        )
        data = header.to_data() + payload

    if export_settings.export_models:
        with export_profiler.stage("lod: write file") if export_profiler else nullcontext():
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
        with export_profiler.stage("lod: cleanup temp collection") if export_profiler else nullcontext():
            for obj in collection_copy_root.objects:
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(collection_copy_root)

    return material_names, hotspots


def get_nodes(context, root_collection, script, auto_smooth_value, export_profiler=None):
    """Recursively builds the BML node list for a given collection with all of its elements
    (refer to the BMLv2 format definition).
    Returns a triple of the nodes in binary format, the material list and the amount of nodes
    """
    material_names = []
    material_lookup = {}
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
            with export_profiler.stage("nodes: join by material") if export_profiler else nullcontext():
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
                    material_lookup,
                    current_vertices_index,
                    current_vertices_size,
                    export_profiler,
                )

            elif get_bml_type(obj) == BlenderNodeType.PBR_LIGHT:
                parsed_nodes = parse_bbl_light(
                    obj,
                    nodes,
                    vertex_indices,
                    material_names,
                    material_lookup,
                    current_vertices_index,
                    current_vertices_size,
                    export_profiler,
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
                vertices_data.append(parsed_nodes.vertex_data)
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
    with export_profiler.stage("nodes: pack index buffer") if export_profiler else nullcontext():
        # FORMAT_16 uses unsigned 16-bit indices, so it is valid while the largest vertex index fits in 0..65535.
        if current_vertices_index <= 65536:
            index_buffer_format = IndexBufferFormat.FORMAT_16
            vertex_indices_data = struct.pack("%sH" % len(vertex_indices), *vertex_indices)
            vertex_indices_data_size = 2 * len(vertex_indices)
        else:
            index_buffer_format = IndexBufferFormat.FORMAT_32
            vertex_indices_data = struct.pack("%sI" % len(vertex_indices), *vertex_indices)
            vertex_indices_data_size = 4 * len(vertex_indices)

    with export_profiler.stage("nodes: pack node data") if export_profiler else nullcontext():
        nodes_data = b"".join(node.to_data() for node in nodes)

    with export_profiler.stage("nodes: pack vertex buffer") if export_profiler else nullcontext():
        packed_vertices_data = b"".join(vertices_data)

    with export_profiler.stage("nodes: assemble payload") if export_profiler else nullcontext():
        data_parts = [struct.pack("<II", script_no, material_count)]
        for material_name in material_names:
            data_parts.append(struct.pack("<i", len(material_name)))
            data_parts.append(bytes(material_name, "ascii"))

        # ibFormat, TotalIndices, TotalVertices, NodeCount
        data_parts.append(
            struct.pack(
                "<IIII",
                index_buffer_format.value,
                len(vertex_indices),
                current_vertices_index,
                len(nodes),
            )
        )
        # nodes
        data_parts.append(nodes_data)
        # ibNextIndex
        data_parts.append(struct.pack("<I", vertex_indices_data_size))
        # ib
        data_parts.append(vertex_indices_data)
        # vbNextIndex
        data_parts.append(struct.pack("<I", current_vertices_size))
        # vb
        data_parts.append(packed_vertices_data)
        data = b"".join(data_parts)

    return {
        "data": data,
        "material_names": material_names,
        "nodes_amount": len(nodes),
        "hotspots": hotspots,
    }


def join_objects_with_same_materials(objects, materials_objects, auto_smooth_value):
    """Joins objects of the same BML node level (i.e. not separated by DOFs, Switches or Slots)
    to a single Blender object. This is critical to reduce draw calls"""
    
    # Instead of joining objects one-by-one, we first group them 
    # by material, then batch join all objects with the same material in a single operation.
    
    object_names = []
    for obj in objects:
        if obj:
            object_names.append(obj.name)

    # Step 1: Categorize objects and prepare light data (no joining yet)
    mesh_objects_by_material = {}  # List of obj for batch join
    
    for obj_name in object_names:
        obj = bpy.data.objects[obj_name]

        if obj.type == "MESH":
            # "do not merge" flag - just use a custom material name which will never be looked up
            # enhance this by including BBOXs in the do not merge category - Otherwise joined objects will not render
            if obj.bml_do_not_merge or get_bml_type(obj) == BlenderNodeType.BBOX:
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

            # Group mesh objects by material for batch processing
            if material_name not in mesh_objects_by_material:
                mesh_objects_by_material[material_name] = []
            mesh_objects_by_material[material_name].append(obj)

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

    # Step 2: Batch join - one join per material group instead of one join per object pair
    for material_name, objects_with_same_material in mesh_objects_by_material.items():
        if len(objects_with_same_material) == 1:
            # Single object with this material, no joining needed
            materials_objects[material_name] = objects_with_same_material
        else:
            # Multiple objects with same material - batch join them all at once
            print(f"Batch join {len(objects_with_same_material)} objects, material: '{material_name}'")
            
            # Fix UV layer preservation during join (Issue #21)
            # Blender's join tends to favor a layer literally named "UVMap". Keep exactly one primary UV layer.
            # Exporter only uses a single UV layer, so we can safely collapse multiples.
            for obj in objects_with_same_material:
                uv_layers = obj.data.uv_layers
                if len(uv_layers) == 0:
                    continue  # No UV layers, nothing to normalize

                # Ensure some layer is active
                if not uv_layers.active:
                    uv_layers.active_index = 0
                    print(f"[BML Export] Warning: Object '{obj.name}' had no active UV layer; first layer set active")

                # Prefer an existing primary layer actually named "UVMap" if present
                primary_layer = uv_layers.get("UVMap")
                if primary_layer is not None:
                    # Make sure it's the active layer for downstream ops
                    for i, layer in enumerate(uv_layers):
                        if layer == primary_layer:
                            uv_layers.active_index = i
                            break
                else:
                    # No layer named "UVMap"; use the active layer as the primary and rename it
                    primary_layer = uv_layers.active
                    if primary_layer.name != "UVMap":
                        print(f"📝  Info: Renaming active UV layer '{primary_layer.name}' on '{obj.name}' to 'UVMap'")
                        primary_layer.name = "UVMap"

                # Remove ALL other layers (exporter uses only one); collect NAMES first so we can re-resolve
                removable_names = [layer.name for layer in uv_layers if layer.name != "UVMap"]
                for lname in removable_names:
                    # Re-fetch by name to avoid stale pointer if Blender reallocated internally
                    layer_obj = uv_layers.get(lname)
                    if layer_obj is None:
                        # Already removed/renamed by previous operation
                        continue
                    try:
                        uv_layers.remove(layer_obj)
                    except RuntimeError as e:
                        print(f"⚠️  Warning: Failed to remove secondary UV layer '{lname}' from '{obj.name}': {e}")

                # Safety check
                if uv_layers.active is None or uv_layers.active.name != "UVMap":
                    # If something unexpected happened, fall back to first layer and rename
                    if len(uv_layers):
                        uv_layers.active_index = 0
                        if uv_layers.active and uv_layers.active.name != "UVMap":
                            try:
                                uv_layers.active.name = "UVMap"
                            except Exception:
                                pass
                        print(f"📝  Info: Repaired primary UVMap layer on '{obj.name}' after cleanup")
            
            # force autosmooth on all objects to be merged (reason: when joining, Blender will override the
            # smoothing options to the last object selected)
            # Check if ANY object in this group has auto_smooth enabled
            any_object_has_auto_smooth = any(obj.data.use_auto_smooth for obj in objects_with_same_material)
            
            if any_object_has_auto_smooth:
                # If ANY object has auto_smooth, apply it to ALL objects in the group (original behavior)
                for obj in objects_with_same_material:
                    if not obj.data.use_auto_smooth:
                        print(f"⚠️  Warning: Object '{obj.name}' does not have auto-smoothing enabled but will be forced to match other objects in material group '{material_name}'")
                    force_auto_smoothing_on_object(obj, auto_smooth_value)

            # Select all objects with this material at once
            bpy.ops.object.select_all(action="DESELECT")
            for obj in objects_with_same_material:
                obj.select_set(True)
            
            # Set first object as active (target for join operation)
            bpy.context.view_layer.objects.active = objects_with_same_material[0]
            
            # Perform ONE join operation for all objects with this material
            bpy.ops.object.join()
            
            # Store the joined result (first object now contains all the merged geometry)
            materials_objects[material_name] = [objects_with_same_material[0]]

    return [item for sublist in materials_objects.values() for item in sublist]

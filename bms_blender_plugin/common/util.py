import bpy

import bpy.utils.previews

import os
import struct


import lzma
import math
from mathutils import Vector, Matrix, Quaternion, Euler

from bms_blender_plugin.common.bml_structs import (
    Header,
    Compression,
    DofType,
)
from bms_blender_plugin.common.blender_types import (
    BlenderNodeType,
    ScriptEnum,
    DofEnum,
    SwitchEnum,
)

import xml.etree.ElementTree as ElementTree

from bms_blender_plugin.common.hotspot import Callback
from bms_blender_plugin.common.coordinates import to_bms_coords


def compress_lz_4(data):
    import lz4.frame

    return lz4.frame.compress(data)


def compress_lzma(data):
    """Compresses a string to BMS custom LZMA"""
    compressor = lzma.LZMACompressor(format=lzma.FORMAT_ALONE)

    output = compressor.compress(data)
    output += compressor.flush()
    # BMS specific: normally, an LZMA header contains 5 bytes of general header data and 8 bytes of uncompressedSize
    # BMS does not want the uncompressedSize for a reason, so we strip it away
    return output[:5] + output[13:]


def get_objcenter(obj, convert_to_bms_coords=True):
    """Returns the center of an object based on its vertices"""
    # https://blender.stackexchange.com/questions/62040/get-center-of-geometry-of-an-object
    x, y, z = [sum([v.co[i] for v in obj.data.vertices]) for i in range(3)]
    count = float(len(obj.data.vertices))

    # ignore objects without geometry
    if count == 0:
        return Vector((0, 0, 0))

    if convert_to_bms_coords:
        return to_bms_coords(obj.matrix_world @ (Vector((x, y, z)) / count))
    else:
        return obj.matrix_world @ (Vector((x, y, z)) / count)


def get_bml_type(obj, purge_orphaned_object=True):
    """Returns the custom type of an object (NOT a node).
    Additionally filter out orphaned objects"""
    if obj is None or "bml_type" not in obj.keys() or len(obj.users_collection) == 0:
        return None
    else:
        # orphaned DOF or switch - e.g. the DOF was removed from the scene but is still referenced by a node
        # if not bpy.app.background and purge_orphaned_object and len(obj.users_collection) == 0:
        #    bpy.data.objects.remove(obj)
        #    return None
        # TODO find a proper way to clean up objects without breaking the export


        bml_type = BlenderNodeType(obj.bml_type)
        if bml_type is BlenderNodeType.NONE:
            return None
        else:
            return bml_type


switches = []


def get_switches():
    """Returns a list of BMS Switches which are loaded from the switch.xml"""
    global switches
    if switches is None or len(switches) == 0:
        import os

        switches_tree = ElementTree.parse(
            os.path.join(os.path.dirname(__file__), "switch.xml")
        )
        root = switches_tree.getroot()
        switches = []

        for switch in root:
            switch_number = int(switch.find("SwitchNum").text)
            branch = int(switch.find("BranchNum").text)
            if switch.find("Name") is not None:
                name = switch.find("Name").text
            else:
                name = ""

            if switch.find("Comment") is not None:
                comment = switch.find("Comment").text
            else:
                comment = ""

            switches.append(SwitchEnum(switch_number, branch, name, comment))

        print(f"Imported {len(switches)} switches from file")

    return switches


scripts = []


def get_scripts():
    """Returns a list of BMS Scripts which are loaded from the script.xml"""
    global scripts

    if scripts is None or len(scripts) == 0:
        scripts_tree = ElementTree.parse(
            os.path.join(os.path.dirname(__file__), "script.xml")
        )
        root = scripts_tree.getroot()
        scripts = [ScriptEnum(-1, "None")]

        for script in root:
            script_number = int(script.find("ScriptNum").text)
            if script.find("Name") is not None:
                name = script.find("Name").text
            else:
                name = ""

            scripts.append(ScriptEnum(script_number, name))

        print(f"Imported {len(scripts) - 1} scripts from file")

    return scripts


dofs = []


def get_dofs():
    """Returns a list of BMS DOFs which are loaded from the DOF.xml"""
    global dofs

    if dofs is None or len(dofs) == 0:
        dofs_tree = ElementTree.parse(
            os.path.join(os.path.dirname(__file__), "DOF.xml")
        )
        root = dofs_tree.getroot()
        dofs = []

        for dof in root:
            dof_number = int(dof.find("DOFNum").text)
            if dof.find("Name") is not None and dof.find("Name").text is not None:
                name = dof.find("Name").text
            else:
                name = ""

            dofs.append(DofEnum(dof_number, name))

        print(f"Imported {len(dofs)} dofs from file")

    return dofs


callbacks = []


def get_callbacks():
    """Returns a list of callbacks from the callbacks.xml file"""
    global callbacks

    if callbacks is None or len(callbacks) == 0:
        callback_tree = ElementTree.parse(
            os.path.join(os.path.dirname(__file__), "callbacks.xml")
        )
        root = callback_tree.getroot()
        callbacks = []

        for callback in root:
            if (
                callback.find("Name") is not None
                and callback.find("Name").text is not None
            ):
                # a valid callback will need its name
                name_id = callback.find("Name").text
                group = "Uncategorized"

                if (
                    callback.find("Group") is not None
                    and callback.find("Group").text is not None
                ):
                    group = callback.find("Group").text

                callbacks.append(Callback(name_id, group))

        print(f"Imported {len(callbacks)} callbacks from file")

    return callbacks


def flatten_collection(collection, parent_collection):
    """Removes all non-switch collections from the tree, moving their objects up
    and deletes empty collections with no children"""
    for collection_child in collection.children:
        flatten_collection(collection_child, collection)

    if (get_bml_type(collection) != BlenderNodeType.SWITCH) and parent_collection:
        print(f"{collection.name} is NOT a switch...")
        for obj in collection.objects:
            collection.objects.unlink(obj)
            parent_collection.objects.link(obj)

        if len(collection.objects) == 0 and len(collection.children) == 0:
            bpy.data.collections.remove(collection)


def get_parent_dof_or_switch(obj):
    """Recursively returns the first parent of an object which is either a DOF or a switch"""
    if obj:
        if (
            get_bml_type(obj) == BlenderNodeType.DOF
            or get_bml_type(obj) == BlenderNodeType.SWITCH
        ):
            return obj
        elif obj.parent:
            return get_parent_dof_or_switch(obj.parent)
    return None


def get_non_translate_dof_parent(obj):
    """Recursively returns the first parent which is not a TRANSLATE DOF"""
    if not obj:
        return None

    if get_bml_type(obj) == BlenderNodeType.DOF and obj.dof_type == DofType.TRANSLATE.name:
        return get_non_translate_dof_parent(obj.parent)
    else:
        return obj


def copy_collection_flat(
    from_collection, to_collection, excluded_collections, scale_factor
):
    """Copies a collection and all of its objects but not its child-collections.
    Also applies a scale factor to its objects"""
    copied_object = None

    if from_collection not in excluded_collections:
        for collection_object in from_collection.objects:
            if collection_object.parent is None:
                # root object - copy that
                copied_object = copy_object(
                    collection_object, None, to_collection, scale_factor
                )

        for collection_child in from_collection.children:
            copy_collection_flat(
                collection_child, to_collection, excluded_collections, scale_factor
            )

        # toggle object mode to make sure that the scaling has been applied (Blender quirk)
        # don't do this with the original object as it might have been hidden in the view port
        if copied_object:
            bpy.context.view_layer.objects.active = copied_object
            bpy.ops.object.mode_set(mode="OBJECT")


def reset_dof(obj):
    """Resets a DOF by zeroing all of its delta values"""
    if get_bml_type(obj) == BlenderNodeType.DOF:
        obj.dof_input = 0
        obj.rotation_mode = "XYZ"
        obj.delta_rotation_euler.x = 0
        obj.delta_rotation_euler.y = 0
        obj.delta_rotation_euler.z = 0
        obj.delta_location.x = 0
        obj.delta_location.y = 0
        obj.delta_location.z = 0

        obj.delta_scale.x = 1
        obj.delta_scale.y = 1
        obj.delta_scale.z = 1


def copy_object(obj, parent, collection, scale_factor=1):
    """Recursively copies an object and all of its children and moves their copies to a given collection.
    Also applies a scale factor"""
    if not obj.hide_render and len(obj.users_collection) != 0:
        copied_object = obj.copy()
        copied_object.parent = parent
        copied_object.matrix_parent_inverse = obj.matrix_parent_inverse.copy()

        if obj.data:
            copied_object.data = copied_object.data.copy()
        for k, e in obj.items():
            copied_object[k] = e

        # copy and apply all modifiers
        for obj_modifier in obj.modifiers:
            copied_object_modifiers = obj.modifiers.get(obj_modifier.name, None)
            if not copied_object_modifiers:
                copied_object_modifiers = obj.modifiers.new(
                    obj_modifier.name, obj_modifier.type
                )

            # collect names of writable properties
            properties = [
                p.identifier
                for p in obj_modifier.bl_rna.properties
                if not p.is_readonly
            ]

            # copy those properties
            for prop in properties:
                setattr(copied_object_modifiers, prop, getattr(obj_modifier, prop))

        # set all DOFs to 0
        if get_bml_type(obj, False) == BlenderNodeType.DOF:
            reset_dof(copied_object)

        # scale only the root objects
        if scale_factor != 1 and obj.parent is None:
            copied_object.scale *= scale_factor
            copied_object.location *= scale_factor

        collection.objects.link(copied_object)

        # override any selection restriction
        copied_object.hide_select = False
        copied_object.hide_viewport = False
        copied_object.hide_set(False)

        for obj_child in obj.children:
            copy_object(obj_child, copied_object, collection, scale_factor)
        return copied_object


def apply_all_modifiers(collection):
    """Applies all modifiers to objects which are rooted in the given collection"""
    for obj in collection.objects:
        if obj.parent is None:
            apply_all_modifiers_on_obj(obj)


def apply_all_modifiers_on_obj(obj):
    """Applies all modifiers to a single object.
    Empties (DOFs, Slots and Switches) are excepted, since applying their modifiers would reset their positions.
    """
    if obj:
        bpy.ops.object.select_all(action="DESELECT")
        # apply the modifiers
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        if obj.type == "MESH":
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.convert(target="MESH", keep_original=False)

        if get_bml_type(obj) not in [
            BlenderNodeType.DOF,
            BlenderNodeType.SLOT,
            BlenderNodeType.HOTSPOT,
        ]:
            bpy.ops.object.transform_apply()
        else:
            # only apply scaling operations to those objects
            # all other operations would reset them since they are empties
            bpy.ops.object.transform_apply(
                location=False, rotation=False, scale=True, properties=False
            )

        for child in obj.children:
            apply_all_modifiers_on_obj(child)


def uncompress_file(src, dest):
    """Uncompresses a compressed BML file and stores it in a separate file"""
    with open(src, "rb") as input_file:
        input_bytes = input_file.read()

        if input_bytes[0:4] != bytes("BML\0", "ascii"):
            raise Exception("Invalid BML file header")

        header = Header.from_data(input_bytes[:28])
        compressed_payload = bytearray(input_bytes[28:])
        uncompressed_payload = uncompress_lzma(compressed_payload, header.payload_size)
        header.compression = Compression.NONE
        header.payload_compressed_size = header.payload_size

    with open(dest, "wb") as output_file:
        output_file.write(header.to_data())
        output_file.write(uncompressed_payload)


def uncompress_lzma(bytes_array, uncompressed_size):
    """Uncompresses a binary stream which is expected to be in BMS LZMA format"""
    # BMS specific: add the missing header bytes for the uncompressedSize
    bytes_array[5:5] = struct.pack("<Q", uncompressed_size)
    decompressor = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE)

    output = decompressor.decompress(bytes_array, uncompressed_size)
    return output


def force_auto_smoothing_on_object(obj, auto_smooth_angle_deg):
    """Applies auto smoothing to an object"""
    if obj and obj.data and obj.type == "MESH":
        obj.data.use_auto_smooth = True
        obj.data.auto_smooth_angle = math.radians(auto_smooth_angle_deg)


def get_bounding_sphere(objects):
    """Returns a bounding sphere as a tuple (center, radius) of a list of objects"""
    """adapted from https://b3d.interplanety.org/en/how-to-calculate-the-bounding-sphere-for-selected-objects/"""
    points_co_global = []

    for obj in objects:
        if obj.data and obj.type == "MESH":
            points_co_global.extend(
                [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
            )

    def get_center(axis):
        return (max(axis) + min(axis)) / 2 if axis else 0.0

    x, y, z = [[point_co[i] for point_co in points_co_global] for i in range(3)]
    b_sphere_center = (
        Vector([get_center(axis) for axis in [x, y, z]]) if (x and y and z) else None
    )
    b_sphere_radius = (
        max(((point - b_sphere_center) for point in points_co_global))
        if b_sphere_center
        else None
    )

    if b_sphere_center and b_sphere_radius:
        return b_sphere_center, b_sphere_radius.length
    else:
        return 0, 0


class Icons:
    """Static icon loader"""

    menu_icon_id = None
    hotspot_icon_id = None
    slot_icon_id = None
    push_button_icon_id = None
    toggle_icon_id = None
    wheel_icon_id = None
    preview_collections = []

    @staticmethod
    def init_icons():
        icons_dict = bpy.utils.previews.new()
        Icons.preview_collections.append(icons_dict)
        icons_dir = os.path.join(os.path.dirname(__file__), "icons")
        icons_dict.load(
            "add_menu_icon", os.path.join(icons_dir, "add_menu.png"), "IMAGE"
        )
        icons_dict.load(
            "hotspot_icon", os.path.join(icons_dir, "hotspot_icon.png"), "IMAGE"
        )
        icons_dict.load("slot_icon", os.path.join(icons_dir, "slot_icon.png"), "IMAGE")

        icons_dict.load(
            "push_button_icon", os.path.join(icons_dir, "push_button.png"), "IMAGE"
        )
        icons_dict.load("toggle_icon", os.path.join(icons_dir, "toggle.png"), "IMAGE")
        icons_dict.load("wheel_icon", os.path.join(icons_dir, "wheel.png"), "IMAGE")

        Icons.menu_icon_id = icons_dict["add_menu_icon"].icon_id
        Icons.hotspot_icon_id = icons_dict["hotspot_icon"].icon_id
        Icons.slot_icon_id = icons_dict["slot_icon"].icon_id
        Icons.push_button_icon_id = icons_dict["push_button_icon"].icon_id
        Icons.toggle_icon_id = icons_dict["toggle_icon"].icon_id
        Icons.wheel_icon_id = icons_dict["wheel_icon"].icon_id

    @staticmethod
    def get_slot_image():
        icons_dir = os.path.join(os.path.dirname(__file__), "icons")
        return bpy.data.images.load(os.path.join(icons_dir, "slot.png"))

    @staticmethod
    def get_hotspot_image():
        icons_dir = os.path.join(os.path.dirname(__file__), "icons")
        return bpy.data.images.load(os.path.join(icons_dir, "hotspot.png"))


Icons.init_icons()


def unregister():
    for coll in Icons.preview_collections:
        bpy.utils.previews.remove(coll)

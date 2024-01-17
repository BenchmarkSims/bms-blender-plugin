from bms_blender_plugin.common.blender_types import BlenderNodeType
from bms_blender_plugin.common.util import get_bml_type


def update_slot_number(slot, context):
    if slot and get_bml_type(slot) == BlenderNodeType.SLOT:
        slot.name = f"Slot #{slot.bml_slot_number}"

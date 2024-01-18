import bpy

from bms_blender_plugin.common.util import Icons
from bms_blender_plugin.ui_tools.operators.create_bounding_box_operator import CreateBoundingBox
from bms_blender_plugin.ui_tools.operators.create_dof import CreateDof
from bms_blender_plugin.ui_tools.operators.create_hotspot import CreateHotspot
from bms_blender_plugin.ui_tools.operators.create_pbr_light import CreatePBRLight
from bms_blender_plugin.ui_tools.operators.create_switch import CreateSwitch
from bms_blender_plugin.ui_tools.operators.slot_operators import CreateSlot


class AddBMLSubmenu(bpy.types.Menu):
    bl_idname = "OBJECT_MT_add_bml_submenu"
    bl_label = "Falcon BMS"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout

        layout.operator(CreateDof.bl_idname, text="DOF", icon="EMPTY_DATA")
        layout.operator(CreateSwitch.bl_idname, text="Switch", icon="CHECKBOX_HLT")
        layout.operator(CreatePBRLight.bl_idname, text="Billboard Light", icon="LIGHT")
        layout.operator(CreateHotspot.bl_idname, text="Hotspot", icon_value=Icons.hotspot_icon_id)
        layout.operator(CreateSlot.bl_idname, text="Slot", icon_value=Icons.slot_icon_id)
        layout.operator(CreateBoundingBox.bl_idname, text="Bounding Box", icon="META_CUBE")


def menu_func(self, context):
    self.layout.menu(AddBMLSubmenu.bl_idname, text=AddBMLSubmenu.bl_label,
                     icon_value=Icons.menu_icon_id)


def register():
    bpy.utils.register_class(AddBMLSubmenu)
    bpy.types.VIEW3D_MT_add.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_add.remove(menu_func)
    bpy.utils.unregister_class(AddBMLSubmenu)

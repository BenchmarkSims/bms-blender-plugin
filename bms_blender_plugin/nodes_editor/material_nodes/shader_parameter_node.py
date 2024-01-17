import bpy
from bpy.props import StringProperty, EnumProperty, FloatProperty, BoolProperty

from bms_blender_plugin.common.bml_material import Slot
from bms_blender_plugin.common.blender_types import BlenderEditorNodeType
from bms_blender_plugin.nodes_editor.material_base_node import MaterialBaseNode


class ShaderNode(MaterialBaseNode):
    bl_label = "Shader"

    def init(self, context):
        self.bml_node_type = str(BlenderEditorNodeType.SHADER_PARAMETER)
        self.outputs.new("NodeSocketVirtual", "Shader Parameters")
        self.width = 200

    def draw_buttons(self, context, layout):
        layout.prop(self, "slot", text="Slot")
        row = layout.row()
        row.label(text="Shader Units")
        box = layout.box()
        box.prop(self, "shader_unit_vertex")
        box.prop(self, "shader_unit_compute")
        box.prop(self, "shader_unit_hull")
        box.prop(self, "shader_unit_domain")
        box.prop(self, "shader_unit_geometry")
        box.prop(self, "shader_unit_pixel")

        layout.row()
        layout.prop(self, "emission_intensity")
        layout.prop(self, "emission_callback")
        layout.separator()

        layout.prop(self, "layout_name", text="Layout Name")


def register():
    bpy.utils.register_class(ShaderNode)


def unregister():
    bpy.utils.unregister_class(ShaderNode)


bpy.types.Node.shader_unit_vertex = BoolProperty(name="Vertex Shader", default=False)
bpy.types.Node.shader_unit_compute = BoolProperty(name="Compute Shader", default=False)
bpy.types.Node.shader_unit_hull = BoolProperty(name="Hull Shader", default=False)
bpy.types.Node.shader_unit_domain = BoolProperty(name="Domain Shader", default=False)
bpy.types.Node.shader_unit_geometry = BoolProperty(
    name="Geometry Shader", default=False
)
bpy.types.Node.shader_unit_pixel = BoolProperty(name="Pixel Shader", default=False)

bpy.types.Node.layout_name = StringProperty(default="", name="Layout")
bpy.types.Node.slot = EnumProperty(
    name="Slot",
    description="The Slot for which the shader is applied",
    items=(
        (Slot.ALBEDO.name, "Albedo", "Albedo"),
        (Slot.ARMW.name, "ARMW", "ARMW"),
        (Slot.EMISSIVE.name, "Emissive", "Emissive"),
        (Slot.NORMAL_MAP.name, "Normal Map", "Normal Map"),
    ),
)

bpy.types.Node.emission_intensity = FloatProperty(
    default=0.0, name="Emission Intensity"
)
bpy.types.Node.emission_callback = FloatProperty(default=0.0, name="Emission Callback")

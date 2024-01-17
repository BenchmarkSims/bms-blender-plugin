import bpy
from bpy.props import EnumProperty, IntProperty

from bms_blender_plugin.common.bml_material import ShaderUnit, Slot, SamplerFilter, SamplerAddress
from bms_blender_plugin.common.blender_types import BlenderEditorNodeType
from bms_blender_plugin.nodes_editor.material_base_node import MaterialBaseNode


class SamplerNode(MaterialBaseNode):
    bl_label = "Sampler"

    def init(self, context):
        self.bml_node_type = str(BlenderEditorNodeType.SAMPLER)
        self.outputs.new("NodeSocketVirtual", "Sampler")
        self.width = 250

    def draw_buttons(self, context, layout):
        layout.prop(self, "slot")
        layout.prop(self, "unit")
        layout.prop(self, "filter")
        layout.prop(self, "max_anisotropy")
        layout.prop(self, "address")


def register():
    bpy.utils.register_class(SamplerNode)


def unregister():
    bpy.utils.unregister_class(SamplerNode)


bpy.types.Node.slot = EnumProperty(
        name="Slot",
        description="Sampler Slot",
        items=(
            (Slot.ALBEDO.name, "Albedo", "Albedo"),
            (Slot.ARMW.name, "ARMW", "ARMW"),
            (Slot.EMISSIVE.name, "Emissive", "Emissive"),
            (Slot.NORMAL_MAP.name, "Normal Map", "Normal Map"),
        ),
    )

bpy.types.Node.unit = EnumProperty(
    name="Shader Unit",
    description="Shader Unit",
    items=(
        (ShaderUnit.VERTEX_SHADER.name, "Vertex Shader", "Vertex Shader"),
        (ShaderUnit.COMPUTE_SHADER.name, "Compute Shader", "Compute Shader"),
        (ShaderUnit.HULL_SHADER.name, "Hull Shader", "Hull Shader"),
        (ShaderUnit.DOMAIN_SHADER.name, "Domain Shader", "Domain Shader"),
        (ShaderUnit.GEOMETRY_SHADER.name, "Geometry Shader", "Geometry Shader"),
        (ShaderUnit.PIXEL_SHADER.name, "Pixel Shader", "Pixel Shader"),
    ),
)

bpy.types.Node.filter = EnumProperty(
    name="Filter",
    description="Sampler Filter",
    items=(
        (SamplerFilter.ANISOTROPIC.name, "Anisotropic", "Anisotropic"),
        (SamplerFilter.POINT_MIP_POINT.name, "Point Mip Point", "Point Mip Point"),
        (SamplerFilter.POINT_MIP_LINEAR.name, "Point Mip Linear", "Point Mip Linear"),
        (SamplerFilter.LINEAR_MIP_POINT.name, "Linear Mip Point", "Linear Mip Point"),
        (SamplerFilter.LINEAR_MIP_LINEAR.name, "Linear Mip Linear", "Linear Mip Linear")
    ),
)

bpy.types.Node.max_anisotropy = IntProperty(default=0, name="Max. Anisotropy", min=0)

bpy.types.Node.address = EnumProperty(
    name="Address",
    description="Address",
    items=(
        (SamplerAddress.WRAP.name, "Wrap", "Wrap"),
        (SamplerAddress.MIRROR.name, "Mirror", "Mirror"),
        (SamplerAddress.CLAMP.name, "Clamp", "Clamp"),
        (SamplerAddress.BORDER.name, "Border", "Border"),
        (SamplerAddress.MIRROR_ONCE.name, "Mirror Once", "Mirror Once")
    ),
)

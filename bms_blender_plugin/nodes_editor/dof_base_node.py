import bpy
from bpy.app.handlers import persistent
from bpy.types import Node
from bpy.props import FloatProperty, StringProperty, IntProperty, PointerProperty, BoolProperty
from bpy.types import PropertyGroup

from bms_blender_plugin.common.bml_structs import ArgType
from bms_blender_plugin.common.blender_types import BlenderEditorNodeType


class RenderControlVariableType(PropertyGroup):
    argument_type: IntProperty(name="Argument Type", description="", default=ArgType.FLOAT)
    argument_id: IntProperty(name="Argument ID", description="", default=0)


class RenderControlVariable(PropertyGroup):
    name: StringProperty(name="Argument Name")
    type: PointerProperty(type=RenderControlVariableType)
    value: FloatProperty(name="value", default=0)
    has_error: BoolProperty(name="has_error", default=False)
    error_text: StringProperty(name="error_text", default="")


class DofBaseNode(Node):
    bl_label = "BMS DOF Node"

    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == "DofNodeTree"

    def execute(self, context):
        pass

    @classmethod
    @persistent
    def load_handler(cls, dummy, dummy_2):
        subscribe_node(cls)


def subscribe_node(node_clazz):
    from bms_blender_plugin.nodes_editor import dof_editor
    bpy.msgbus.subscribe_rna(
            key=node_clazz,
            owner=node_clazz.__name__,
            args=(),
            notify=dof_editor.execute_active_node_tree,
            options={
                "PERSISTENT",
            },
        )

    if node_clazz.load_handler not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(node_clazz.load_handler)


def unsubscribe_node(node_clazz):
    bpy.msgbus.clear_by_owner(node_clazz.__name__)
    if node_clazz.load_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(node_clazz.load_handler)


def register():
    bpy.utils.register_class(RenderControlVariableType)
    bpy.utils.register_class(RenderControlVariable)
    bpy.types.Node.arguments = bpy.props.CollectionProperty(type=RenderControlVariable)
    bpy.types.Node.result = bpy.props.PointerProperty(type=RenderControlVariable)
    bpy.utils.register_class(DofBaseNode)


def unregister():
    bpy.utils.unregister_class(RenderControlVariable)
    bpy.utils.unregister_class(RenderControlVariableType)
    bpy.utils.unregister_class(DofBaseNode)


bpy.types.Node.bml_node_type = bpy.props.EnumProperty(
    name="BML Node Type",
    description="BML Node Type",
    items=(
        (
            str(BlenderEditorNodeType.DOF_MODEL),
            "DOF Model",
            "A DOF representation in the model",
        ),
        (
            str(BlenderEditorNodeType.RENDER_CONTROL),
            "Render Control",
            "A Render Control",
        ),
        (
            str(BlenderEditorNodeType.MATERIAL),
            "Material",
            "A BML Material",
        ),
        (
            str(BlenderEditorNodeType.SAMPLER),
            "Sampler",
            "Sampler for a Material",
        ),
        (
            str(BlenderEditorNodeType.SHADER_PARAMETER),
            "Shader Parameter",
            "Shader Parameter for a Material",
        ),
        (str(BlenderEditorNodeType.NONE), "None", "None"),
    ),
    default=str(BlenderEditorNodeType.NONE),
)



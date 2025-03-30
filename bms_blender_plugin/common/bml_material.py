from enum import Enum, IntEnum

"""Represents the Materials.mtl file structure"""


class Slot(IntEnum):
    ALBEDO = 0
    ARMW = 1
    NORMAL_MAP = 2
    EMISSIVE = 3


class Texture:
    def __init__(self, File: str, Slot: Slot):
        self.File = File
        self.Slot = Slot


class Cull(str, Enum):
    BACK = "BACK"
    FRONT = "FRONT"
    NONE = "NONE"


class Flag:
    def __init__(
        self, Cull: Cull, DepthBias: int, ShadowCaster: int, SlopeScaledDepthBias: float
    ):
        self.Cull = Cull
        self.DepthBias = DepthBias
        self.ShadowCaster = ShadowCaster
        self.SlopeScaledDepthBias = SlopeScaledDepthBias


class ShaderParamConstants:
    def __init__(self, emissionIntensity: float, emissionCallback: float):
        self.emissionIntensity = emissionIntensity
        self.emissionCallback = emissionCallback


class ShaderUnit(str, Enum):
    VERTEX_SHADER = "VS"
    COMPUTE_SHADER = "CS"
    HULL_SHADER = "HS"
    DOMAIN_SHADER = "DS"
    GEOMETRY_SHADER = "GS"
    PIXEL_SHADER = "PS"


class ShaderParam:
    def __init__(
        self,
        Layout: str,
        Slot: Slot,
        Unit: list[ShaderUnit],
        Constants: ShaderParamConstants,
    ):
        self.Layout = Layout
        self.Slot = Slot
        self.Unit = Unit
        self.Constants = Constants


class Template:
    def __init__(self, File: str, Material: str):
        self.File = File
        self.Material = Material


class SamplerFilter(str, Enum):
    ANISOTROPIC = "ANISOTROPIC"
    POINT_MIP_POINT = "POINT_MIP_POINT"
    POINT_MIP_LINEAR = "POINT_MIP_LINEAR"
    LINEAR_MIP_POINT = "LINEAR_MIP_POINT"
    LINEAR_MIP_LINEAR = "LINEAR_MIP_LINEAR"


class SamplerAddress(str, Enum):
    WRAP = "WRAP"
    MIRROR = "MIRROR"
    CLAMP = "CLAMP"
    BORDER = "BORDER"
    MIRROR_ONCE = "MIRROR_ONCE"


class Sampler:
    def __init__(
        self,
        Slot: Slot,
        Unit: ShaderUnit,
        Filter: SamplerFilter,
        MaxAnisotropy: int,
        Address: SamplerAddress,
    ):
        self.Slot = Slot
        self.Unit = Unit
        self.Filter = Filter
        self.MaxAnisotropy = MaxAnisotropy
        self.Address = Address


class BlendLocation(str, Enum):
    ZERO = "ZERO"
    ONE = "ONE"
    SRC_COLOR = "SRC_COLOR"
    INV_SRC_COLOR = "INV_SRC_COLOR"
    SRC_ALPHA = "SRC_ALPHA"
    INV_SRC_ALPHA = "INV_SRC_ALPHA"
    DEST_ALPHA = "DEST_ALPHA"
    INV_DEST_ALPHA = "INV_DEST_ALPHA"
    DEST_COLOR = "DEST_COLOR"
    INV_DEST_COLOR = "INV_DEST_COLOR"
    SRC_ALPHA_SAT = "SRC_ALPHA_SAT"
    BLEND_FACTOR = "BLEND_FACTOR"
    INV_BLEND_FACTOR = "INV_BLEND_FACTOR"
    SRC1_COLOR = "SRC1_COLOR"
    INV_SRC1_COLOR = "INV_SRC1_COLOR"
    SRC1_ALPHA = "SRC1_ALPHA"
    INV_SRC1_ALPHA = "INV_SRC1_ALPHA"


class BlendOperation(str, Enum):
    ADD = "ADD"
    SUBTRACT = "SUBTRACT"
    REVSUBTRACT = "REVSUBTRACT"
    MIN = "MIN"
    MAX = "MAX"


class Blend:
    def __init__(
        self,
        Enable: bool,
        Src: BlendLocation,
        Dst: BlendLocation,
        Op: BlendOperation,
        SrcAlpha: BlendLocation,
        DstAlpha: BlendLocation,
        OpAlpha: BlendOperation,
    ):
        self.Enable = Enable
        self.Src = Src
        self.Dst = Dst
        self.Op = Op
        self.SrcAlpha = SrcAlpha
        self.DstAlpha = DstAlpha
        self.OpAlpha = OpAlpha


class Material:
    def __init__(
        self,
        Name: str,
        Textures: list[Texture],
        Flags: Flag,
        ShaderParams: list[ShaderParam],
        Template: Template,
        Samplers: list[Sampler],
        Blend: Blend,
    ):
        self.Name = Name
        self.Textures = Textures
        self.Flags = Flags
        self.ShaderParams = ShaderParams
        self.Template = Template
        self.Samplers = Samplers
        self.Blend = Blend

    @classmethod
    def get_default(cls, material_name):
        return Material(material_name, list(), None, list(), Template("BML", "BML-Default"), None, None)


class MaterialRootObject:
    def __init__(self, Materials: list[Material]):
        self.Materials = Materials


class MaterialTemplate:
    templates = dict()
    """"This class is not used directly by the Materials.mtl, it is used to represent built-in templates to the user"""
    def __init__(self, template_name, template_file_name):
        self.template_name = template_name
        self.template_file_name = template_file_name

    @classmethod
    def get_templates(cls):
        if not MaterialTemplate.templates:
            MaterialTemplate.templates = {
                # BML
                "BML-Default": MaterialTemplate("BML-Default", "BML"),
                "BML-VertexFormat": MaterialTemplate("BML-VertexFormat", "BML"),
                "BML-DefaultUnlit": MaterialTemplate("BML-DefaultUnlit", "BML"),
                "BML-DefaultSolid": MaterialTemplate("BML-DefaultSolid", "BML"),
                "BML-DefaultAlpha": MaterialTemplate("BML-DefaultAlpha", "BML"),
                "BML-AfterBurner": MaterialTemplate("BML-AfterBurner", "BML"),
                "BML-VCOCK_DISPLAYS": MaterialTemplate("BML-VCOCK_DISPLAYS", "BML"),
                "BML-VCOCK_CANOPY": MaterialTemplate("BML-VCOCK_CANOPY", "BML"),
                "BML-BillboardGlowLight": MaterialTemplate("BML-BillboardGlowLight", "BML"),

                # PBR
                "DiffuseIrradiance": MaterialTemplate("DiffuseIrradiance", "PBR"),
                "SpecularIrradiance": MaterialTemplate("SpecularIrradiance", "PBR"),
                "BRDF": MaterialTemplate("BRDF", "PBR"),
                "PBR": MaterialTemplate("PBR", "PBR"),
                "PBR-Glass": MaterialTemplate("PBR-Glass", "PBR"),
                "PBR-Glass-Emissive": MaterialTemplate("PBR-Glass-Emissive", "PBR"),
                "PBR-DefaultAlpha": MaterialTemplate("PBR-DefaultAlpha", "PBR"),
                
                # Glass templates with proper settings
                "BMS-Glass": MaterialTemplate("BMS-Glass", "BMS"),
                "PBR-OptimizedGlass": MaterialTemplate("PBR-OptimizedGlass", "PBR"),
            }
            
        return MaterialTemplate.templates


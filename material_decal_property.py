import bpy
from bpy.types import PropertyGroup, Material, Object, Text
from typing import TYPE_CHECKING, Generic, Literal, Optional, TypeVar
from .material_decal_localization import T

if TYPE_CHECKING:
    T = TypeVar('T')

    class Collection(list[T], Generic[T]):
        def add(self) -> T:
            pass

        def find(self, _: T) -> int:
            pass

        def __getitem__(self, _) -> T:
            pass


def depsgraph_update(self, context):
    for o in [x for x in bpy.data.materials]:
        o.update_tag(refresh=set())


def on_channel_rename(self, context):
    if len([x.name for x in get_decal_channels_props().decal_channels if x.name == self.name]) > 1:
        self.name += "(1)"
    depsgraph_update(self, context)


class DecalChannelProperties(PropertyGroup):
    if TYPE_CHECKING:
        name: str
        type: Literal["SHADER", "RGBA"]
    else:
        name: bpy.props.StringProperty(update=on_channel_rename, name=T("channel_name"))
        type: bpy.props.EnumProperty(update=depsgraph_update, name=T("decal_type"), items=[
            ("SHADER", "Shader", "Shader"),
            ("RGBA", "Color", "Color"),
        ])


class DecalChannelsRuntimeProperties(PropertyGroup):
    if TYPE_CHECKING:
        decal_channels: Collection[DecalChannelProperties]
        active_channel: int
    else:
        decal_channels: bpy.props.CollectionProperty(type=DecalChannelProperties, name=T("decal_material"))
        active_channel: bpy.props.IntProperty(update=depsgraph_update)

    def get_decal_channel(self, channel: str) -> Optional[DecalChannelProperties]:
        return self.decal_channels[channel] if self.decal_channels.find(channel) >= 0 else None

    def get_active_decal_channel(self) -> Optional[DecalChannelProperties]:
        return self.decal_channels[self.active_channel] if self.active_channel < len(self.decal_channels) and self.active_channel >= 0 else None


class DecalProjectorTargetProperties(PropertyGroup):
    if TYPE_CHECKING:
        name: str
        material: Material
        fade_out: float
    else:
        name: bpy.props.StringProperty(name=T("channel_name"))
        material: bpy.props.PointerProperty(type=Material, name=T("decal_material"))
        fade_out: bpy.props.FloatProperty(min=0, name=T("fade_out"))


class DecalProjectorProperties(PropertyGroup):
    if TYPE_CHECKING:
        targets:  Collection[DecalProjectorTargetProperties]
        active_target: int
    else:
        targets: bpy.props.CollectionProperty(type=DecalProjectorTargetProperties, name=T("target_decal_channels"))
        active_target: bpy.props.IntProperty()

    def get_target(self, channel: str) -> Optional[DecalProjectorTargetProperties]:
        return self.targets[channel] if self.targets.find(channel) >= 0 else None

    def get_active_target(self) -> Optional[DecalProjectorTargetProperties]:
        return self.targets[self.active_target] if self.active_target < len(self.targets) and self.active_target >= 0 else None


def get_decal_channels_props() -> DecalChannelsRuntimeProperties:
    if bpy.data.texts.find(".__DecalPreferences") < 0:
        bpy.data.texts.new(".__DecalPreferences")
    return bpy.data.texts[".__DecalPreferences"].material_decal


def get_decal_projector_props(object: Object) -> DecalProjectorProperties:
    return object.decal_projector


def register():
    Object.decal_projector = bpy.props.PointerProperty(
        type=DecalProjectorProperties)
    Text.material_decal = bpy.props.PointerProperty(
        type=DecalChannelsRuntimeProperties)


classes = (
    DecalChannelProperties,
    DecalChannelsRuntimeProperties,
    DecalProjectorTargetProperties,
    DecalProjectorProperties,
)

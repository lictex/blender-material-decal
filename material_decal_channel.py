from bpy.types import Operator, UIList, UILayout, Panel
from .material_decal_property import get_decal_channels_props
from .material_decal_localization import T


class DECAL_OT_add_channel(Operator):
    bl_idname = "material_decals.add_channel"
    bl_options = {'UNDO'}
    bl_label = T("add_decal_channel")

    def execute(self, context):
        props = get_decal_channels_props()
        o = props.decal_channels.add()
        o.name = "New Channel"
        props.active_channel = len(props.decal_channels) - 1

        return {'FINISHED'}


class DECAL_OT_remove_channel(Operator):
    bl_idname = "material_decals.remove_channel"
    bl_options = {'UNDO'}
    bl_label = T("remove_decal_channel")

    @classmethod
    def poll(self, context):
        return get_decal_channels_props().get_active_decal_channel() is not None

    def execute(self, context):
        props = get_decal_channels_props()
        props.decal_channels.remove(props.active_channel)
        props.active_channel = max(props.active_channel - 1, 0)

        return {'FINISHED'}


class DECAL_UL_channel(UIList):
    def draw_item(self, context, layout: UILayout, data, item, icon, active_data, active_propname):
        icon = "NODE_MATERIAL" if item.type == "SHADER" else "NODE_TEXTURE"
        layout.prop(item, "name", text="", icon=icon, emboss=False)


class DECAL_PT_channel(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = T("decals")
    bl_label = T("decals")

    def draw(self, context):
        layout = self.layout

        layout.label(text=T("decal_channels", ":"))

        row = layout.row()

        props = get_decal_channels_props()
        row.template_list("DECAL_UL_channel",
                          "",
                          props,
                          "decal_channels",
                          props,
                          "active_channel")
        col = row.column(align=True)
        col.operator("material_decals.add_channel", icon="ADD", text="")
        col.operator("material_decals.remove_channel", icon="REMOVE", text="")

        active = get_decal_channels_props().get_active_decal_channel()
        if active:
            layout.label(text=T("channel_info", ":"))
            layout.prop(active, "type")
            layout.label(icon="ERROR", text=T("warn_channel_type"))


classes = (
    DECAL_OT_add_channel,
    DECAL_OT_remove_channel,
    DECAL_PT_channel,
    DECAL_UL_channel,
)

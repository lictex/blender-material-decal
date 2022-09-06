import bpy
from bpy.types import Operator, Object, UIList, UILayout, Panel, Menu, Context, VIEW3D_MT_make_links
from .material_decal_property import get_decal_channels_props, get_decal_projector_props
from .material_decal_material import get_material_type
from .material_decal_localization import T


class DECAL_OT_copy_projector_target(Operator):
    bl_idname = "material_decals.copy_projector_settings"
    bl_options = {'UNDO'}
    bl_label = T("copy_projector_settings")

    @classmethod
    def poll(self, context):
        return bpy.context.active_object and bpy.context.active_object.type == "EMPTY"

    def execute(self, context):
        active = bpy.context.active_object
        for object in [x for x in bpy.context.selected_objects if
                       x != active and
                       x.type == "EMPTY"]:
            get_decal_projector_props(object).targets.clear()
            for target in get_decal_projector_props(active).targets:
                new_target = get_decal_projector_props(object).targets.add()
                new_target.fade_out = target.fade_out
                new_target.material = target.material
                new_target.name = target.name
            object.update_tag(refresh={"DATA"})
        return {'FINISHED'}


class DECAL_OT_add_projector_target(Operator):
    bl_idname = "material_decals.add_projector_target"
    bl_options = {'UNDO'}
    bl_label = T("add_decal_projector_target")

    def execute(self, context):
        props = get_decal_projector_props(context.object)
        o = props.targets.add()
        o.name = "New Target"
        props.active_target = len(props.targets) - 1

        return {'FINISHED'}


class DECAL_OT_remove_projector_target(Operator):
    bl_idname = "material_decals.remove_projector_target"
    bl_options = {'UNDO'}
    bl_label = T("remove_decal_projector_target")

    @classmethod
    def poll(self, context):
        props = get_decal_projector_props(context.object)
        return props.active_target < len(props.targets) and props.active_target >= 0

    def execute(self, context):
        props = get_decal_projector_props(context.object)
        props.targets.remove(props.active_target)
        props.active_target = max(props.active_target - 1, 0)

        return {'FINISHED'}


def get_target_status_icon(object: Object, channel: str):
    material_type = get_material_type(get_decal_projector_props(object).get_target(channel).material)
    props = get_decal_channels_props() .decal_channels
    channel_index = props.find(channel)
    if channel_index < 0:
        return "CANCEL"
    elif material_type != props[channel_index].type:
        return "ERROR"
    else:
        return "NODE_MATERIAL" if material_type == "SHADER" else "NODE_TEXTURE"


class DECAL_UL_projector_target(UIList):
    def draw_item(self, context, layout: UILayout, data, item, icon, active_data, active_propname):
        icon = get_target_status_icon(context.object, item.name)
        layout.prop(item, "name", text="", icon=icon, emboss=False)


class DECAL_PT_projector(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    bl_label = T("decal_projector")

    @classmethod
    def poll(cls, context):
        ob = context.object
        return (ob and ob.type == "EMPTY")

    def draw(self, context):
        object = context.object
        layout = self.layout

        layout.label(text=T("target_decal_channels", ":"))
        row = layout.row()
        row.template_list("DECAL_UL_projector_target",
                          "",
                          get_decal_projector_props(object),
                          "targets",
                          get_decal_projector_props(object),
                          "active_target")
        col = row.column(align=True)
        col.operator("material_decals.add_projector_target",
                     icon="ADD", text="")
        col.operator("material_decals.remove_projector_target",
                     icon="REMOVE", text="")

        active_target = get_decal_projector_props(object).get_active_target()
        if active_target:
            layout.label(text=T("channel_info", ":"))
            layout.use_property_split = True
            layout.use_property_decorate = False

            # only cube & sphere have the fade out option
            if object.empty_display_type in ["CUBE", "SPHERE"]:
                layout.prop(active_target, "fade_out")
            layout.prop(active_target, "material")

            info_layout = layout.split(factor=0.4)
            info_layout.column()
            info_layout = info_layout.column()

            def draw_material_status():
                material_type = get_material_type(active_target.material)
                if material_type == None:
                    return  # no material assigned
                elif material_type == "SHADER":
                    info_layout.label(text=T("shader_decal"), icon="NODE_MATERIAL")
                elif material_type == "RGBA":
                    info_layout.label(text=T("color_decal"), icon="NODE_TEXTURE")
                else:
                    if material_type == "INVALID_NO_OUTPUT":
                        info_layout.label(text=T("err_material_no_output"), icon="CANCEL")
                    elif material_type == "INVALID_MULTI_OUTPUT":
                        info_layout.label(
                            text=T("err_material_multi_output"), icon="CANCEL")
                    elif material_type == "INVALID_UNKNOWN_OUTPUT":
                        info_layout.label(
                            text=T("err_material_unknown_output"), icon="CANCEL")

            draw_material_status()

            def draw_channel_status():
                error = False
                cancel = False

                status = get_target_status_icon(object, active_target.name)
                if status == "CANCEL":
                    cancel = True
                elif status == "ERROR":
                    error = True

                if error:
                    info_layout.label(
                        text=T("err_channel_type_mismatch"), icon="ERROR")
                if cancel:
                    info_layout.label(text=T("err_channel_invalid"), icon="CANCEL")

            draw_channel_status()


def menu_copy_projector_settings(self: Menu, context: Context):
    layout = self.layout
    layout.separator()
    layout.operator("material_decals.copy_projector_settings")


def register():
    VIEW3D_MT_make_links.append(menu_copy_projector_settings)


def unregister():
    VIEW3D_MT_make_links.remove(menu_copy_projector_settings)


classes = (
    DECAL_OT_add_projector_target,
    DECAL_OT_copy_projector_target,
    DECAL_OT_remove_projector_target,
    DECAL_UL_projector_target,
    DECAL_PT_projector,
)

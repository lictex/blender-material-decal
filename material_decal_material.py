from bpy.types import Menu, Material, NodeGroup, NodeLink, Context, NODE_MT_add
from typing import cast
from .material_decal_localization import T


class DECAL_MT_material(Menu):
    bl_idname = "NODE_MT_ADD_decals"
    bl_label = T("decals")

    def draw(self, context):
        layout = self.layout

        # input node

        op = layout.operator(
            "node.add_node", text=T("decal_coords"))
        op.type = "ShaderNodeGroup"
        op.use_transform = True

        set = op.settings.add()
        set.name = "label"
        set.value = "\"" + T("decal_coords") + "\""

        set = op.settings.add()
        set.name = "node_tree"
        set.value = "bpy.data.node_groups[\".__DecalInput\"]"

        set = op.settings.add()
        set.name = "show_options"
        set.value = "False"

        # output node

        op = layout.operator(
            "node.add_node", text=T("decal_outputs"))
        op.type = "ShaderNodeGroup"
        op.use_transform = True

        set = op.settings.add()
        set.name = "label"
        set.value = "\"" + T("decal_outputs") + "\""

        set = op.settings.add()
        set.name = "node_tree"
        set.value = "bpy.data.node_groups[\".__DecalOutput\"]"

        set = op.settings.add()
        set.name = "show_options"
        set.value = "False"


def get_material_type(material: Material):
    if material == None:
        return None
    output = [] if not material.use_nodes else [x for x in cast(list[NodeGroup], material.node_tree.nodes) if
                                                x.type == "GROUP" and
                                                x.node_tree and
                                                x.node_tree.name == ".__DecalOutput"]

    if len(output) == 0:
        return "INVALID_NO_OUTPUT"

    if len(output) > 1:
        return "INVALID_MULTI_OUTPUT"

    node: NodeGroup = output[0]
    links = node.inputs["Output"].links
    if len(links) == 0:
        return "INVALID_NO_OUTPUT"

    source_type = cast(list[NodeLink], node.inputs["Output"].links)[0].from_socket.type
    if source_type in ["RGBA", "VALUE", "VECTOR"]:
        return "RGBA"
    elif source_type == "SHADER":
        return "SHADER"
    else:
        return "INVALID_UNKNOWN_OUTPUT"


def menu_add_decal_coords_node(self: Menu, context: Context):
    layout = self.layout
    layout.menu("NODE_MT_ADD_decals")


def register():
    NODE_MT_add.append(menu_add_decal_coords_node)


def unregister():
    NODE_MT_add.remove(menu_add_decal_coords_node)


classes = (
    DECAL_MT_material,
)

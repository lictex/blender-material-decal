import bpy
from bpy.types import (
    Nodes, NodeTree, Node, NodeGroup, NodeSocket, NodeLink,
    Material, Object,
    Depsgraph, DepsgraphUpdate,
    bpy_struct, bpy_prop_collection
)
from bpy.app.handlers import persistent
from mathutils import Vector
from typing import cast
from .material_decal_property import DecalProjectorTargetProperties, get_decal_channels_props, get_decal_projector_props
from .material_decal_material import get_material_type
from .material_decal_localization import T


def add_generated_group_mark(nodes: Nodes):
    frame = nodes.new("NodeFrame")
    frame.label = T("generated_node_mark")
    frame.width = 480
    frame.height = 0


def ensure_predefined_node_groups_exists():
    if bpy.data.node_groups.get(".__DecalInput") is None:
        node_group = bpy.data.node_groups.new(".__DecalInput", "ShaderNodeTree")
        add_generated_group_mark(node_group.nodes)
        node_group.outputs.new("NodeSocketVector", "Vector")
        node_group.use_fake_user = True

        texcoord_node = node_group.nodes.new("ShaderNodeTexCoord")
        texcoord_node.location[0] = 0
        texcoord_node.location[1] = -50

        output_node = node_group.nodes.new("NodeGroupOutput")
        output_node.location[0] = 200
        output_node.location[1] = -50
        node_group.links.new(texcoord_node.outputs["UV"], output_node.inputs[0])

    if bpy.data.node_groups.get(".__DecalOutput") is None:
        node_group = bpy.data.node_groups.new(".__DecalOutput", "ShaderNodeTree")
        add_generated_group_mark(node_group.nodes)
        node_group.inputs.new("NodeSocketShader", "Output")
        s = node_group.inputs.new("NodeSocketFloat", "Alpha")
        s.min_value = 0
        s.max_value = 1
        s.default_value = 1
        node_group.use_fake_user = True

        group_inputs = node_group.nodes.new("NodeGroupInput")
        group_inputs.location[0] = 0
        group_inputs.location[1] = -50

        transparent_node = node_group.nodes.new("ShaderNodeBsdfTransparent")
        transparent_node.location[0] = 200
        transparent_node.location[1] = -50

        mix_node = node_group.nodes.new("ShaderNodeMixShader")
        mix_node.location[0] = 400
        mix_node.location[1] = -50
        node_group.links.new(group_inputs.outputs[0], mix_node.inputs[2])
        node_group.links.new(transparent_node.outputs[0], mix_node.inputs[1])
        node_group.links.new(group_inputs.outputs[1], mix_node.inputs[0])

        output_node = node_group.nodes.new("ShaderNodeOutputMaterial")
        output_node.location[0] = 600
        output_node.location[1] = -50
        node_group.links.new(mix_node.outputs[0], output_node.inputs[0])


def get_socket_index(socket: NodeSocket) -> int:
    return int(socket.path_from_id()[:-1].split("[")[-1])


def copy_node_tree(source: NodeTree, target: NodeTree) -> list[Node]:
    def copy_attrs(source: bpy_struct, target: bpy_struct):
        for attr_name in [x.identifier for x in source.bl_rna.properties if
                          not x.identifier.startswith("bl_") and
                          x.identifier not in bpy_struct.__dict__.keys() and
                          x.identifier not in ["inputs", "outputs"]]:
            attr = getattr(source, attr_name)
            attr_target = getattr(target, attr_name)
            if hasattr(target, "is_property_readonly") and not target.is_property_readonly(attr_name):
                setattr(target, attr_name, attr)
            elif isinstance(attr, bpy_prop_collection):
                if hasattr(attr, "new"):
                    args = [0 for x in attr.rna_type.functions["new"].parameters if not x.is_output]
                    while len(attr_target) < len(attr):
                        attr_target.new(*args)
                for i in range(len(attr_target)):
                    if hasattr(attr[i], "bl_rna"):
                        copy_attrs(attr[i], attr_target[i])
                    else:
                        attr[i] = attr_target[i]
            elif hasattr(attr, "bl_rna") and not hasattr(attr, attr_name):
                copy_attrs(attr, attr_target)

    # copy nodes
    new_nodes = []
    name_map = {}
    for source_node in source.nodes:
        target_node = target.nodes.new(source_node.bl_idname)
        copy_attrs(source_node, target_node)
        for i in range(len(target_node.inputs)):
            copy_attrs(source_node.inputs[i], target_node.inputs[i])
        for i in range(len(target_node.outputs)):
            copy_attrs(source_node.outputs[i], target_node.outputs[i])
        new_nodes.append(target_node)
        name_map[source_node.name] = target_node.name

    # copy links
    for source_node in source.nodes:
        target_node = target.nodes[name_map[source_node.name]]

        for i, source_input in enumerate(source_node.inputs):
            for source_link in source_input.links:
                target.links.new(target.nodes[name_map[source_link.from_node.name]].outputs[get_socket_index(source_link.from_socket)], target_node.inputs[i])

    return new_nodes


def calc_nodes_bounds(nodes: list[Node]) -> tuple[float, float, float, float]:
    min_x = min_y = 2147483647
    max_x = max_y = -2147483648
    for node in nodes:
        min_x = min(node.location.x, min_x)
        min_y = min(node.location.y, min_y)
        max_x = max(node.location.x + node.dimensions.x, max_x)
        max_y = max(node.location.y + node.dimensions.y, max_y)
    return (min_x, min_y, max_x, max_y)


def move_nodes(nodes: list[Node], x: float, y: float):
    for node in nodes:
        node.location.x += x
        node.location.y += y


def generate_nodes():
    # get projectors
    decal_channels = get_decal_channels_props().decal_channels
    actions_list = []
    for projector_props_list in [get_decal_projector_props(x) for x in bpy.data.objects if
                                 x.users_collection and  # filter out deleted objects
                                 x.type == "EMPTY" and
                                 len(get_decal_projector_props(x).targets) > 0]:
        for target_props in projector_props_list.targets:
            i = decal_channels.find(target_props.name)
            if i < 0:
                continue  # not exist

            if decal_channels[i].type != get_material_type(target_props.material):
                continue  # type mismatch

            actions_list.append((target_props.name, target_props))

    actions: dict[str, list[DecalProjectorTargetProperties]] = {}
    for i in actions_list:
        actions.setdefault(i[0], []).append(i[1])

    for node_tree in [x for x in bpy.data.node_groups if x.name.startswith("__Decal")]:
        # remove fake user on decal receivers to drop unused ones
        node_tree.use_fake_user = False

    # setup receiver groups
    for channel_name in [x.name for x in decal_channels]:
        receiver_name = "__Decal " + channel_name
        channel_type = decal_channels[channel_name].type

        node_tree = bpy.data.node_groups.get(receiver_name)
        if node_tree is None:
            node_tree = bpy.data.node_groups.new(receiver_name, "ShaderNodeTree")

        def setup_sockets(sockets):
            while len(sockets) > 1:
                sockets.remove(sockets[-1])
            if len(sockets) > 0 and sockets[0].type == channel_type:
                return
            else:
                sockets.clear()
                sockets.new("NodeSocketColor" if channel_type == "RGBA" else "NodeSocketShader", "Input")

        setup_sockets(node_tree.inputs)
        setup_sockets(node_tree.outputs)
        node_tree.use_fake_user = True

        # clear exist nodes
        node_tree.nodes.clear()
        add_generated_group_mark(node_tree.nodes)

        # create default nodes
        default_input = node_tree.nodes.new("NodeGroupInput")
        default_input.location[0] = 0
        default_input.location[1] = -50
        default_output = node_tree.nodes.new("NodeGroupOutput")
        default_output.location[0] = 200
        default_output.location[1] = -50
        node_tree.links.new(default_input.outputs[0], default_output.inputs[0])

    # generate node geoups
    for channel_name, projector_props_list in actions.items():
        receiver_name = "__Decal " + channel_name
        channel_type = decal_channels[channel_name].type

        node_tree = bpy.data.node_groups.get(receiver_name)

        # clear exist nodes
        node_tree.nodes.clear()
        add_generated_group_mark(node_tree.nodes)

        # create new nodes
        ofs = 0

        def create_node(type):
            nonlocal ofs
            n = node_tree.nodes.new(type)
            n.location[0] = ofs
            n.location[1] = -50
            ofs += 200
            return n

        group_input = create_node("NodeGroupInput")

        # loop over projectors
        prev_output = group_input.outputs[0]
        for props in [x for x in projector_props_list]:
            decal_material_nodes = copy_node_tree(props.material.node_tree, node_tree)

            # replace all .__DecalInput groups
            def replace_decal_inputs():
                decal_inputs_list = [x for x in cast(list[NodeGroup], decal_material_nodes) if
                                     x.type == "GROUP" and
                                     x.node_tree and
                                     x.node_tree.name == ".__DecalInput"]

                tex_coords_node = create_node("ShaderNodeTexCoord")
                tex_coords_node.object = props.id_data

                mapping_node = create_node("ShaderNodeMapping")
                mapping_node.vector_type = "POINT"
                mapping_node.inputs[1].default_value = Vector((0.5, 0.5, 0.5))
                mapping_node.inputs[2].default_value = Vector((0, 0, 0))
                mapping_node.inputs[3].default_value = Vector((0.5, 0.5, 0.5))
                node_tree.links.new(tex_coords_node.outputs["Object"], mapping_node.inputs[0])

                for decal_inputs in decal_inputs_list:
                    for coord_links in cast(list[NodeLink], decal_inputs.outputs[0].links):
                        node_tree.links.new(mapping_node.outputs[0], coord_links.to_socket)
                    node_tree.nodes.remove(decal_inputs)
                    decal_material_nodes.remove(decal_inputs)

                return tex_coords_node

            decal_tex_coords_node = replace_decal_inputs()

            # move decal material nodes to a proper location
            def place_copied_nodes():
                nonlocal ofs
                (min_x, min_y, max_x, max_y) = calc_nodes_bounds(decal_material_nodes)
                move_nodes(decal_material_nodes, -min_x + ofs, -max_y - 200)
                ofs += 200 + (max_x - min_x)

            place_copied_nodes()

            # replace .__DecalOutput with mix nodes
            def replace_decal_outputs():
                nonlocal prev_output
                decal_outputs = [x for x in cast(list[NodeGroup], decal_material_nodes) if
                                 x.type == "GROUP" and
                                 x.node_tree and
                                 x.node_tree.name == ".__DecalOutput"][0]

                def try_relink(source: NodeSocket, target: NodeSocket):
                    if len(source.links) == 0:
                        if type(source.default_value) is float and type(target.default_value) is not float:
                            target.default_value = [source.default_value] * 4
                        else:
                            target.default_value = source.default_value
                    else:
                        node_tree.links.new(source.links[0].from_node.outputs[get_socket_index(source.links[0].from_socket)], target)

                # additional alpha masks
                alpha_mask_output = None
                projector_type: str = props.id_data.empty_display_type
                if projector_type == "CUBE":
                    abs_node = create_node("ShaderNodeVectorMath")
                    abs_node.operation = "ABSOLUTE"
                    node_tree.links.new(decal_tex_coords_node.outputs["Object"], abs_node.inputs[0])

                    sep_node = create_node("ShaderNodeSeparateXYZ")
                    node_tree.links.new(abs_node.outputs[0], sep_node.inputs[0])

                    xy_max_node = create_node("ShaderNodeMath")
                    xy_max_node.operation = "MAXIMUM"
                    node_tree.links.new(sep_node.outputs[0], xy_max_node.inputs[0])
                    node_tree.links.new(sep_node.outputs[1], xy_max_node.inputs[1])

                    if props.fade_out > 0:  # fade out enabled
                        less_cmp_node = create_node("ShaderNodeMath")
                        less_cmp_node.operation = "LESS_THAN"
                        node_tree.links.new(xy_max_node.outputs[0], less_cmp_node.inputs[0])
                        less_cmp_node.inputs[1].default_value = 1

                        range_node = create_node("ShaderNodeMapRange")
                        range_node.data_type = "FLOAT"
                        range_node.interpolation_type = "SMOOTHERSTEP"
                        node_tree.links.new(sep_node.outputs[2], range_node.inputs[0])
                        range_node.inputs[1].default_value = 1
                        range_node.inputs[2].default_value = 1 + props.fade_out
                        range_node.inputs[3].default_value = 1
                        range_node.inputs[4].default_value = 0

                        min_node = create_node("ShaderNodeMath")
                        min_node.operation = "MINIMUM"
                        node_tree.links.new(less_cmp_node.outputs[0], min_node.inputs[0])
                        node_tree.links.new(range_node.outputs[0], min_node.inputs[1])

                        alpha_mask_output = min_node.outputs[0]
                    else:
                        yz_max_node = create_node("ShaderNodeMath")
                        yz_max_node.operation = "MAXIMUM"
                        node_tree.links.new(xy_max_node.outputs[0], yz_max_node.inputs[0])
                        node_tree.links.new(sep_node.outputs[2], yz_max_node.inputs[1])

                        less_cmp_node = create_node("ShaderNodeMath")
                        less_cmp_node.operation = "LESS_THAN"
                        node_tree.links.new(yz_max_node.outputs[0], less_cmp_node.inputs[0])
                        less_cmp_node.inputs[1].default_value = 1

                        alpha_mask_output = less_cmp_node.outputs[0]
                elif projector_type == "SPHERE":
                    length_node = create_node("ShaderNodeVectorMath")
                    length_node.operation = "LENGTH"
                    node_tree.links.new(decal_tex_coords_node.outputs["Object"], length_node.inputs[0])

                    if props.fade_out > 0:  # fade out enabled
                        range_node = create_node("ShaderNodeMapRange")
                        range_node.data_type = "FLOAT"
                        range_node.interpolation_type = "SMOOTHERSTEP"
                        node_tree.links.new(length_node.outputs["Value"], range_node.inputs[0])
                        range_node.inputs[1].default_value = 1
                        range_node.inputs[2].default_value = 1 + props.fade_out
                        range_node.inputs[3].default_value = 1
                        range_node.inputs[4].default_value = 0

                        alpha_mask_output = range_node.outputs[0]
                    else:
                        less_cmp_node = create_node("ShaderNodeMath")
                        less_cmp_node.operation = "LESS_THAN"
                        node_tree.links.new(length_node.outputs["Value"], less_cmp_node.inputs[0])
                        less_cmp_node.inputs[1].default_value = 1

                        alpha_mask_output = less_cmp_node.outputs[0]

                mix_node = create_node("ShaderNodeMixShader" if channel_type == "SHADER" else "ShaderNodeMixRGB")
                node_tree.links.new(prev_output, mix_node.inputs[1])

                # output
                try_relink(decal_outputs.inputs[0], mix_node.inputs[2])

                if alpha_mask_output:
                    alpha_mix_node = create_node("ShaderNodeMixRGB")
                    alpha_mix_node.blend_type = "MULTIPLY"
                    alpha_mix_node.inputs[0].default_value = 1
                    try_relink(decal_outputs.inputs[1], alpha_mix_node.inputs[1])
                    node_tree.links.new(alpha_mask_output, alpha_mix_node.inputs[2])
                    node_tree.links.new(alpha_mix_node.outputs[0],  mix_node.inputs[0])
                else:
                    try_relink(decal_outputs.inputs[1], mix_node.inputs[0])

                prev_output = mix_node.outputs[0]
                node_tree.nodes.remove(decal_outputs)

            replace_decal_outputs()

        group_output = create_node("NodeGroupOutput")

        node_tree.links.new(prev_output, group_output.inputs[0])


@persistent
def on_depsgraph_update(self):
    ensure_predefined_node_groups_exists()

    # check if we can skip the update
    depsgraph: Depsgraph = bpy.context.evaluated_depsgraph_get()
    updates: list[DepsgraphUpdate] = depsgraph.updates

    should_update = False

    for x in [x for x in updates if type(x.id) == Material]:
        should_update |= not get_material_type(x.id).startswith("INVALID")

    for x in [x for x in updates if type(x.id) == Object]:
        should_update |= x.id.type == "EMPTY" and not (
            x.is_updated_transform and
            not x.is_updated_geometry and
            not x.is_updated_shading
        )
        should_update |= x.id.name not in depsgraph.view_layer_eval.objects

    # more?

    if not should_update:
        return

    print("-"*32)
    print("regenerating decal groups...")
    print("-"*32)
    print("caused by:")
    for update in set([x for x in updates]):
        print(f"{update.id} (g: {update.is_updated_geometry}, s: {update.is_updated_shading}, t: {update.is_updated_transform})")
    print("-"*32)

    generate_nodes()


def register():
    bpy.app.handlers.depsgraph_update_post.append(on_depsgraph_update)


def unregister():
    bpy.app.handlers.depsgraph_update_post.remove(on_depsgraph_update)

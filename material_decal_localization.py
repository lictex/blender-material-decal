import bpy

__strlist = {
    "generated_node_mark": {
        "en_US": "GENETATED NODE GROUP - Do not Modify!",
        "zh_CN": "自动生成的节点组 - 请勿修改！"
    },
    "decal_channels": {
        "en_US": "Decal Channels",
        "zh_CN": "贴花通道"
    },
    "target_decal_channels": {
        "en_US": "Target Decal Channels",
        "zh_CN": "目标贴花通道"
    },
    "add_decal_projector_target": {
        "en_US": "Add Target",
        "zh_CN": "添加目标"
    },
    "remove_decal_projector_target": {
        "en_US": "Remove Target",
        "zh_CN": "移除目标"
    },
    "add_decal_channel": {
        "en_US": "Add Channel",
        "zh_CN": "添加通道"
    },
    "remove_decal_channel": {
        "en_US": "Remove Channel",
        "zh_CN": "移除通道"
    },
    "channel_info": {
        "en_US": "Channel Settings",
        "zh_CN": "通道选项"
    },
    "channel_name": {
        "en_US": "Channel Name",
        "zh_CN": "通道命名"
    },
    "decals": {
        "en_US": "Decals",
        "zh_CN": "贴花"
    },
    "decal_coords": {
        "en_US": "Decal Coordinates",
        "zh_CN": "贴花坐标"
    },
    "decal_outputs": {
        "en_US": "Decal Outputs",
        "zh_CN": "贴花输出"
    },
    "decal_projector": {
        "en_US": "Decal Projector",
        "zh_CN": "贴花投射"
    },
    "decal_material": {
        "en_US": "Decal Material",
        "zh_CN": "贴花材质"
    },
    "decal_type": {
        "en_US": "Decal Type",
        "zh_CN": "贴花类型"
    },
    "color_decal": {
        "en_US": "Color Decal",
        "zh_CN": "颜色贴花"
    },
    "shader_decal": {
        "en_US": "Shader Decal",
        "zh_CN": "着色器贴花"
    },
    "err_material_no_output": {
        "en_US": "Missing decal output",
        "zh_CN": "缺失贴花输出"
    },
    "err_material_multi_output": {
        "en_US": "Multiple decal outputs exist",
        "zh_CN": "存在多个贴花输出"
    },
    "err_material_unknown_output": {
        "en_US": "Unknown decal output type",
        "zh_CN": "无法推断贴花格式"
    },
    "err_channel_invalid": {
        "en_US": "Invalid channel",
        "zh_CN": "无效贴花通道"
    },
    "err_channel_type_mismatch": {
        "en_US": "Channel type mismatch",
        "zh_CN": "通道类型不匹配"
    },
    "fade_out": {
        "en_US": "Fade Out",
        "zh_CN": "渐出"
    },
    "copy_projector_settings": {
        "en_US": "Copy Decal Projector Settings",
        "zh_CN": "复制贴花投射设置"
    },
    "warn_channel_type": {
        "en_US": "Changing the decal type will break existing node links!",
        "zh_CN": "修改贴花类型会破坏已有节点连接！"
    },
}


def T(k, a=""):
    if k in __strlist:
        locale = bpy.app.translations.locale
        return __strlist[k][locale if locale in __strlist[k] else "en_US"] + a
    else:
        raise "localization error"

bl_info = {
    "name": "Material Decals",
    "author": "lictex_",
    "version": (0, 1, 0),
    "blender": (3, 3, 0),
    "description": "Auto generate decal material nodes",
    "category": "Material",
}


def register_module(c):
    if hasattr(c, "classes"):
        for clazz in c.classes:
            import bpy
            bpy.utils.register_class(clazz)
    if hasattr(c, "register"):
        c.register()


def unregister_module(c):
    if hasattr(c, "unregister"):
        c.unregister()
    if hasattr(c, "classes"):
        for clazz in c.classes:
            import bpy
            bpy.utils.unregister_class(clazz)


if "bpy" not in locals():
    from . import material_decal_property
    from . import material_decal_node_generator
    from . import material_decal_localization
    from . import material_decal_material
    from . import material_decal_projector
    from . import material_decal_channel
else:
    import importlib

    def reload(i):
        importlib.reload(i)

    if "material_decal_properties" in locals():
        reload(material_decal_property)
    if "material_decal_node_generator" in locals():
        reload(material_decal_node_generator)
    if "material_decal_localization" in locals():
        reload(material_decal_localization)
    if "material_decal_material" in locals():
        reload(material_decal_material)
    if "material_decal_projector" in locals():
        reload(material_decal_projector)
    if "material_decal_channel" in locals():
        reload(material_decal_channel)

modules = [
    material_decal_property,
    material_decal_node_generator,
    material_decal_localization,
    material_decal_material,
    material_decal_projector,
    material_decal_channel
]


def register():
    for c in modules:
        register_module(c)


def unregister():
    for c in modules:
        unregister_module(c)

    import sys
    for v in [x[0] for x in sys.modules.items()]:
        if v.startswith(__name__):
            del sys.modules[v]


if __name__ == "__main__":
    register()

another blender decal addon  

why *not* use  
* it works by generating complex materials with lots of nodes, which often affects performance drastically. ui becomes laggy after creating tens of decals, and eevee usually takes a long time to compile shaders before starting to render

basic example  
* add a new plane and create a material. replace material outputs with decal outputs. add an image texture as the base color, then link image vector to a new decal coordinates node. this is the decal material  
* in view3d panel -> decals, add a channel, keep default name  
* edit the material that needs to receive decals. insert a generated nodegroup called `__Decal New Channel` before material outputs
* add a new empty object. in the object properties, set display as to cube. add a decal target and rename it to `New Channel`. set decal material to the one created above.  
* snap the empty to receivers surface. scale, rotate and move it around
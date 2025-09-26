bl_info = {
    "name": "FastFit Primitives",
    "blender": (4, 0, 0),
    "category": "Object",
    "version": (1, 0, 0),
    "author": "Pavel Vesnin ",
    "description": "Create primitives that fit the bounding box of selected objects.",
    "support": "COMMUNITY",
}

if "bpy" in locals():
    import importlib
    importlib.reload(operators)
    importlib.reload(prefs)
else:
    from . import operators, prefs

import bpy

def register():
    operators.register()
    prefs.register()

def unregister():
    prefs.unregister()
    operators.unregister()

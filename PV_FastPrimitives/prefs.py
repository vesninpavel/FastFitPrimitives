import bpy
from bpy.props import IntProperty, EnumProperty, BoolProperty

addon_key = __package__
addon_keymaps = []

def _key_items():
    letters = [(c, c, "") for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
    specials = [("SPACE","Space",""),("ENTER","Enter",""),("TAB","Tab",""),("ESC","Esc","")] + [(f"F{i}", f"F{i}", "") for i in range(1,13)]
    return letters + specials


class FastPrimitivesPreferences(bpy.types.AddonPreferences):
    bl_idname = addon_key

    key: EnumProperty(name="Key", items=_key_items(), default='F')
    ctrl: BoolProperty(name="Ctrl", default=False)
    shift: BoolProperty(name="Shift", default=True)
    alt: BoolProperty(name="Alt", default=False)
    oskey: BoolProperty(name="OS Key", default=False)

    vertices: IntProperty(name="Default Cylinder Segments", default=32, min=3, max=1024)
    primitive_type: EnumProperty(name="Default Primitive",
                                 items=[('CYLINDER','Cylinder',''),('CUBE','Cube','')],
                                 default='CYLINDER')

    def draw(self, context):
        layout = self.layout
        layout.label(text="Fast Primitives Keymap")
        row = layout.row(align=True)
        row.prop(self, "key", text="")
        row.prop(self, "ctrl")
        row.prop(self, "shift")
        row.prop(self, "alt")
        row.prop(self, "oskey")
        layout.operator("wm.fast_primitives_reload_keymap", text="Reload Keymap")
        layout.separator()
        layout.label(text="Defaults")
        layout.prop(self, "vertices")
        layout.prop(self, "primitive_type")
        layout.label(text="After changing the key, press Reload Keymap.")


class WM_OT_FastPrimitivesReloadKeymap(bpy.types.Operator):
    bl_idname = "wm.fast_primitives_reload_keymap"
    bl_label = "Reload Fast Primitives Keymap"

    def execute(self, context):
        unregister_keymaps()
        register_keymaps()
        self.report({'INFO'}, "Fast Primitives keymap reloaded")
        return {'FINISHED'}


def register_keymaps():
    kc = bpy.context.window_manager.keyconfigs.addon
    if not kc:
        return
    try:
        prefs = bpy.context.preferences.addons[addon_key].preferences
    except Exception:
        prefs = None
    key = prefs.key if prefs else 'F'
    ctrl = prefs.ctrl if prefs else False
    shift = prefs.shift if prefs else True
    alt = prefs.alt if prefs else False
    oskey = prefs.oskey if prefs else False
    unregister_keymaps()
    km = kc.keymaps.new(name='Object Mode', space_type='EMPTY')
    try:
        kmi = km.keymap_items.new("object.pv_primitive_bb", type=key, value='PRESS',
                                  ctrl=ctrl, shift=shift, alt=alt, oskey=oskey)
        addon_keymaps.append((km, kmi))
    except Exception:
        pass

def unregister_keymaps():
    kc = bpy.context.window_manager.keyconfigs.addon
    if not kc:
        addon_keymaps.clear()
        return
    for km, kmi in list(addon_keymaps):
        try:
            km.keymap_items.remove(kmi)
        except Exception:
            pass
    addon_keymaps.clear()

classes = (FastPrimitivesPreferences, WM_OT_FastPrimitivesReloadKeymap)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    register_keymaps()

def unregister():
    unregister_keymaps()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
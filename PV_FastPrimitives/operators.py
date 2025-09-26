import bpy
from bpy.props import IntProperty, EnumProperty, StringProperty
from mathutils import Vector

addon_key = __package__ if (__package__ and __package__ != "") else __name__
addon_keymaps = []


def compute_bbox(obj):
    """Compute center, size and rotation of the object's bounding box in world space."""
    min_corner = Vector(obj.bound_box[0])
    max_corner = Vector(obj.bound_box[6])
    size_local = max_corner - min_corner
    center_local = (max_corner + min_corner) / 2
    center_world = obj.matrix_world @ center_local
    rotation_euler = obj.matrix_world.decompose()[1].to_euler()
    return center_world, size_local, rotation_euler


class PV_OT_CreatePrimitiveBB(bpy.types.Operator):
    bl_idname = "object.pv_primitive_bb"
    bl_label = "Create Primitive from Bounding Box"
    bl_options = {'REGISTER', 'UNDO'}

    targets_csv: StringProperty(name="_targets", default="", options={'HIDDEN'})

    vertices: IntProperty(name="Cylinder Segments", default=32, min=3, max=1024)
    primitive_type: EnumProperty(
        name="Primitive Type",
        items=[('CYLINDER', "Cylinder", ""), ('CUBE', "Cube", "")],
        default='CYLINDER'
    )

    cylinder_axis: EnumProperty(
        name="Cylinder Axis",
        items=[
            ('X', "X Axis", ""),
            ('Y', "Y Axis", ""),
            ('Z', "Z Axis", ""),
        ],
        default='Z'
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "primitive_type")
        if self.primitive_type == 'CYLINDER':
            layout.prop(self, "vertices")
            layout.prop(self, "cylinder_axis")

    def _update_header(self, context):
        try:
            if context.area:
                if self.primitive_type == 'CYLINDER':
                    context.area.header_text_set(
                        f"FastPrimitives: Cylinder (Verts: {self.vertices}, Axis: {self.cylinder_axis}) — "
                        f"Wheel=Toggle, Ctrl+Wheel=Segments, C=Change Axis, LMB/Enter=Confirm"
                    )
                else:
                    context.area.header_text_set(
                        f"FastPrimitives: Cube — Wheel=Toggle, LMB/Enter=Confirm"
                    )
        except Exception:
            pass

    def _clear_header(self):
        try:
            if hasattr(self, "_area") and self._area:
                self._area.header_text_set(None)
        except Exception:
            try:
                bpy.context.area.header_text_set(None)
            except Exception:
                pass

    def create_cylinder(self, context, center, rotation, size, obj, preview=False):
        radius = min(size.x, size.y) / 2
        height = size.z
        
        if self.cylinder_axis == 'Z':
            radius = min(size.x, size.y) / 2
            height = size.z
            extra_rot = (0, 0, 0)
        elif self.cylinder_axis == 'X':
            radius = min(size.y, size.z) / 2
            height = size.x
            extra_rot = (0, 1.5708, 0)  # 90° вокруг Y
        else:  # Y
            radius = min(size.x, size.z) / 2
            height = size.y
            extra_rot = (1.5708, 0, 0)  # 90° вокруг X

        bpy.ops.mesh.primitive_cylinder_add(
            radius=radius,
            depth=height,
            vertices=self.vertices,
            location=center,
            rotation=(rotation[0] + extra_rot[0],
                    rotation[1] + extra_rot[1],
                    rotation[2] + extra_rot[2])
        )          
        cyl = context.object
        sc = obj.scale
        cyl.scale = (abs(sc[0]), abs(sc[1]), abs(sc[2]))
        if preview:
            cyl.name = f"FP_preview_{obj.name}"
            cyl.display_type = 'WIRE'
            cyl.hide_select = True
            cyl.hide_render = True
            try:
                cyl.show_in_front = True
            except Exception:
                pass
           
        else:
            try:
                for o in context.selected_objects:
                    o.select_set(False)
                cyl.select_set(True)
                context.view_layer.objects.active = cyl
                bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            except Exception:
                pass
        return cyl

    def create_cube(self, context, center, rotation, size, obj, preview=False):
        bpy.ops.mesh.primitive_cube_add(location=center, rotation=rotation)
        cube = context.object
        cube.scale = (size.x / 2, size.y / 2, size.z / 2)
        sc = obj.scale
        cube.scale = (
            cube.scale[0] * abs(sc[0]),
            cube.scale[1] * abs(sc[1]),
            cube.scale[2] * abs(sc[2])
        )
        if preview:
            cube.name = f"FP_preview_{obj.name}"
            cube.display_type = 'WIRE'
            cube.hide_select = True
            cube.hide_render = True
            try:
                cube.show_in_front = True
            except Exception:
                pass
            
        else:
            try:
                for o in context.selected_objects:
                    o.select_set(False)
                cube.select_set(True)
                context.view_layer.objects.active = cube
                bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            except Exception:
                pass
        return cube

    def _create_preview_for(self, context, obj, prim_type):
        prev_selected = list(context.selected_objects)
        prev_active = context.view_layer.objects.active
        center, size, rot = compute_bbox(obj)
        try:
            if prim_type == 'CYLINDER':
                p = self.create_cylinder(context, center, rot, size, obj, preview=True)
            else:
                p = self.create_cube(context, center, rot, size, obj, preview=True)
        finally:
            try:
                p.select_set(False)
            except Exception:
                pass
            try:
                for o in context.selected_objects:
                    o.select_set(False)
                for o in prev_selected:
                    o.select_set(True)
                context.view_layer.objects.active = prev_active
            except Exception:
                pass
        return p

    def _create_previews(self, context):
        self._clear_previews()
        self._targets = list(context.selected_objects)
        self._previews = []
        if not self._targets:
            return
        for tgt in self._targets:
            try:
                p = self._create_preview_for(context, tgt, self.primitive_type)
                self._previews.append(p)
            except Exception:
                pass

    def _remove_all_preview_objects(self):
        try:
            for obj in list(bpy.data.objects):
                if obj and obj.name.startswith("FP_preview_"):
                    bpy.data.objects.remove(obj, do_unlink=True)
            for mesh in list(bpy.data.meshes):
                if mesh.users == 0:
                    bpy.data.meshes.remove(mesh)
        except Exception:
            pass

    def _clear_previews(self, restore_shading=True):
        self._remove_all_preview_objects()
        self._previews = []

    def _update_previews(self, context):
        self._clear_previews()
        self._create_previews(context)

    def invoke(self, context, event):
        if not context.selected_objects:
            self.report({'WARNING'}, "No objects selected.")
            return {'CANCELLED'}
        if context.area is None or context.area.type != 'VIEW_3D':
            return self.execute(context)
        self._area = context.area
        self._targets = list(context.selected_objects)
        try:
            self.targets_csv = "|".join([o.name for o in self._targets if o])
        except Exception:
            self.targets_csv = ""
        self._create_previews(context)
        context.window_manager.modal_handler_add(self)
        self._update_header(context)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'C' and event.value == 'PRESS':
            if self.cylinder_axis == 'Z':
                self.cylinder_axis = 'X'
            elif self.cylinder_axis == 'X':
                self.cylinder_axis = 'Y'
            else:
                self.cylinder_axis = 'Z'
            self._update_previews(context)
            self._update_header(context)
            return {'RUNNING_MODAL'}
        
        if event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'} and event.value == 'PRESS':
            if event.ctrl:
                if self.primitive_type == 'CYLINDER':
                    step = 1 if event.type == 'WHEELUPMOUSE' else -1
                    self.vertices = max(3, min(1024, self.vertices + step))
                    self._update_header(context)
                    self._update_previews(context)
            else:
                self.primitive_type = 'CUBE' if self.primitive_type == 'CYLINDER' else 'CYLINDER'
                self._update_header(context)
                self._update_previews(context)
            return {'RUNNING_MODAL'}
        if (event.type in {'LEFTMOUSE', 'RET', 'NUMPAD_ENTER'}) and event.value == 'PRESS':
            self._clear_header()
            self._clear_previews()
            return self.execute(context)
        if (event.type in {'RIGHTMOUSE', 'ESC'}) and event.value == 'PRESS':
            self._clear_header()
            self._clear_previews()
            self.report({'INFO'}, "FastPrimitives: cancelled")
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}

    def execute(self, context):
        names = []
        try:
            if getattr(self, 'targets_csv', ''):
                names = [n for n in self.targets_csv.split('|') if n]
        except Exception:
            names = []
        targets = [bpy.data.objects.get(n) for n in names] if names else list(context.selected_objects)
        targets = [o for o in targets if o]
        if not targets:
            self.report({'WARNING'}, "No valid targets.")
            return {'CANCELLED'}
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        prefs = None
        try:
            prefs = context.preferences.addons[addon_key].preferences
        except Exception:
            prefs = None
        for obj in targets:
            try:
                center, size, rot = compute_bbox(obj)
            except ReferenceError:
                continue
            except Exception:
                continue
            if prefs:
                if self.vertices == 32:
                    self.vertices = prefs.vertices
                if self.primitive_type == 'CYLINDER' and prefs.primitive_type != 'CYLINDER':
                    self.primitive_type = prefs.primitive_type
            if self.primitive_type == 'CYLINDER':
                self.create_cylinder(context, center, rot, size, obj, preview=False)
            else:
                self.create_cube(context, center, rot, size, obj, preview=False)
            try:
                bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='BOUNDS')
            except Exception:
                pass
        return {'FINISHED'}
    
classes = (PV_OT_CreatePrimitiveBB,)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
import bpy


def remove_geometry_blocks():
    for o in bpy.context.scene.objects:
        if "Geometry" in o.name:
            o.select_set(True)
        else:
            o.select_set(False)
    bpy.ops.object.delete()


def remove_collisions_blocks():
    for o in bpy.context.scene.objects:
        if "(Collisions)" in o.name:
            o.select_set(True)
        else:
            o.select_set(False)
    bpy.ops.object.delete()


def select_all_objects():
    deleteListObjects = ['MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'HAIR', 'POINTCLOUD', 'VOLUME', 'GPENCIL',
                         'ARMATURE', 'LATTICE', 'EMPTY', 'LIGHT', 'LIGHT_PROBE', 'CAMERA', 'SPEAKER']
    for o in bpy.context.scene.objects:
        for i in deleteListObjects:
            if o.type == i:
                o.select_set(False)
            else:
                o.select_set(True)


def view_selected_objects():
    select_all_objects()
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            ctx = bpy.context.copy()
            ctx['area'] = area
            ctx['region'] = area.regions[-1]
            bpy.ops.view3d.view_selected(ctx)


def set_viewport_clips(clip_start, clip_end):
    for a in bpy.context.screen.areas:
        if a.type == 'VIEW_3D':
            for s in a.spaces:
                if s.type == 'VIEW_3D':
                    s.clip_start = clip_start
                    s.clip_end = clip_end


def delete_all_objects():
    select_all_objects()
    bpy.ops.object.delete()

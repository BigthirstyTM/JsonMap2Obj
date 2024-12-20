from .constants import *
from .utils.blocks_utils import *
from .utils.blender_utils import *
from bpy.props import StringProperty, PointerProperty
import bpy
import os
import mathutils
from mathutils import Euler
import json
import math
import time

ADDON_ROOT_PATH = os.path.dirname(__file__)

bl_info = {
    "name": "JsonMap2Obj",
    "author": "Team Dojo",
    "description": "Recreate any map, automatically, block by block",
    "blender": (4, 3, 0),  # Updated to match your Blender version
    "version": (0, 0, 2),
    "location": "View3D",
    "warning": "",
    "category": "Trackmania",
    "doc_url": "https://github.com/BigthirstyTM/JsonMap2Obj"
}
# GLOBALS

block_name_to_mesh_obj = {}

block_name_to_obj_path = {}
textures = {}

blocks_json = None
total_block_count = 0
placed_block_count = 0


# IO UTILS

def load_map_json(json_file_path):
    global blocks_json
    with open(json_file_path) as f:
        blocks_json = json.load(f)
        nadeo_blocks_length = len(blocks_json['nadeoBlocks'])
        freemode_blocks_length = len(blocks_json['freeModeBlocks'])
        anchored_objects_length = len(blocks_json['anchoredObjects'])

        total_block_count = nadeo_blocks_length + \
            freemode_blocks_length + \
            anchored_objects_length

        print("Total block count:", str(total_block_count))


# BLOCKS UTILS

def get_blocks_recursively(root_folder):
    for file in os.listdir(root_folder):
        if file.endswith('.obj'):
            splitted = file.split(".")
            block_name = splitted[0]
            block_mesh_absolute_path = root_folder + "/" + file
            block_name_to_obj_path[block_name] = block_mesh_absolute_path

    sub_folders = [f.path for f in os.scandir(root_folder) if f.is_dir()]
    for sub_folder in sub_folders:
        get_blocks_recursively(sub_folder)


def get_blocks_meshes(root_folder):
    get_blocks_recursively(root_folder)
    print("Found", len(block_name_to_obj_path),
          "block meshes in folder", root_folder)


def get_textures(textures_path):
    for file in os.listdir(textures_path):
        if file.endswith('.dds') or file.endswith('.png'):
            texture_base_name = ""
            if '_' in file:
                texture_base_name = file.split("_")[0]
            elif "." in file:
                texture_base_name = file.split(".")[0]

            if len(texture_base_name) > 0 and texture_base_name not in textures:
                textures[texture_base_name] = []
            if textures[texture_base_name] != None:
                textures[texture_base_name].append(file)

    print("Found", len(textures), "textures in folder", textures_path)


def check_user_inputs():
    if bpy.context.scene.json_file != "":
        if blocks_json is None:
            load_map_json(bpy.context.scene.json_file)
    if bpy.context.scene.obj_folder != "":
        if len(block_name_to_obj_path) == 0:
            get_blocks_meshes(bpy.context.scene.obj_folder)
    if bpy.context.scene.dds_folder != "":
        if len(textures) == 0:
            get_textures(bpy.context.scene.dds_folder)
# MAIN


class MyAddonPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "JsonMap2Obj"
    bl_idname = "OBJECT_PT_my_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "JsonMap2Obj"
    bl_options = {'DEFAULT_CLOSED'}  # Added for better UX in Blender 4

    def draw(self, context):
        layout = self.layout
        # ... (rest of the panel code remains the same)

        # Add a button to browse for the map JSON file
        layout.label(text="Browse for map JSON file:")
        row = layout.row()
        row.prop(context.scene, "json_file", text="")
        row.operator("myaddon.browse_json", text="Browse")

        # Add a button to browse for the OBJ folder
        layout.label(text="Browse for blocks OBJ folder:")
        row = layout.row()
        row.prop(context.scene, "obj_folder", text="")
        row.operator("myaddon.browse_obj", text="Browse")

        # Add a button to browse for the DDS folder
        layout.label(text="Browse for textures DDS folder:")
        row = layout.row()
        row.prop(context.scene, "dds_folder", text="")
        row.operator("myaddon.browse_dds", text="Browse")

        # Add a button to build the map
        layout.separator()
        layout.label(text="Build map:")
        row = layout.row()
        row.operator("myaddon.build_map", text="Build")

        # Add a button to browse for the block output folder
        layout.label(text="Browse for blocks output folder:")
        row = layout.row()
        row.prop(context.scene, "block_folder_output", text="")
        row.operator("myaddon.browse_block_folder_output", text="Browse")

        # Add a button to place a single block
        layout.separator()
        row = layout.row()
        row.prop(context.scene, "my_string")
        row.operator("my.print_string", text="Export block")

        # Add a button to place and export every block
        layout.separator()
        layout.label(text="Export all blocks:")
        row = layout.row()
        row.operator("myaddon.export_all_blocks", text="Export")


def update_single_block_name(self, context):
    global my_string
    my_string = context.scene.my_string


def build_single_block(block_name):
    delete_all_objects()
    block_path = block_name_to_obj_path.get(block_name)

    if block_path:
        try:
            # Changed from import_scene.obj to wm.obj_import
            bpy.ops.wm.obj_import(filepath=block_path)
            if bpy.context.selected_objects:
                mesh_obj = bpy.context.selected_objects[0]
                block_name_to_mesh_obj[block_name] = mesh_obj
                add_textures()
            else:
                print(f"Warning: No objects were imported for block {block_name}")
        except Exception as e:
            print(f"Error importing block {block_name}: {str(e)}")

def export_all_blocks():
    for block_name in block_name_to_obj_path:
        build_single_block(block_name)
        export_single_block(block_name)


def export_single_block(block_name):
    block_path = bpy.context.scene.block_folder_output + "/" + block_name + ".obj"
    print("Exporting block", block_name, "to path", block_path)
    bpy.ops.export_scene.obj(filepath=block_path)

    # replace mtl texture paths with relative paths
    mtl_path = bpy.context.scene.block_folder_output + "/" + block_name + ".mtl"
    with open(mtl_path, "r") as mtl_file:
        mtl_lines = mtl_file.readlines()
    with open(mtl_path, "w") as mtl_file:
        for line in mtl_lines:
            if line.startswith("map_Kd"):
                # map_Kd D:\\Downloads\\DefaultTextures\\Image_PNG\\DecoHill2_D.png
                line = "map_Kd textures\\\\" + line.split("\\")[-1]
            mtl_file.write(line)


class EXPORT_SINGLE_BLOCK_OT_OPTERATOR(bpy.types.Operator):
    """Export single block"""
    bl_idname = "my.print_string"
    bl_label = "Export single block"

    def execute(self, context):
        global my_string
        global block_name_to_mesh_obj

        # delete_all_objects()

        block_name = context.scene.my_string
        build_single_block(block_name)
        export_single_block(block_name)
        return {'FINISHED'}


class MyAddonBrowseJSON(bpy.types.Operator):
    """Operator to browse for the JSON file"""
    bl_idname = "myaddon.browse_json"
    bl_label = "Browse for JSON file"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        context.scene.json_file = self.filepath
        print("Selected JSON file: " + self.filepath)
        load_map_json(self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class MyAddonBrowseOBJ(bpy.types.Operator):
    """Operator to browse for the OBJ folder"""
    bl_idname = "myaddon.browse_obj"
    bl_label = "Browse for OBJ folder"

    filepath: bpy.props.StringProperty(subtype="DIR_PATH")

    def execute(self, context):
        context.scene.obj_folder = self.filepath
        get_blocks_meshes(self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class MyAddonBrowseDDS(bpy.types.Operator):
    """Operator to browse for the DDS folder"""
    bl_idname = "myaddon.browse_dds"
    bl_label = "Browse for DDS folder"

    filepath: bpy.props.StringProperty(subtype="DIR_PATH")

    def execute(self, context):
        context.scene.dds_folder = self.filepath
        get_textures(self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class MyAddonBuildMap(bpy.types.Operator):
    """Operator to build the map"""
    bl_idname = "myaddon.build_map"
    bl_label = "Build map"

    def execute(self, context):
        check_user_inputs()
        build_map()
        return {'FINISHED'}


class MyAddonExportAllBlocks(bpy.types.Operator):
    """Operator to export all blocks"""
    bl_idname = "myaddon.export_all_blocks"
    bl_label = "Export all blocks"

    def execute(self, context):
        export_all_blocks()
        return {'FINISHED'}


class MyAddonBrowseBlockFolderOutput(bpy.types.Operator):
    """Operator to browse for the block folder output"""
    bl_idname = "myaddon.browse_block_folder_output"
    bl_label = "Browse for block folder output"

    filepath: bpy.props.StringProperty(subtype="DIR_PATH")

    def execute(self, context):
        context.scene.block_folder_output = self.filepath
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


def place_blocks():
    start = time.time()

    # Loop over the blocks and import the corresponding mesh objects
    all_named_blocks = blocks_json['nadeoBlocks'] + \
        blocks_json['freeModeBlocks'] + \
        blocks_json["anchoredObjects"]

    for block in all_named_blocks:
        block_name = block['name']
        if block_name not in block_name_to_mesh_obj:
            block_path = block_name_to_obj_path.get(block_name)
            if block_path:
                try:
                    # Changed from import_scene.obj to wm.obj_import
                    bpy.ops.wm.obj_import(filepath=block_path)
                    if bpy.context.selected_objects:
                        mesh_obj = bpy.context.selected_objects[0]
                        block_name_to_mesh_obj[block_name] = mesh_obj
                    else:
                        print(f"Warning: No objects were imported for block {block_name}")
                except Exception as e:
                    print(f"Error importing block {block_name}: {str(e)}")

    # Loop over the blocks and create instances of the mesh objects
    for nadeo_block in blocks_json['nadeoBlocks']:
        block_name = nadeo_block['name']

        if block_name in block_name_to_mesh_obj:
            mesh_obj = block_name_to_mesh_obj[block_name]

            position = calc_block_coord(nadeo_block)

            rotation = Euler((0,
                              (math.pi / 2) * (4 - ((nadeo_block['dir']) % 4)),
                              0))

            rotation_mode = "XYZ"

            # Create an instance of the mesh object
            instance = mesh_obj.copy()
            instance.data = mesh_obj.data.copy()
            instance.location = position
            instance.rotation_euler = rotation
            instance.rotation_mode = rotation_mode
            instance.name = block_name

            # Link the instance to the current collection
            bpy.context.collection.objects.link(instance)

            # print("Placed", blockName, "at position", realPos)
        else:
            print(block_name, "not in mesh dict")

    for freemode_block in blocks_json['freeModeBlocks']:
        block_name = freemode_block['name']

        if block_name in block_name_to_mesh_obj:
            mesh_obj = block_name_to_mesh_obj[block_name]

            position = (freemode_block['pos'][0],
                        freemode_block['pos'][1],
                        freemode_block['pos'][2])

            rotation = Euler((freemode_block['rot'][1],
                              freemode_block['rot'][0],
                              freemode_block['rot'][2]))

            rotation_mode = 'XZY'  # Experiment with rotations, not working yet

            # Create an instance of the mesh object
            instance = mesh_obj.copy()
            instance.data = mesh_obj.data.copy()
            instance.location = position
            instance.rotation_euler = rotation
            instance.rotation_mode = rotation_mode
            instance.name = block_name

            # Link the instance to the current collection
            bpy.context.collection.objects.link(instance)

            # print("Placed", blockName, "at position", realPos)
        else:
            print(block_name, "not in mesh dict")

    # for anchored_object in blocks_json["anchoredObjects"]:
    #     block_name = anchored_object['name']

    #     # Place cube at position of the anchored object, with correct rotation
    #     bpy.ops.mesh.primitive_cone_add(location=position,
    #                                     vertices=8,
    #                                     scale=(2.0, 2.0, 2.0))
    #     bpy.context.object.rotation_euler = rotation
    #     bpy.context.object.rotation_mode = rotation_mode
    #     bpy.context.object.name = block_name

    #     # Color the cube red
    #     bpy.context.object.data.materials.append(
    #         bpy.data.materials.new(name="Red"))
    #     bpy.context.object.data.materials[0].diffuse_color = (1, 0, 0, 1)

    #     if block_name in block_name_to_mesh_obj:
    #         mesh_obj = block_name_to_mesh_obj[block_name]

    #         position = (anchored_object['pos'][0],
    #                     anchored_object['pos'][1],
    #                     anchored_object['pos'][2])

    #         rotation = Euler((anchored_object['pitch'],
    #                           anchored_object['yaw'],
    #                           anchored_object['roll']))

    #         rotation_mode = 'YXZ'

    #         # Create an instance of the mesh object
    #         instance = mesh_obj.copy()
    #         instance.data = mesh_obj.data.copy()
    #         instance.location = position
    #         instance.rotation_euler = rotation
    #         instance.rotation_mode = rotation_mode
    #         instance.name = block_name

    #         # Link the instance to the current collection
    #         bpy.context.collection.objects.link(instance)

    #     # print("Placed", blockName, "at position", realPos)
    #     else:
    #         print(block_name, "not in mesh dict")

    # Remove the imported mesh objects and only keep the instances
    remove_geometry_blocks()

    end = time.time()
    print("Placed", len(blocks_json['nadeoBlocks']), "blocks in",
          end - start, "seconds")


def add_textures():
    start = time.time()

    texture_dict = {}
    materials_dict = {}
    missing_materials = []

    # Iterate through every object in the scene
    for object in bpy.context.scene.objects:
        if not hasattr(object.data, "materials"):
            continue
            
        # Iterate through every material applied to the object
        for i in range(len(object.data.materials)):
            material = object.data.materials[i]
            if not material:
                continue
                
            material_path_split = material.name.split("\\")
            material_name = material_path_split[-1]
            material_name_base = str(material_name).split(".")[0]

            has_texture = material_name_base in textures

            if has_texture:
                # Check if the texture image has already been loaded
                if material_name_base in texture_dict:
                    texture_image = texture_dict[material_name_base]
                else:
                    texture_file_path = bpy.context.scene.dds_folder + \
                        textures[material_name_base][0]
                    try:
                        texture_image = bpy.data.images.load(texture_file_path)
                        texture_dict[material_name_base] = texture_image
                    except:
                        print(f"Warning: Could not load texture {texture_file_path}")
                        continue

                if material_name_base in materials_dict:
                    mat = materials_dict[material_name_base]
                else:
                    # Create a new material node tree and assign the texture image to the material
                    mat = bpy.data.materials.new(name=material_name_base)
                    mat.use_nodes = True
                    bsdf = mat.node_tree.nodes["Principled BSDF"]
                    tex_image = mat.node_tree.nodes.new('ShaderNodeTexImage')
                    tex_image.image = texture_image
                    mat.node_tree.links.new(
                        bsdf.inputs['Base Color'], tex_image.outputs['Color'])
                    materials_dict[material_name_base] = mat

                # Assign the new material to the object
                object.data.materials[i] = mat
            elif material_name_base not in missing_materials:
                print("No texture for", material_name_base)
                missing_materials.append(material_name_base)

    end = time.time()
    print("Added textures in", end - start, "seconds")


def rotate_blocks():
    start = time.time()

    # Loop through all the objects and rotate them
    for obj in bpy.context.scene.objects:
        # Calculate the rotation matrix
        rotation_matrix = mathutils.Matrix.Rotation(math.radians(90), 4, 'X')

        # Rotate the object around the world origin
        obj.matrix_world = rotation_matrix @ obj.matrix_world

    end = time.time()
    print("Rotated blocks in", end - start, "seconds")


def build_map():
    """Function to build the map"""

    set_viewport_clips(1, 50000)
    print("Building map...")

    delete_all_objects()

    # clear the mesh object dictionary as it is referencing objects that have been deleted
    block_name_to_mesh_obj.clear()

    place_blocks()
    add_textures()

    remove_collisions_blocks()

    rotate_blocks()

    view_selected_objects()


def register():
    bpy.utils.register_class(MyAddonPanel)
    bpy.utils.register_class(MyAddonBrowseJSON)
    bpy.utils.register_class(MyAddonBrowseOBJ)
    bpy.utils.register_class(MyAddonBrowseDDS)
    bpy.utils.register_class(MyAddonBuildMap)
    bpy.utils.register_class(MyAddonBrowseBlockFolderOutput)
    bpy.utils.register_class(EXPORT_SINGLE_BLOCK_OT_OPTERATOR)
    bpy.utils.register_class(MyAddonExportAllBlocks)

    bpy.types.Scene.json_file = StringProperty(name="JSON File")
    bpy.types.Scene.obj_folder = StringProperty(name="OBJ Folder")
    bpy.types.Scene.dds_folder = StringProperty(name="DDS Folder")
    bpy.types.Scene.block_folder_output = StringProperty(
        name="Block Output Folder")
    bpy.types.Scene.my_string = bpy.props.StringProperty(
        name="Block Name",
        default="",
        update=update_single_block_name
    )


def unregister():
    bpy.utils.unregister_class(MyAddonPanel)
    bpy.utils.unregister_class(MyAddonBrowseJSON)
    bpy.utils.unregister_class(MyAddonBrowseOBJ)
    bpy.utils.unregister_class(MyAddonBrowseDDS)
    bpy.utils.unregister_class(MyAddonBuildMap)
    bpy.utils.unregister_class(MyAddonBrowseBlockFolderOutput)
    bpy.utils.unregister_class(EXPORT_SINGLE_BLOCK_OT_OPTERATOR)
    bpy.utils.unregister_class(MyAddonExportAllBlocks)
    del bpy.types.Scene.json_file
    del bpy.types.Scene.obj_folder
    del bpy.types.Scene.dds_folder
    del bpy.types.Scene.block_folder_output
    block_name_to_mesh_obj.clear()

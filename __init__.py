import bpy
from bpy.props import StringProperty
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
    "blender": (3, 4, 1),
    "version": (0, 0, 1),
    "location": "View3D",
    "warning": "",
    "category": "Trackmania"
}

# CONSTANTS

BLOCK_SIZE = mathutils.Vector((32, 8, 32))

# GLOBALS

blockNameToMeshObj = {}

blockNameToObjPath = {}
textures = {}

blocksJson = None
totalBlockCount = 0
placedBlockCount = 0

# BLENDER UTILS


def removeGeometryBlocks():
    for o in bpy.context.scene.objects:
        if "Geometry." in o.name:
            o.select_set(True)
        else:
            o.select_set(False)
    bpy.ops.object.delete()


def removeCollisionsBlocks():
    for o in bpy.context.scene.objects:
        if "(Collisions)" in o.name:
            o.select_set(True)
        else:
            o.select_set(False)
    bpy.ops.object.delete()


def selectAllObjects():
    deleteListObjects = ['MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'HAIR', 'POINTCLOUD', 'VOLUME', 'GPENCIL',
                         'ARMATURE', 'LATTICE', 'EMPTY', 'LIGHT', 'LIGHT_PROBE', 'CAMERA', 'SPEAKER']
    for o in bpy.context.scene.objects:
        for i in deleteListObjects:
            if o.type == i:
                o.select_set(False)
            else:
                o.select_set(True)


def viewSelectedObjects():
    selectAllObjects()
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            ctx = bpy.context.copy()
            ctx['area'] = area
            ctx['region'] = area.regions[-1]
            bpy.ops.view3d.view_selected(ctx)


def setViewportClipEnd(clip_end):
    for a in bpy.context.screen.areas:
        if a.type == 'VIEW_3D':
            for s in a.spaces:
                if s.type == 'VIEW_3D':
                    s.clip_end = clip_end


def deleteAllObjects():
    selectAllObjects()
    bpy.ops.object.delete()

# IO UTILS


def loadMapJson(jsonFilePath):
    global blocksJson
    with open(jsonFilePath) as f:
        blocksJson = json.load(f)
        nadeoBlocksLength = len(blocksJson['nadeoBlocks'])
        freeModeBlocksLength = len(blocksJson['freeModeBlocks'])
        anchoredObjectsLength = len(blocksJson['anchoredObjects'])

        totalBlockCount = nadeoBlocksLength + \
            freeModeBlocksLength + anchoredObjectsLength
        print("Total block count:", str(totalBlockCount))

# BLOCKS UTILS


def calcBlockCoord(block):
    pos = block['pos']
    blockOffsets = block['blockOffsets']
    dir = block['dir']

    print(pos)

    meshCoord = mathutils.Vector((pos[0], pos[1] - 8, pos[2]))

    modelCoord = mathutils.Vector((0, 0, 0)) + meshCoord + mathutils.Vector((
        -BLOCK_SIZE.x / 2,
        BLOCK_SIZE.y / 2,
        -BLOCK_SIZE.z / 2,
    ))

    maxX = max([offset[0] for offset in blockOffsets]) * \
        BLOCK_SIZE[0] + BLOCK_SIZE[0]
    maxZ = max([offset[2] for offset in blockOffsets]) * \
        BLOCK_SIZE[2] + BLOCK_SIZE[2]

    positionWithOffset = mathutils.Vector((0, 0, 0)) + modelCoord + mathutils.Vector((
        (dir == 1 or dir == 2) and maxX or 0,
        0,
        (dir == 2 or dir == 3) and maxZ or 0,
    ))

    return positionWithOffset


def getBlocksRecursively(rootFolder):
    for file in os.listdir(rootFolder):
        if file.endswith('.obj'):
            splitted = file.split(".")
            blockName = splitted[0]
            blockMeshAbsolutePath = rootFolder + "/" + file
            blockNameToObjPath[blockName] = blockMeshAbsolutePath

    subFolders = [f.path for f in os.scandir(rootFolder) if f.is_dir()]
    for subFolder in subFolders:
        getBlocksRecursively(subFolder)


def getBlocksMeshes(rootFolder):
    getBlocksRecursively(rootFolder)
    print("Found", len(blockNameToObjPath),
          "block meshes in folder", rootFolder)


def getTextures(texturesPath):
    for file in os.listdir(texturesPath):
        if file.endswith('.dds'):
            textureBaseName = ""
            if '_' in file:
                textureBaseName = file.split("_")[0]
            elif "." in file:
                textureBaseName = file.split(".")[0]

            if len(textureBaseName) > 0 and textureBaseName not in textures:
                textures[textureBaseName] = []
            if textures[textureBaseName] != None:
                textures[textureBaseName].append(file)

    print("Found", len(textures), "textures in folder", texturesPath)

# MAIN


class MyAddonPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "JsonMap2Obj"
    bl_idname = "OBJECT_PT_my_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "JsonMap2Obj"

    def draw(self, context):
        layout = self.layout

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


class MyAddonBrowseJSON(bpy.types.Operator):
    """Operator to browse for the JSON file"""
    bl_idname = "myaddon.browse_json"
    bl_label = "Browse for JSON file"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        context.scene.json_file = self.filepath
        print("Selected JSON file: " + self.filepath)
        loadMapJson(self.filepath)
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
        getBlocksMeshes(self.filepath)
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
        getTextures(self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class MyAddonBuildMap(bpy.types.Operator):
    """Operator to build the map"""
    bl_idname = "myaddon.build_map"
    bl_label = "Build map"

    def execute(self, context):
        BuildMap()
        return {'FINISHED'}


# Dictionary to store the imported mesh objects


def PlaceBlocks():
    start = time.time()

    # Loop over the blocks and import the corresponding mesh objects
    for nadeoBlock in blocksJson['nadeoBlocks']:
        blockName = nadeoBlock['name']
        if blockName not in blockNameToMeshObj:
            blockPath = blockNameToObjPath.get(blockName)
            if blockPath:
                bpy.ops.import_scene.obj(filepath=blockPath)
                mesh_obj = bpy.context.selected_objects[0]
                blockNameToMeshObj[blockName] = mesh_obj

    # Loop over the blocks and create instances of the mesh objects
    for nadeoBlock in blocksJson['nadeoBlocks']:
        blockName = nadeoBlock['name']

        if blockName in blockNameToMeshObj:
            mesh_obj = blockNameToMeshObj[blockName]

            position = (nadeoBlock['pos'][0],
                        nadeoBlock['pos'][1], nadeoBlock['pos'][2])

            realPos = calcBlockCoord(nadeoBlock)

            realRot = Euler(
                (0, (math.pi / 2) * (4 - ((nadeoBlock['dir']) % 4)), 0), 'ZYX')

            # Create an instance of the mesh object
            instance = mesh_obj.copy()
            instance.data = mesh_obj.data.copy()
            instance.location = realPos
            instance.rotation_euler = realRot
            instance.name = blockName

            # Link the instance to the current collection
            bpy.context.collection.objects.link(instance)

            # print("Placed", blockName, "at position", realPos)
        else:
            print(blockName, "not in mesh dict")

    # Remove the imported mesh objects and only keep the instances
    removeGeometryBlocks()

    end = time.time()
    print("Placed", len(blocksJson['nadeoBlocks']), "blocks in",
          end - start, "seconds")


def AddTextures():
    start = time.time()

    texture_dict = {}

    # Iterate through every object in the scene
    for object in bpy.context.scene.objects:
        # Iterate through every material applied to the object
        for i in range(len(object.data.materials)):
            material = object.data.materials[i]
            materialPathSplit = material.name.split("\\")
            materialName = materialPathSplit[-1]
            materialNameBase = str(materialName).split(".")[0]

            hasTexture = materialNameBase in textures

            if hasTexture:
                # Check if the texture image has already been loaded
                if materialNameBase in texture_dict:
                    texture_image = texture_dict[materialNameBase]
                else:
                    texture_file_path = bpy.context.scene.dds_folder + \
                        textures[materialNameBase][0]
                    texture_image = bpy.data.images.load(texture_file_path)
                    texture_dict[materialNameBase] = texture_image

                # Create a new material node tree and assign the texture image to the material
                mat = bpy.data.materials.new(name=materialNameBase)
                mat.use_nodes = True
                bsdf = mat.node_tree.nodes["Principled BSDF"]
                texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
                texImage.image = texture_image
                mat.node_tree.links.new(
                    bsdf.inputs['Base Color'], texImage.outputs['Color'])

                # Assign the new material to the object
                object.data.materials[i] = mat
            else:
                print("No texture for", materialNameBase)

    end = time.time()
    print("Added textures in", end - start, "seconds")

def RotateBlocks():
    start = time.time()

    # Set the rotation angle in degrees
    rotation_angle_degrees = 90

    # Get all the objects in the scene
    scene_objects = bpy.context.scene.objects

    # Loop through all the objects and rotate them
    for obj in scene_objects:
        # Calculate the rotation matrix
        rotation_matrix = mathutils.Matrix.Rotation(math.radians(rotation_angle_degrees), 4, 'X')
        
        # Rotate the object around the world origin
        obj.matrix_world = rotation_matrix @ obj.matrix_world

    end = time.time()
    print("Rotated blocks in", end - start, "seconds")


def BuildMap():
    """Function to build the map"""
    setViewportClipEnd(50000)
    print("Building map...")
    deleteAllObjects()

    PlaceBlocks()
    AddTextures()

    removeCollisionsBlocks()

    RotateBlocks()

    viewSelectedObjects()


def register():
    bpy.utils.register_class(MyAddonPanel)
    bpy.utils.register_class(MyAddonBrowseJSON)
    bpy.utils.register_class(MyAddonBrowseOBJ)
    bpy.utils.register_class(MyAddonBrowseDDS)
    bpy.utils.register_class(MyAddonBuildMap)
    bpy.types.Scene.json_file = StringProperty(name="JSON File")
    bpy.types.Scene.obj_folder = StringProperty(name="OBJ Folder")
    bpy.types.Scene.dds_folder = StringProperty(name="DDS Folder")


def unregister():
    bpy.utils.unregister_class(MyAddonPanel)
    bpy.utils.unregister_class(MyAddonBrowseJSON)
    bpy.utils.unregister_class(MyAddonBrowseOBJ)
    bpy.utils.unregister_class(MyAddonBrowseDDS)
    bpy.utils.unregister_class(MyAddonBuildMap)
    del bpy.types.Scene.json_file
    del bpy.types.Scene.obj_folder
    del bpy.types.Scene.dds_folder
    blockNameToMeshObj.clear()

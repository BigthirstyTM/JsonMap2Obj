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
    "blender": (3, 4, 1),
    "version": (0, 0, 1),
    "location": "View3D",
    "warning": "",
    "category": "Trackmania"
}

from .utils.BlenderUtils import *

# CONSTANTS

BLOCK_SIZE = mathutils.Vector((32, 8, 32))

# GLOBALS

blockNameToMeshObj = {}

blockNameToObjPath = {}
textures = {}

blocksJson = None
totalBlockCount = 0
placedBlockCount = 0

# selectAllObjects()
# bpy.ops.object.delete()

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


def CheckUserInputs():
    if bpy.context.scene.json_file != "":
        if blocksJson is None:
            loadMapJson(bpy.context.scene.json_file)
    if bpy.context.scene.obj_folder != "":
        if len(blockNameToObjPath) == 0:
            getBlocksMeshes(bpy.context.scene.obj_folder)
    if bpy.context.scene.dds_folder != "":
        if len(textures) == 0:
            getTextures(bpy.context.scene.dds_folder)
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
        CheckUserInputs()
        BuildMap()
        return {'FINISHED'}


# Convert Pitch, Yaw, Roll tp Euler angles, quickly used ChatGPT formula for euler angles, hope it works
def euler_angles(pitch, yaw, roll):
    # Calculate the Euler angles using the Z-Y-X rotation order
    phi = math.atan2(math.sin(roll) * math.cos(pitch) * math.cos(yaw) + math.sin(pitch) * math.sin(yaw),
                     math.cos(roll) * math.cos(pitch))
    theta = math.atan2(math.sin(pitch) * math.cos(yaw),
                       math.cos(pitch))
    psi = math.atan2(math.sin(yaw) * math.cos(pitch) * math.cos(roll) + math.sin(pitch) * math.sin(roll),
                     math.cos(yaw) * math.cos(pitch))

    # Convert the Euler angles back to degrees and return them as a tuple
    return math.degrees(phi), math.degrees(theta), math.degrees(psi)

# Dictionary to store the imported mesh objects


def PlaceBlocks():
    start = time.time()

    # Loop over the blocks and import the corresponding mesh objects
    all_named_blocks = blocksJson['nadeoBlocks'] + blocksJson['freeModeBlocks']
    for block in all_named_blocks:
        blockName = block['name']
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

    for freeModeBlock in blocksJson['freeModeBlocks']:
        blockName = freeModeBlock['name']

        if blockName in blockNameToMeshObj:
            mesh_obj = blockNameToMeshObj[blockName]

            position = (freeModeBlock['pos'][0],
                        freeModeBlock['pos'][1],
                        freeModeBlock['pos'][2])

            rotation = Euler((freeModeBlock['rot'][1],
                              freeModeBlock['rot'][0],
                              freeModeBlock['rot'][2]))

            rotation_mode = 'XZY'  # Experiment with rotations, not working yet

            # Create an instance of the mesh object
            instance = mesh_obj.copy()
            instance.data = mesh_obj.data.copy()
            instance.location = position
            instance.rotation_euler = rotation
            instance.rotation_mode = rotation_mode
            instance.name = blockName

            # Link the instance to the current collection
            bpy.context.collection.objects.link(instance)

            # print("Placed", blockName, "at position", realPos)
        else:
            print(blockName, "not in mesh dict")

    # for anchoredObject in blocksJson["anchoredObjects"]:
    #     blockName = anchoredObject['name']

    #     position = (anchoredObject['pos'][0],
    #                 anchoredObject['pos'][1],
    #                 anchoredObject['pos'][2])

    #     rotation = Euler(euler_angles(anchoredObject['pitch'],
    #                                   anchoredObject['yaw'],
    #                                   anchoredObject['roll']))

    #     rotation_mode = 'ZYX'

    #     # Place cube at position of the anchored object, with correct rotation
    #     bpy.ops.mesh.primitive_cone_add(location=position,
    #                                     vertices=8,
    #                                     scale=(2.0, 2.0, 2.0))
    #     bpy.context.object.rotation_euler = rotation
    #     bpy.context.object.rotation_mode = rotation_mode
    #     bpy.context.object.name = blockName
    #     bpy.context.object.name = blockName

    #     # Color the cube red
    #     bpy.context.object.data.materials.append(
    #         bpy.data.materials.new(name="Red"))
    #     bpy.context.object.data.materials[0].diffuse_color = (1, 0, 0, 1)

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

    # Loop through all the objects and rotate them
    for obj in bpy.context.scene.objects:
        # Calculate the rotation matrix
        rotation_matrix = mathutils.Matrix.Rotation(math.radians(90), 4, 'X')

        # Rotate the object around the world origin
        obj.matrix_world = rotation_matrix @ obj.matrix_world

    end = time.time()
    print("Rotated blocks in", end - start, "seconds")


def BuildMap():
    """Function to build the map"""

    setViewportClips(1, 50000)
    print("Building map...")

    deleteAllObjects()

    # clear the mesh object dictionary as it is referencing objects that have been deleted
    blockNameToMeshObj.clear()

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


import math
import mathutils
from ..constants import *

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


def calc_block_coord(block):
    pos = block['pos']
    block_offsets = block['blockOffsets']
    dir = block['dir']

    # print(pos)

    mesh_coord = mathutils.Vector((pos[0], pos[1] - 8, pos[2]))

    model_coord = mathutils.Vector((0, 0, 0)) + mesh_coord + mathutils.Vector((
        -BLOCK_SIZE.x / 2,
        BLOCK_SIZE.y / 2,
        -BLOCK_SIZE.z / 2,
    ))

    max_x = max([offset[0] for offset in block_offsets]) * \
        BLOCK_SIZE[0] + BLOCK_SIZE[0]
    max_z = max([offset[2] for offset in block_offsets]) * \
        BLOCK_SIZE[2] + BLOCK_SIZE[2]

    position_with_offset = mathutils.Vector((0, 0, 0)) + model_coord + mathutils.Vector((
        (dir == 1 or dir == 2) and max_x or 0,
        0,
        (dir == 2 or dir == 3) and max_z or 0,
    ))

    return position_with_offset

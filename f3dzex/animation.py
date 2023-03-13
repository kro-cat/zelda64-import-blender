from collections import namedtuple
from math import radians
import numpy as np
from struct import unpack, calcsize
from warnings import warn, BytesWarning

from segment import load_segment


#TODO classes to go in package __init__

class Segment_Offset:
    segment: int
    offset: int

    def __init__(self, segment: int, offset: int):
        self.segment = segment
        self.offset = offset

    @classmethod
    def from_address(cls, address: int):
        return cls(address >> 24, address & 0x00ffffff)

    def __int__(self):
        return (self.segment << 24) | self.offset


class Animation_Header:
    num_frames: int
    rotation_values: Segment_Offset
    rotation_index: Segment_Offset
    minimum_rotation_index: int

    def __init__(self, num_frames: int, rotation_values: int,
                 rotation_index: int, minimum_rotation_index: int):
        self.num_frames = num_frames
        self.rotation_values = Segment_Offset.from_address(rotation_values)
        self.rotation_index = Segment_Offset.from_address(rotation_index)
        self.minimum_rotation_index = minimum_rotation_index

    @classmethod
    def from_bytearray(cls, bdata: bytearray):
        hdr_format = ">HxxIIHxx"
        # ssss0000 rrrrrrrr iiiiiiii llll0000
        # s: # of frames
        # r: segment offset of rotation value list
        # i: segment offset of rotation index list
        # l: rotation index limit

        # Most of these are self explanatory, but there is one that more
        # confusing, the limit. If a entry in the rotation index list is
        # greater than or equal to the limit, then for each frame the next
        # value in the rotation value list is read.

        # size_difference = calcsize(hdr_format) - len(bdata)
        size_difference = 16 - len(bdata)
        if (size_difference > 0):
            warn(f"[from_bytearray] Data length ({len(bdata)}) is too short" \
                 f" for format (min is 16). Extraneous data is undefined!",
                 Warning)
            bdata += [0] * size_difference

        anim_hdr = cls(*list(unpack(hdr_format, bdata)))
        
        return anim_hdr


class Animation:
    address: Segment_Offset
    header: Animation_Header

    def __init__(self, address: int, header: Animation_Header):
        self.address = Segment_Offset.from_address(address)
        self.header = header


def find_animations(external = False: bool):
    # Animations are found in the following segments:
    # 0x06 (Animations)
    # 0x0f (External Animations)

    segment = 0x06

    if external:
        segment = 0x0f

    animations = []

    segment_data = load_segment(segment)

    # num_chunks = len(segment_data) >> 2
    num_chunks = len(segment_data) // 4

    # sift through segment data one int (16 bytes) at a time and try to match
    # the animation header format
    for i in range(num_chunks - 1):
        offset = i * 4

        data_window = segment_data[offset:offset+16]
        header = Animation_Header.from_bytearray(data_window)

        # detect animation header
        if ((header.num_frames > 0)
                and (header.rotation_values.segment == 0x06)
                and (header.rotation_index.segment == 0x06)):
            address = Segment_Offset(segment, offset)
            log.info(f"[find_animations] Animation found at" \
                     f" 0x{int(address):08X} with {header.num_frames} frames")
            animations.append(Animation(address, header))

    num_animations = len(animations)
    if(num_animations > 0):
        log.info(f"[find_animations] Found {num_animations:d} total" \
                 f" Animations in segment 0x{segment_number:02X}")

    return animations


def load_animation(animation: Animation, heirarchy_most_bones, frame_offset):
    segment = self.segment
    n_anims = self.animTotal
    if (AnimtoPlay > 0 and AnimtoPlay <= n_anims):
        currentanim = AnimtoPlay - 1
    else:
        currentanim = 0

    rotation_index_offset = animation.header.rotation_index.offset
    rotation_values_offset = animation.header.rotation_values.offset
    minimum_rotation_index = animation.header.rotation.minimum_rotation_index

    segment_data = load_segment(animation.address.segment)
    segment_data_length = len(segment_data)

    ## Translation

    def get_value(rotation_index, frame_offset):
        # TODO document why we do this
        if (rotation_index >= minimum_rotation_index):
            rotation_index += frame_offset

        rotation_value_offset = rotation_values_offset + rotation_index
        if (rotation_value_offset > segment_data_length):
            warn(f"[load_animation] Offset ({rotation_value_offset:06X}) is" \
                 f" out of bounds (max is {segment_data_length:06X})." \
                 f" Extraneous data is undefined!", Warning)
            return 0

        return unpack_from(">h", segment_data, rotation_value_offset)[0]

    global scaleFactor
    translation_indices = list(
        unpack_from(">3h", segment_data, rotation_index_offset))
    translation = [ scaleFactor * get_value(index, frame_offset)
                   for index in translation_indices ]
    # TODO fix the funny loading: swap z and y, and y (was x) is negative

    ## Rotations

    # offset by 6 (3 * 2 bytes) because we don't associate the translation with
    # the rotations when working with bones
    rotation_index_offset += 6
    
    # not used, MUST be not relevant because we use hierarchyMostBones (its armature) as placeholder
    #seg, offset = splitOffset(hierarchy.offset)
    bone_count_max = hierarchy_most_bones.limbCount
    armature = hierarchy_most_bones.armature

    for bone_index in range(bone_count_max):
        # Had to reverse here, cuz didn't find a way to rotate bones on LOCAL space, start rotating from last to first bone on hierarchy GLOBAL.
        bIndx = ((bone_count_max - 1) - bone_index)

        rotation_indicies = list(
            unpack_from(">3h", segment_data,
                        rotation_index_offset + (6 * bIndx)))
        rotation_scale = 65535.0 / 360.0
        rotation = [ radians(get_value(index, frame_offset) / rotation_scale)
                    for index in rotation_indices ]
        # TODO fix the funny loading: swap z and y, and y (was x) is negative

        # TODO left off here

        log.trace("limb: %d XIdx: %d %d YIdx: %d %d ZIdx: %d %d frameTotal: %d", bIndx, rot_indexx, rot_indx, rot_indexy, rot_indy, rot_indexz, rot_indz, frameTotal)
        log.trace("limb: %d RX %d RZ %d RY %d anim: %d frame: %d frameTotal: %d", bIndx, int(RX), int(RZ), int(RY), currentanim+1, frameCurrent+1, frameTotal)
        if (bIndx > -1):
            bone = armature.data.bones["limb_%02i" % (bIndx)]
            bone.select = True
            bpy.ops.transform.rotate(value = RXX, axis=(0, 0, 0), constraint_axis=(True, False, False))
            bpy.ops.transform.rotate(value = RZZ, axis=(0, 0, 0), constraint_axis=(False, False, True))
            bpy.ops.transform.rotate(value = RYY, axis=(0, 0, 0), constraint_axis=(False, True, False))
            bpy.ops.pose.select_all(action="DESELECT")

    bone = armature.pose.bones["limb_00"]
    bone.location += mathutils.Vector((newLocx,newLocz,-newLocy))
    bone.keyframe_insert(data_path='location')

    ### Could have done some math here but... just reverse previus frame, so it just repose.
    bpy.context.scene.tool_settings.use_keyframe_insert_auto = False

    bone = armature.pose.bones["limb_00"]
    bone.location -= mathutils.Vector((newLocx,newLocz,-newLocy))


def buildAnimations(self, hierarchyMostBones, newframe):
    log = getLogger('F3DZEX.buildAnimations')
    rot_indx = 0
    rot_indy = 0
    rot_indz = 0
    Trot_indx = 0
    Trot_indy = 0
    Trot_indz = 0
    segment = self.segment
    RX, RY, RZ = 0,0,0
    n_anims = self.animTotal
    if (AnimtoPlay > 0 and AnimtoPlay <= n_anims):
        currentanim = AnimtoPlay - 1
    else:
        currentanim = 0

    AnimationOffset = self.offsetAnims[currentanim]
    #seg, offset = splitOffset(hierarchy.offset) # not used, MUST be not relevant because we use hierarchyMostBones (its armature) as placeholder
    BoneCountMax = hierarchyMostBones.limbCount
    armature = hierarchyMostBones.armature
    frameCurrent = newframe

    if not validOffset(segment, AnimationOffset):
        log.warning('Skipping invalid animation offset 0x%X', AnimationOffset)
        return

    AniSeg = AnimationOffset >> 24
    AnimationOffset &= 0xFFFFFF

    frameTotal = unpack_from(">h", segment[AniSeg], (AnimationOffset))[0]
    rot_vals_addr = unpack_from(">L", segment[AniSeg], (AnimationOffset + 4))[0]
    RotIndexoffset = unpack_from(">L", segment[AniSeg], (AnimationOffset + 8))[0]
    Limit = unpack_from(">H", segment[AniSeg], (AnimationOffset + 12))[0] # todo no idea what this is

    rot_vals_addr  &= 0xFFFFFF
    RotIndexoffset &= 0xFFFFFF

    rot_vals_max_length = int ((RotIndexoffset - rot_vals_addr) / 2)
    if rot_vals_max_length < 0:
        log.info('rotation indices (animation data) is located before indexed rotation values, this is weird but fine')
        rot_vals_max_length = (len(segment[AniSeg]) - rot_vals_addr) // 2
    rot_vals_cache = []
    def rot_vals(index, errorDefault=0):
        if index < 0 or (rot_vals_max_length and index >= rot_vals_max_length):
            log.trace('index in rotations table %d is out of bounds (rotations table is <= %d long)', index, rot_vals_max_length)
            return errorDefault
        if index >= len(rot_vals_cache):
            rot_vals_cache.extend(unpack_from(">h", segment[AniSeg], (rot_vals_addr) + (j * 2))[0] for j in range(len(rot_vals_cache),index+1))
            log.trace('Computed rot_vals_cache up to %d %r', index, rot_vals_cache)
        return rot_vals_cache[index]

    bpy.context.scene.tool_settings.use_keyframe_insert_auto = True
    bpy.context.scene.frame_end = frameTotal
    bpy.context.scene.frame_current = frameCurrent + 1

    log.log(
        logging.INFO if (frameCurrent + 1) % min(20, max(min(10, frameTotal), frameTotal // 3)) == 0 else logging.DEBUG,
        "anim: %d/%d frame: %d/%d", currentanim+1, self.animTotal, frameCurrent+1, frameTotal)

    ## Translations
    Trot_indx = unpack_from(">h", segment[AniSeg], RotIndexoffset)[0]
    Trot_indy = unpack_from(">h", segment[AniSeg], RotIndexoffset + 2)[0]
    Trot_indz = unpack_from(">h", segment[AniSeg], RotIndexoffset + 4)[0]

    if (Trot_indx >= Limit):
        Trot_indx += frameCurrent
    if (Trot_indz >= Limit):
        Trot_indz += frameCurrent
    if (Trot_indy >= Limit):
        Trot_indy += frameCurrent

    TRX = rot_vals(Trot_indx)
    TRZ = rot_vals(Trot_indy)
    TRY = rot_vals(Trot_indz)

    global scaleFactor
    newLocx =  TRX * scaleFactor
    newLocz =  TRZ * scaleFactor
    newLocy = -TRY * scaleFactor
    log.trace("X %d Y %d Z %d", int(TRX), int(TRY), int(TRZ))

    log.trace("       %d Frames %d still values %f tracks",frameTotal, Limit, ((rot_vals_max_length - Limit) / frameTotal)) # what is this debug message?
    for i in range(BoneCountMax):
        bIndx = ((BoneCountMax-1) - i) # Had to reverse here, cuz didn't find a way to rotate bones on LOCAL space, start rotating from last to first bone on hierarchy GLOBAL.

        if RotIndexoffset + (bIndx * 6) + 10 + 2 > len(segment[AniSeg]):
            log.trace('Ignoring bone %d in animation %d, rotation table does not have that many entries', bIndx, AnimtoPlay)
            continue

        rot_indexx = unpack_from(">h", segment[AniSeg], RotIndexoffset + (bIndx * 6) + 6)[0]
        rot_indexy = unpack_from(">h", segment[AniSeg], RotIndexoffset + (bIndx * 6) + 8)[0]
        rot_indexz = unpack_from(">h", segment[AniSeg], RotIndexoffset + (bIndx * 6) + 10)[0]

        rot_indx = rot_indexx
        rot_indy = rot_indexy
        rot_indz = rot_indexz

        if (rot_indx >= Limit):
            rot_indx += frameCurrent
        if (rot_indy >= Limit):
            rot_indy += frameCurrent
        if (rot_indz >= Limit):
            rot_indz += frameCurrent

        RX = rot_vals(rot_indx, False)
        RY = rot_vals(rot_indz, False)
        RZ = rot_vals(rot_indy, False)

        if RX is False or RY is False or RZ is False:
            log.trace('Ignoring bone %d in animation %d, rotation table did not have the entry', bIndx, AnimtoPlay)
            continue

        RX /= 182.04444444444444444444 # = 0x10000 / 360
        RY /= -182.04444444444444444444
        RZ /= 182.04444444444444444444

        RXX = radians(RX)
        RYY = radians(RY)
        RZZ = radians(RZ)

        log.trace("limb: %d XIdx: %d %d YIdx: %d %d ZIdx: %d %d frameTotal: %d", bIndx, rot_indexx, rot_indx, rot_indexy, rot_indy, rot_indexz, rot_indz, frameTotal)
        log.trace("limb: %d RX %d RZ %d RY %d anim: %d frame: %d frameTotal: %d", bIndx, int(RX), int(RZ), int(RY), currentanim+1, frameCurrent+1, frameTotal)
        if (bIndx > -1):
            bone = armature.data.bones["limb_%02i" % (bIndx)]
            bone.select = True
            bpy.ops.transform.rotate(value = RXX, axis=(0, 0, 0), constraint_axis=(True, False, False))
            bpy.ops.transform.rotate(value = RZZ, axis=(0, 0, 0), constraint_axis=(False, False, True))
            bpy.ops.transform.rotate(value = RYY, axis=(0, 0, 0), constraint_axis=(False, True, False))
            bpy.ops.pose.select_all(action="DESELECT")

    bone = armature.pose.bones["limb_00"]
    bone.location += mathutils.Vector((newLocx,newLocz,-newLocy))
    bone.keyframe_insert(data_path='location')

    ### Could have done some math here but... just reverse previus frame, so it just repose.
    bpy.context.scene.tool_settings.use_keyframe_insert_auto = False

    bone = armature.pose.bones["limb_00"]
    bone.location -= mathutils.Vector((newLocx,newLocz,-newLocy))

    for i in range(BoneCountMax):
        bIndx = i

        if RotIndexoffset + (bIndx * 6) + 10 + 2 > len(segment[AniSeg]):
            log.trace('Ignoring bone %d in animation %d, rotation table does not have that many entries', bIndx, AnimtoPlay)
            continue

        rot_indexx = unpack_from(">h", segment[AniSeg], RotIndexoffset + (bIndx * 6) + 6)[0]
        rot_indexy = unpack_from(">h", segment[AniSeg], RotIndexoffset + (bIndx * 6) + 8)[0]
        rot_indexz = unpack_from(">h", segment[AniSeg], RotIndexoffset + (bIndx * 6) + 10)[0]

        rot_indx = rot_indexx
        rot_indy = rot_indexy
        rot_indz = rot_indexz

        if (rot_indx > Limit):
            rot_indx += frameCurrent
        if (rot_indy > Limit):
            rot_indy += frameCurrent
        if (rot_indz > Limit):
            rot_indz += frameCurrent

        RX = rot_vals(rot_indx, False)
        RY = rot_vals(rot_indz, False)
        RZ = rot_vals(rot_indy, False)

        if RX is False or RY is False or RZ is False:
            log.trace('Ignoring bone %d in animation %d, rotation table did not have the entry', bIndx, AnimtoPlay)
            continue

        RX /= -182.04444444444444444444
        RY /= 182.04444444444444444444
        RZ /= -182.04444444444444444444

        RXX = radians(RX)
        RYY = radians(RY)
        RZZ = radians(RZ)

        log.trace("limb: %d XIdx: %d %d YIdx: %d %d ZIdx: %d %d frameTotal: %d", i, rot_indexx, rot_indx, rot_indexy, rot_indy, rot_indexz, rot_indz, frameTotal)
        log.trace("limb: %d RX %d RZ %d RY %d anim: %d frame: %d frameTotal: %d", bIndx, int(RX), int(RZ), int(RY), currentanim+1, frameCurrent+1, frameTotal)
        if (bIndx > -1):
            bone = armature.data.bones["limb_%02i" % (bIndx)]
            bone.select = True
            bpy.ops.transform.rotate(value = RYY, axis=(0, 0, 0), constraint_axis=(False, True, False))
            bpy.ops.transform.rotate(value = RZZ, axis=(0, 0, 0), constraint_axis=(False, False, True))
            bpy.ops.transform.rotate(value = RXX, axis=(0, 0, 0), constraint_axis=(True, False, False))
            bpy.ops.pose.select_all(action="DESELECT")

    if (frameCurrent < (frameTotal - 1)):## Next Frame
        frameCurrent += 1
        self.buildAnimations(hierarchyMostBones, frameCurrent)
    else:
        bpy.context.scene.frame_current = 1


def locateLinkAnimations():
    data = self.segment[0x04]
    self.animation = []
    self.offsetAnims = []
    self.animFrames = []
    self.animTotal = -1
    if (len( self.segment[0x04] ) > 0):
        if (MajorasAnims):
            for i in range(0xD000, 0xE4F8, 8):
                self.animTotal += 1
                self.animation.append(self.animTotal)
                self.animFrames.append(self.animTotal)
                self.offsetAnims.append(self.animTotal)
                self.offsetAnims[self.animTotal]     = unpack_from(">L", data, i + 4)[0]
                self.animFrames[self.animTotal] = unpack_from(">h", data, i)[0]
                log.debug('- Animation #%d offset: %07X frames: %d', self.animTotal+1, self.offsetAnims[self.animTotal], self.animFrames[self.animTotal])
        else:
            for i in range(0x2310, 0x34F8, 8):
                self.animTotal += 1
                self.animation.append(self.animTotal)
                self.animFrames.append(self.animTotal)
                self.offsetAnims.append(self.animTotal)
                self.offsetAnims[self.animTotal]     = unpack_from(">L", data, i + 4)[0]
                self.animFrames[self.animTotal] = unpack_from(">h", data, i)[0]
                log.debug('- Animation #%d offset: %07X frames: %d', self.animTotal+1, self.offsetAnims[self.animTotal], self.animFrames[self.animTotal])
    log.info("         Link has come to town!!!!")
    if ( (len( self.segment[0x07] ) > 0) and (self.animTotal > 0)):
        self.buildLinkAnimations(self.hierarchy[0], 0)


def buildLinkAnimations(self, hierarchy, newframe):
    global AnimtoPlay
    global Animscount
    log = getLogger('F3DZEX.buildLinkAnimations')
    # todo buildLinkAnimations hasn't been rewritten/improved like buildAnimations has
    log.warning('The code to build link animations has not been improved/tested for a while, not sure what features it lacks compared to regular animations, pretty sure it will not import all animations')
    segment = []
    rot_indx = 0
    rot_indy = 0
    rot_indz = 0
    data = self.segment[0x06]
    segment = self.segment
    n_anims = self.animTotal
    seg, offset = splitOffset(hierarchy.offset)
    BoneCount  = hierarchy.limbCount
    RX, RY, RZ = 0,0,0
    frameCurrent = newframe

    if (AnimtoPlay > 0 and AnimtoPlay <= n_anims):
      currentanim = AnimtoPlay - 1
    else:
      currentanim = 0

    log.info("currentanim: %d frameCurrent: %d", currentanim+1, frameCurrent+1)
    AnimationOffset = self.offsetAnims[currentanim]
    TAnimationOffset = self.offsetAnims[currentanim]
    AniSeg = AnimationOffset >> 24
    AnimationOffset &= 0xFFFFFF
    rot_offset = AnimationOffset
    rot_offset += (frameCurrent * (BoneCount * 6 + 8))
    frameTotal = self.animFrames[currentanim]
    rot_offset += BoneCount * 6

    Trot_offset = TAnimationOffset & 0xFFFFFF
    Trot_offset += (frameCurrent * (BoneCount * 6 + 8))
    TRX = unpack_from(">h", segment[AniSeg], Trot_offset)[0]
    Trot_offset += 2
    TRZ = unpack_from(">h", segment[AniSeg], Trot_offset)[0]
    Trot_offset += 2
    TRY = -unpack_from(">h", segment[AniSeg], Trot_offset)[0]
    Trot_offset += 2
    BoneListListOffset = unpack_from(">L", segment[seg], offset)[0]
    BoneListListOffset &= 0xFFFFFF

    BoneOffset = unpack_from(">L", segment[seg], BoneListListOffset + (0 << 2))[0]
    S_Seg = (BoneOffset >> 24) & 0xFF
    BoneOffset &= 0xFFFFFF
    TRX += unpack_from(">h", segment[S_Seg], BoneOffset)[0]
    TRZ += unpack_from(">h", segment[S_Seg], BoneOffset + 2)[0]
    TRY += -unpack_from(">h", segment[S_Seg], BoneOffset + 4)[0]
    newLocx = TRX / 79
    newLocz = -25.5
    newLocz += TRZ / 79
    newLocy = TRY / 79

    bpy.context.scene.tool_settings.use_keyframe_insert_auto = True

    for i in range(BoneCount):
        bIndx = ((BoneCount-1) - i) # Had to reverse here, cuz didn't find a way to rotate bones on LOCAL space, start rotating from last to first bone on hierarchy GLOBAL.
        RX = unpack_from(">h", segment[AniSeg], rot_offset)[0]
        rot_offset -= 2
        RY = unpack_from(">h", segment[AniSeg], rot_offset + 4)[0]
        rot_offset -= 2
        RZ = unpack_from(">h", segment[AniSeg], rot_offset + 8)[0]
        rot_offset -= 2

        RX /= (182.04444444444444444444)
        RY /= (182.04444444444444444444)
        RZ /= (182.04444444444444444444)

        RXX = (RX)
        RYY = (-RZ)
        RZZ = (RY)

        log.trace('limb: %d RX %d RZ %d RY %d anim: %d frame: %d', bIndx, int(RXX), int(RZZ), int(RYY), currentanim+1, frameCurrent+1)
        if (i > -1):
            bone = hierarchy.armature.bones["limb_%02i" % (bIndx)]
            bone.select = True
            bpy.ops.transform.rotate(value = radians(RXX), axis=(0, 0, 0), constraint_axis=(True, False, False))
            bpy.ops.transform.rotate(value = radians(RZZ), axis=(0, 0, 0), constraint_axis=(False, False, True))
            bpy.ops.transform.rotate(value = radians(RYY), axis=(0, 0, 0), constraint_axis=(False, True, False))
            bpy.ops.pose.select_all(action="DESELECT")

    hierarchy.armature.bones["limb_00"].select = True ## Translations
    bpy.ops.transform.translate(value =(newLocx, 0, 0), constraint_axis=(True, False, False))
    bpy.ops.transform.translate(value = (0, 0, newLocz), constraint_axis=(False, False, True))
    bpy.ops.transform.translate(value = (0, newLocy, 0), constraint_axis=(False, True, False))
    bpy.ops.pose.select_all(action="DESELECT")

    if (frameCurrent < (frameTotal - 1)):## Next Frame ### Could have done some math here but... just reverse previus frame, so it just repose.
        bpy.context.scene.tool_settings.use_keyframe_insert_auto = False

        hierarchy.armature.bones["limb_00"].select = True ## Translations
        bpy.ops.transform.translate(value = (-newLocx, 0, 0), constraint_axis=(True, False, False))
        bpy.ops.transform.translate(value = (0, 0, -newLocz), constraint_axis=(False, False, True))
        bpy.ops.transform.translate(value = (0, -newLocy, 0), constraint_axis=(False, True, False))
        bpy.ops.pose.select_all(action="DESELECT")

        rot_offset = AnimationOffset
        rot_offset += (frameCurrent * (BoneCount * 6 + 8))
        rot_offset += 6
        for i in range(BoneCount):
            RX = unpack_from(">h", segment[AniSeg], rot_offset)[0]
            rot_offset += 2
            RY = unpack_from(">h", segment[AniSeg], rot_offset)[0]
            rot_offset += 2
            RZ = unpack_from(">h", segment[AniSeg], rot_offset)[0]
            rot_offset += 2

            RX /= (182.04444444444444444444)
            RY /= (182.04444444444444444444)
            RZ /= (182.04444444444444444444)

            RXX = (-RX)
            RYY = (RZ)
            RZZ = (-RY)

            log.trace("limb: %d RX %d RZ %d RY %d anim: %d frame: %d", i, int(RXX), int(RZZ), int(RYY), currentanim+1, frameCurrent+1)
            if (i > -1):
                bone = hierarchy.armature.bones["limb_%02i" % (i)]
                bone.select = True
                bpy.ops.transform.rotate(value = radians(RYY), axis=(0, 0, 0), constraint_axis=(False, True, False))
                bpy.ops.transform.rotate(value = radians(RZZ), axis=(0, 0, 0), constraint_axis=(False, False, True))
                bpy.ops.transform.rotate(value = radians(RXX), axis=(0, 0, 0), constraint_axis=(True, False, False))
                bpy.ops.pose.select_all(action="DESELECT")

        bpy.context.scene.frame_end += 1
        bpy.context.scene.frame_current += 1
        frameCurrent += 1
        self.buildLinkAnimations(hierarchy, frameCurrent)
    else:
        bpy.context.scene.tool_settings.use_keyframe_insert_auto = False
        bpy.context.scene.frame_current = 1


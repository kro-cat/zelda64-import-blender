from collections import namedtuple
from math import radians
from mmap import mmap
import numpy as np
from struct import unpack
from warnings import warn, BytesWarning

from segments import load_segment


#TODO classes to go in package __init__

def seg_offs(address: int):
        return ((address >> 24), (address & 0x00ffffff))

class Animation_Frame:
    def __init__(self, translation, rotation):
        self.translation = translation
        self.rotation = rotation

class Animation:
    def __init__(self):
        # translations of the root limb.
        # ( [x1, x2, x3, ...], [y1, y2, y3, ...], [z1, z2, z3, ...] )
        self.translations = ([0], [0], [0])

        # rotations of each limb
        # [ ( [l1_x1, l1_x2, ...], [l1_y1, l1_y2, ...], [l1_z1, l1_z2, ...] ),
        #   ( [l2_x1, l2_x2, ...], [l2_y1, l2_y2, ...], [l2_z1, l2_z2, ...] ),
        #   ( [ ...
        self.rotations = []

    @classmethod
    def load(cls, address, num_limbs):
        seg_num, seg_offs = seg_offs(address)

        # Animation Header

        hdr_format = ">HxxIIHxx"
        # ssss0000 rrrrrrrr iiiiiiii llll0000
        # s: # of frames
        # r: segment offset of rotation value list
        #     - rotation animation data, indexed via rotation index list
        # i: segment offset of rotation index list
        #     - start of rotation data in animation, limb indexed
        # l: index pivot
        #     - rotation value list indices less than this value
        #       remain constant.
        #     - rotation value list indices greater than this value
        #       are treated as sequential rotation frames.

        hdr_segment = load_segment(segment_num)
        hdr = unpack(hdr_format, hdr_segment[segment_offs
                                             : segment_offs + 16])

        num_frames = hdr[0]
        rval_addr = hdr[1]
        ridx_addr = hdr[2]
        index_pivot = hdr[3]

        val_segment = load_segment(rval_addr.segment)
        idx_segment = load_segment(ridx_addr.segment)

        def get_values(offs: int):
            frames = 1
            values = []
            idx_xyz = unpack(">3h", idx_segment[offs : offs + 6])
            for idx in idx_xyz:
                if (idx >= index_pivot):
                    frames = num_frames
                rval_offs = rval_addr.offset + idx
                values.append(unpack(
                    f">{frames}h",
                    val_segment[rval_offs : rval_offs + (2 * frames)]))
            return values

        anim = cls()

        # Translation

        ridx_offs = ridx_addr.offset
        anim.translations = get_values(ridx_offs) # ([x], [y], [z])
        # NOTE missing from rewrite:
        # * Scale translation by global scaleFactor
        # * Swap x and y axes
        # * Negate y axis (after swap)

        # Limb Rotations

        for limb in range(num_limbs):
            # offset by 6 (3 * 2 bytes) firstly; so we skip the tranlation
            ridx_offs += 6
            anim.rotations.append(get_values(ridx_offs)) # ([x], [y], [z])
            # NOTE missing from rewrite:
            # * Scale translation by rotationScale (360.0 / 65536.0)
            # * Swap x and y axes
            # * Negate y axis (after swap)


def find_animations(num_limbs: int, external=False: bool):
    # Animations are found in the following segments:
    # 0x06 (Animations)
    # 0x0f (External Animations)

    segment = external ? 0x0f : 0x06

    animations = []

    # sift through segment data one int (16 bytes) at a time and try to match
    # the animation header format
    # TODO figure out a better way to load this... "unknown" animation data
    for i in range(0, load_segment(segment).size() - 1, 4):
        address = (segment << 24) | i

        try:
            anim = Animation.load(address, num_limbs)
            log.info(f"[find_animations] Animation found at" \
                     f" 0x{int(address):08X} with {header.num_frames} frames")
            animations.append(anim)
        except:
            # no worries
            pass

    num_animations = len(animations)
    log.info(f"[find_animations] Found {num_animations:d} total" \
             f" Animations in segment 0x{segment_number:02X}")

    return animations




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


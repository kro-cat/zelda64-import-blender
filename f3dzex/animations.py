import logging
from mmap import mmap
from struct import unpack
from warnings import warn

from .segments import load_segment, SegmentNotFoundError
from .addressing import segment_offset


logger = logging.getLogger(__name__)

class InvalidAnimationException(Exception):
    pass

class Animation_Frame:
    def __init__(self, translation, rotation):
        self.translation = translation
        self.rotation = rotation

class Animation:
    def __init__(self):
        # translations of the root limb.
        # [
        #   (x,y,z), # frame 0
        #   (x,y,z), # frame 1
        #   ...
        # ]
        self.translations = []

        # rotations of each limb
        # [
        #   [ (x,y,z), (x,y,z), ... ], # limb 0
        #   [ (x,y,z), (x,y,z), ... ], # limb 1
        #   ...
        # ]
        self.rotations = []

    @classmethod
    def load(cls, hdr_segment: mmap, offset: int, num_limbs: int):
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

        # try:
        #     hdr_segment = load_segment(segment)
        # except SegmentNotFoundError:
        #     raise InvalidAnimationException("[Animation::load]" \
        #             f" bad segment 0x{seg_num:02X}")

        seg_offs_end = offset + 16
        if (seg_offs_end > hdr_segment.size()):
            raise InvalidAnimationException("[Animation::load]" \
                    f" header offset 0x{seg_offs_end:06X} is out of bounds" \
                    f" for segment 0x{segment:02X}")
        hdr = unpack(hdr_format, hdr_segment[offset:seg_offs_end])

        anim = cls()

        anim.num_frames = hdr[0]
        rval_seg_num, rval_seg_offs = segment_offset(hdr[1])
        ridx_seg_num, ridx_seg_offs = segment_offset(hdr[2])
        index_pivot = hdr[3]

        if ((rval_seg_num == 0) or (rval_seg_num > 16)):
            raise InvalidAnimationException("[Animation::load]" \
                    f" bad segment 0x{rval_seg_num:02X} in value list address")

        if ((ridx_seg_num == 0) or (ridx_seg_num > 16)):
            raise InvalidAnimationException("[Animation::load]" \
                    f" bad segment 0x{ridx_seg_num:02X} in index list address")

        try:
            val_segment = load_segment(rval_seg_num)
        except SegmentNotFoundError as e:
            raise InvalidAnimationException(str(e))

        try:
            idx_segment = load_segment(ridx_seg_num)
        except SegmentNotFoundError as e:
            raise InvalidAnimationException(str(e))

        def get_index(offs):
            offs_end = offs + 6
            if (offs_end > idx_segment.size()):
                raise InvalidAnimationException("[Animation::load.get_index]" \
                        f" index offset 0x{offs_end:06X} is out of bounds" \
                        f" for segment 0x{ridx_seg_num:02X}")
            return unpack(">3H", idx_segment[offs:offs_end])

        def _get_values(offs, count=1):
            offs_end = offs + (2 * count)
            if (offs_end > val_segment.size()):
                raise InvalidAnimationException("[Animation::load.get_values]" \
                        f" values offset 0x{offs_end:06X} is out of" \
                        f" bounds for segment 0x{rval_seg_num:02X}")
            return unpack(f">{count}H", val_segment[offs:offs_end])

        def get_values(offs):
            values = []
            idx_xyz = get_index(offs)
            for idx in idx_xyz:
                if (idx >= index_pivot):
                    values.append(_get_values(rval_seg_offs + idx,
                                              anim.num_frames))
                else:
                    values.append(_get_values(rval_seg_offs + idx)
                                  * anim.num_frames)
            return list(zip(values[0], values[1], values[2]))

        # Translation

        anim.translations = get_values(ridx_seg_offs)
        # NOTE missing from rewrite:
        # * Scale translation by global scaleFactor
        # * Swap z and y axes
        # * Negate y axis (after swap)

        # Limb Rotations

        for limb in range(num_limbs):
            # offset by 6 (3 * 2 bytes) firstly; so we skip the tranlation
            ridx_seg_offs += 6
            anim.rotations.append(get_values(ridx_seg_offs))
            # NOTE missing from rewrite:
            # * Scale translation by rotationScale (360.0 / 65536.0) # 0x10000
            # * Swap z and y axes
            # * Negate y axis (after swap)

        return anim

def load_animations(num_limbs: int, external: bool = False):
    # Animations are found in the following segments:
    # 0x06 (Animations)
    # 0x0f (External Animations)

    segment = 0x0f if external else 0x06

    animations = []

    # sift through segment data one dword (4 bytes) at a time and try to match
    # the animation header format
    # TODO figure out a better way to load this... "unknown" animation data
    offset = 0
    data = load_segment(segment)
    seg_offs_end = data.size() - 1
    while ((offset + 16) < seg_offs_end):
        try:
            anim = Animation.load(data, offset, num_limbs)
            logger.info(f"[load_animations] Animation found at" \
                    f" 0x{segment:02X}{offset:06X} with" \
                    f" {anim.num_frames} frames")
            animations.append(anim)
            offset += 16
        except InvalidAnimationException as e:
            logger.debug(str(e))
            offset += 4
            pass

    num_animations = len(animations)
    logger.info(f"[load_animations] Found {num_animations:d} total" \
             f" Animations in segment 0x{segment:02X}")

    return animations

class Link_Animation:
    def __init__(self):
        # translations of the root limb.
        # [
        #   (x,y,z), # frame 0
        #   (x,y,z), # frame 1
        #   ...
        # ]
        self.translations = []

        # rotations of each limb
        # [
        #   [ (x,y,z), (x,y,z), ... ], # limb 0
        #   [ (x,y,z), (x,y,z), ... ], # limb 1
        #   ...
        # ]
        self.rotations = []

    @classmethod
    def load(cls, hdr_segment: mmap, offset: int, num_limbs: int = 21):
        # Animation Header

        hdr_format = ">HxxI"
        # ssss0000 aaaaaaaa
        # s: # of frames
        # a: segment address of animation

        seg_offs_end = offset + 8
        if (seg_offs_end > hdr_segment.size()):
            raise InvalidAnimationException("[Link_Animation::load]" \
                    f" header offset 0x{seg_offs_end:06X} is out of bounds" \
                    f" for segment 0x{segment:02X}")
        hdr = unpack(hdr_format, hdr_segment[offset:seg_offs_end])

        anim = cls()

        anim.num_frames = hdr[0]
        rval_seg_num, rval_seg_offs = segment_offset(hdr[1])

        if ((rval_seg_num == 0) or (rval_seg_num > 16)):
            raise InvalidAnimationException("[Animation::load]" \
                    f" bad segment 0x{rval_seg_num:02X} in value list address")

        try:
            val_segment = load_segment(rval_seg_num)
        except SegmentNotFoundError as e:
            raise InvalidAnimationException(str(e))

        def get_values(offs):
            frames = []
            for frame in range(anim.num_frames):
                offs_start = offs + (0x7e * frame)
                offs_end = offs_start + 6
                if (offs_end > val_segment.size()):
                    raise InvalidAnimationException(f"[Link_Animation::load.get_values]" \
                            f" values offset 0x{offs_end:06X} is out" \
                            f" of bounds for segment 0x{rval_seg_num:02X}")
                frames.append(unpack(">3H", val_segment[offs_start:offs_end]))
            return frames

        # Translation

        anim.translations = get_values(rval_seg_offs)
        # NOTE missing from rewrite:
        # * Swap z and y axes
        # * Negate y axis (after swap)
        # * Translate z axis by -25.5 (after swap)

        # Rotation
        for limb in range(num_limbs):
            # offset by 6 (3 * 2 bytes) firstly; so we skip the tranlation
            rval_offs += 6
            anim.rotations.append(get_values(rval_seg_offs))
            # NOTE missing from rewrite:
            # * Scale translation by rotationScale (360.0 / 65536.0) # 0x10000
            # * Swap x and y axes
            # * Negate y axis (after swap)

        return anim

def load_link_animations(num_limbs: int = 21, majoras_mask: bool = False):
    segment = 0x04

    animations = []

    offset_start = 0x2310
    offset_end = 0x34f8

    if (majoras_mask):
        offset_start = 0xd000
        offset_end = 0xe4f8

    # sift through segment data one qword (8 bytes) at a time and try to match
    # the animation header format
    # TODO figure out a better way to load this... "unknown" animation data
    offset = offset_start
    data = load_segment(segment)
    seg_offs_end = data.size() - 1
    while (((offset + 8) <= offset_end) and ((offset + 8) < seg_offs_end)):
        try:
            anim = Link_Animation.load(data, offset, num_limbs)
            logger.info(f"[load_link_animations] Link Animation found at" \
                    f" 0x{segment:02X}{offset:06X} with" \
                    f" {anim.num_frames} frames")
            animations.append(anim)
            offset += 8
        except InvalidAnimationException as e:
            logger.debug(str(e))
            offset += 8
            pass

    num_animations = len(animations)
    logger.debug(f"[load_link_animations] Found {num_animations:d} total" \
             f" Link Animations in segment 0x{segment:02X}")

    return animations


import logging

from .memory import segment_offset, load_segment, MemoryException


logger = logging.getLogger(__name__)


class InvalidAnimationException(Exception):
    pass

class Animation_Frame:
    def __init__(self, translation, rotation):
        self.translation = translation
        self.rotation = rotation

class Animation:
    translation: tuple
    rotations: list

    def __init__(self, translation: tuple, rotations: list):
        # translation of the root limb. Guaranteed to be static
        # (x,y,z)
        self.translation = translation

        # rotations of each limb
        # !!! This is a ragged array !!!
        # [ # frame 1, frame 2, ...
        #   [ (x,y,z), (x,y,z), ... ], # limb 0
        #   [ (x,y,z), (x,y,z), ... ], # limb 1
        #   ...
        # ]
        self.rotations = rotations


def load_animation(segment: int, offset: int, limb_count: int):
    # Animation Header

    try:
        hdr_segment = load_segment(segment)
        header = hdr_segment.read_fmt(">HxxIIHxx", offset)
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
    except* MemoryException as e:
        raise InvalidAnimationException(
            "[load_animation] failed to load header") from e

    frame_count = header[0]
    rval_seg_num, rval_seg_offs = segment_offset(header[1])
    ridx_seg_num, ridx_seg_offs = segment_offset(header[2])
    index_pivot = header[3]

    try:
        val_segment = load_segment(rval_seg_num)
        idx_segment = load_segment(ridx_seg_num)
    except* MemoryException as e:
        raise InvalidAnimationException(
            "[load_animation] failed to load segment") from e

    # Translation

    translation_indices = idx_segment.read_fmt(">3H", ridx_seg_offs)
    translation_values = [ val_segment.read_fmt(">H", rval_seg_offs + index)
                          for index in translation_indices ]
    try:
        translation = next(zip(translation_values[0],
                               translation_values[1],
                               translation_values[2]))
    except StopIteration as e:
        raise InvalidAnimationException(
            '[load_animation] no translation I guess??') from e
    # NOTE missing from rewrite:
    # * Scale translation by global scaleFactor
    # * Swap z and y axes
    # * Negate y axis (after swap)

    # Rotations

    ridx_seg_offs += 6 # translation doesn't count
    rotations = []
    for limb in range(limb_count): # indexed arrays
        indices = idx_segment.read_fmt(">3H", ridx_seg_offs + (6 * limb))
        # xxxx yyyy zzzz
        # x, y, z: an index in the values list (head of values array)

        values = []
        for index in indices:
            count = 1 if (index < index_pivot) else frame_count
            values += val_segment.read_fmt(f">{count}H", rval_seg_offs + index)

        # values = [ [x], [y], [z] ]
        # ... needs to be zipped
        rotations += list(zip(values[0], values[1], values[2]))

    # NOTE missing from rewrite:
    # * Scale rotation by rotationScale (360.0 / 65536.0) # 0x10000
    # * Swap z and y axes
    # * Negate y axis (after swap)

    return Animation(translation, rotations)


def load_link_animation(segment: int, offset: int, limb_count: int = 21):
    # Animation Header

    try:
        hdr_segment = load_segment(segment)
        header = hdr_segment.read_fmt(">HxxI", offset)
        # ssss0000 aaaaaaaa
        # s: # of frames
        # a: segment address of animation
    except* MemoryException as e:
        raise InvalidAnimationException(
            "[load_link_animation] failed to load header") from e

    frame_count = header[0]
    rval_seg_num, rval_seg_offs = segment_offset(header[1])

    try:
        val_segment = load_segment(rval_seg_num)
    except* MemoryException as e:
        raise InvalidAnimationException(
            "[load_link_animation] failed to load segment") from e

    # Translation

    translation_values = val_segment.read_fmt(">3H", rval_seg_offs)
    try:
        translation = next(zip(translation_values[0],
                               translation_values[1],
                               translation_values[2]))
    except StopIteration as e:
        raise InvalidAnimationException(
            '[load_link_animation] no translation I guess??') from e
    # NOTE missing from rewrite:
    # * Scale translation by global scaleFactor
    # * Swap z and y axes
    # * Negate y axis (after swap)

    # Rotations

    ridx_seg_offs += 6 # translation doesn't count

    rotations = []
    anim_length = 3 * frame_count
    matrix_width = 2 * anim_length # accounting for width of 'H' format
    for limb in range(limb_count): # indexed matrix
        values = val_segment.read_fmt(f">{anim_length}H",
                                      rval_seg_offs + (matrix_width * limb))

        # values = [ [x, y, z, x, y, z, x, ... ]
        # ... needs to be grouped by threes

        rotations += [ (values[n], values[n+1], values[n+2])
                     for n in range(0, len(values), 3) ]

    # NOTE missing from rewrite:
    # * Scale rotation by rotationScale (360.0 / 65536.0) # 0x10000
    # * Swap z and y axes
    # * Negate y axis (after swap)

    return Animation(translation, rotations)


def load_animations(limb_count: int, external: bool = False):
    # Animations are found in the following segments:
    # 0x06 (Animations)
    # 0x0f (External Animations)

    segment = 0x0f if external else 0x06

    animations = []

    # sift through segment data one dword (4 bytes) at a time and try to match
    # the animation header format
    # TODO figure out a better way to load this... "unknown" animation data
    offset = 0
    seg_offs_end = load_segment(segment).size() - 1
    while ((offset + 16) < seg_offs_end):
        try:
            animations.append(load_animation(segment, offset, limb_count))
            logger.info(f"[load_animations] Animation found at" \
                    f" 0x{segment:02X}{offset:06X}")
            offset += 16
        except InvalidAnimationException as e:
            logger.debug(e.value)
            offset += 4

    num_animations = len(animations)
    logger.info(f"[load_animations] Found {num_animations:d} total" \
             f" Animations in segment 0x{segment:02X}")

    return animations


def load_link_animations(limb_count: int = 21, majoras_mask: bool = False):
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
    seg_offs_end = load_segment(segment).size() - 1
    while (((offset + 8) <= offset_end) and ((offset + 8) < seg_offs_end)):
        try:
            animations.append(load_link_animation(segment, offset, limb_count))
            logger.info(f"[load_link_animations] Link Animation found at" \
                    f" 0x{segment:02X}{offset:06X}")
            offset += 8
        except InvalidAnimationException as e:
            logger.debug(e.value)
            offset += 8

    num_animations = len(animations)
    logger.debug(f"[load_link_animations] Found {num_animations:d} total" \
             f" Link Animations in segment 0x{segment:02X}")

    return animations

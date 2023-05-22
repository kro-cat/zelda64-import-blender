import logging

from f3dzex2.processmodel import memory
from f3dzex2.processmodel.memory import MemoryException


logger = logging.getLogger(__name__)


class InvalidAnimationException(Exception):
    pass


# TODO: make this an iterator for Animation
class Animation_Frame:
    def __init__(self, translation, rotation):
        self.translation = translation
        self.rotation = rotation


class Animation:
    translation: tuple
    rotations: list
    max_frame_count: int

    def __init__(self, translation: tuple, rotations: list,
                 max_frame_count: int = -1):
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
        self.max_frame_count = max_frame_count


def load(address: int, limb_count: int) -> Animation:
    # Animation Header

    try:
        header = memory.read_fmt(address, ">HxxIIHxx")
        # ssss---- rrrrrrrr iiiiiiii llll----
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
    except MemoryException as e:
        raise InvalidAnimationException("failed to read header") from e

    frame_count = header[0]
    rval_addr = header[1]
    ridx_addr = header[2]
    index_pivot = header[3]

    # Translation
    try:
        translation_indices = memory.read_fmt(ridx_addr, ">3H")
        translation_values = [memory.read_fmt(rval_addr + index, ">H")
                              for index in translation_indices]
        translation = next(zip(translation_values[0],
                               translation_values[1],
                               translation_values[2]))
    except MemoryException as e:
        raise InvalidAnimationException("failed to read translation") from e
    except StopIteration as e:
        raise InvalidAnimationException("no translation I guess??") from e

    # NOTE missing from rewrite:
    # * Scale translation by global scaleFactor
    # * Swap z and y axes
    # * Negate y axis (after swap)

    # Rotations

    ridx_addr += 6  # translation doesn't count
    rotations = []
    for limb in range(limb_count):  # indexed arrays
        try:
            indices = memory.read_fmt(ridx_addr + (6 * limb), ">3H")
            # xxxx yyyy zzzz
            # x, y, z: an index in the values list (head of values array)

            values = []
            for index in indices:
                count = 1 if (index < index_pivot) else frame_count
                values.append(memory.read_fmt(rval_addr + index, f">{count}H"))

            # values = [ [x], [y], [z] ]
            # ... needs to be zipped
            rotations.append(list(zip(values[0], values[1], values[2])))
        except MemoryException as e:
            raise InvalidAnimationException(
                    "failed to read translation") from e

    # NOTE missing from rewrite:
    # * Scale rotation by rotationScale (360.0 / 65536.0) # 0x10000
    # * Swap z and y axes
    # * Negate y axis (after swap)

    return Animation(translation, rotations, frame_count)


def load_link(address: int, limb_count: int) -> Animation:
    # Animation Header
    try:
        header = memory.read_fmt(address, ">HxxI")
        # ssss0000 aaaaaaaa
        # s: # of frames
        # a: segment address of animation
    except MemoryException as e:
        raise InvalidAnimationException("failed to read header") from e

    frame_count = header[0]
    rval_addr = header[1]

    # Translation
    try:
        translation_values = memory.read_fmt(rval_addr, ">3H")
        translation = next(zip(translation_values[0],
                               translation_values[1],
                               translation_values[2]))
    except MemoryException as e:
        raise InvalidAnimationException("failed to read segment") from e
    except StopIteration as e:
        raise InvalidAnimationException("no translation I guess??") from e

    # NOTE missing from rewrite:
    # * Scale translation by global scaleFactor
    # * Swap z and y axes
    # * Negate y axis (after swap)

    # Rotations

    rval_addr += 6  # translation doesn't count

    rotations = []
    anim_length = 3 * frame_count
    matrix_width = 2 * anim_length  # accounting for width of 'H' format
    for limb in range(limb_count):  # indexed matrix
        values = memory.read_fmt(rval_addr + (matrix_width * limb),
                                 f">{anim_length}H")

        # values = [ [x, y, z, x, y, z, x, ... ]
        # ... needs to be grouped by threes

        rotations += [(values[n], values[n+1], values[n+2])
                      for n in range(0, len(values), 3)]

    # NOTE missing from rewrite:
    # * Scale rotation by rotationScale (360.0 / 65536.0) # 0x10000
    # * Swap z and y axes
    # * Negate y axis (after swap)

    return Animation(translation, rotations, frame_count)

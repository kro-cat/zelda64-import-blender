import logging

from .memory import Memory, MemoryException


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


class AnimationLoader:
    memory: Memory

    def __init__(self, memory: Memory):
        self.memory = memory

    def load_animation(self, limb_count: int, address: int) -> Animation:
        # Animation Header

        try:
            header = self.memory.read_fmt(">HxxIIHxx", address)
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
        except MemoryException as e:
            raise InvalidAnimationException(
                "[load_animation] failed to read header") from e

        frame_count = header[0]
        rval_addr = header[1]
        ridx_addr = header[2]
        index_pivot = header[3]

        # Translation
        try:
            translation_indices = self.memory.read_fmt(">3H", ridx_addr)
            translation_values = [self.memory.read_fmt(">H", rval_addr + index)
                                  for index in translation_indices]
            translation = next(zip(translation_values[0],
                                   translation_values[1],
                                   translation_values[2]))
        except MemoryException as e:
            raise InvalidAnimationException(
                "[load_animation] failed to read translation") from e
        except StopIteration as e:
            raise InvalidAnimationException(
                '[load_animation] no translation I guess??') from e
        # NOTE missing from rewrite:
        # * Scale translation by global scaleFactor
        # * Swap z and y axes
        # * Negate y axis (after swap)

        # Rotations

        ridx_addr += 6  # translation doesn't count
        rotations = []
        for limb in range(limb_count):  # indexed arrays
            try:
                indices = self.memory.read_fmt(">3H", ridx_addr + (6 * limb))
                # xxxx yyyy zzzz
                # x, y, z: an index in the values list (head of values array)

                values = []
                for index in indices:
                    count = 1 if (index < index_pivot) else frame_count
                    values.append(self.memory.read_fmt(f">{count}H",
                                                       rval_addr + index))

                # values = [ [x], [y], [z] ]
                # ... needs to be zipped
                rotations.append(list(zip(values[0], values[1], values[2])))
            except MemoryException as e:
                raise InvalidAnimationException(
                    "[load_animation] failed to read translation") from e

        # NOTE missing from rewrite:
        # * Scale rotation by rotationScale (360.0 / 65536.0) # 0x10000
        # * Swap z and y axes
        # * Negate y axis (after swap)

        return Animation(translation, rotations, frame_count)

    def load_link_animation(self, limb_count: int, address: int) -> Animation:
        # Animation Header
        try:
            header = self.memory.read_fmt(">HxxI", address)
            # ssss0000 aaaaaaaa
            # s: # of frames
            # a: segment address of animation
        except MemoryException as e:
            raise InvalidAnimationException(
                "[load_link_animation] failed to read header") from e

        frame_count = header[0]
        rval_addr = header[1]

        # Translation
        try:
            translation_values = self.memory.read_fmt(">3H", rval_addr)
            translation = next(zip(translation_values[0],
                                   translation_values[1],
                                   translation_values[2]))
        except MemoryException as e:
            raise InvalidAnimationException(
                "[load_link_animation] failed to read segment") from e
        except StopIteration as e:
            raise InvalidAnimationException(
                '[load_link_animation] no translation I guess??') from e
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
            values = self.memory.read_fmt(f">{anim_length}H",
                                          rval_addr + (matrix_width * limb))

            # values = [ [x, y, z, x, y, z, x, ... ]
            # ... needs to be grouped by threes

            rotations += [(values[n], values[n+1], values[n+2])
                          for n in range(0, len(values), 3)]

        # NOTE missing from rewrite:
        # * Scale rotation by rotationScale (360.0 / 65536.0) # 0x10000
        # * Swap z and y axes
        # * Negate y axis (after swap)

        return Animation(translation, rotations, frame_count)

    def load_animations(self, limb_count: int, external: bool = False):
        # Animations are found in the following segments:
        # 0x06 (Animations)
        # 0x0f (External Animations)

        segment = 0x0f if external else 0x06
        address = self.memory.get_start_address(segment)
        end = self.memory.get_end_address(segment)

        animations = []

        # sift through segment data one dword (4 bytes) at a time and try to
        # match the animation header format
        # TODO figure out a better way to load this... "unknown" animation data
        while (address + 16 < end):
            try:
                animation = self.load_animation(limb_count, address)
                animations.append(animation)
                logger.info("[load_animations] Animation found at 0x"
                            f"{address:08X} with {animation.max_frame_count} "
                            "frames")
                address += 16
            except InvalidAnimationException as e:
                logger.debug(repr(e))
                address += 4

        num_animations = len(animations)
        logger.info(f"[load_animations] Found {num_animations:d} total"
                    f" Animations in segment {segment}")
        return animations

    def load_link_animations(self, limb_count: int = 21,
                             majoras_mask: bool = False):
        segment = 0x04

        animations = []

        offset_start = 0x2310
        offset_end = 0x34f8

        if (majoras_mask):
            offset_start = 0xd000
            offset_end = 0xe4f8

        search_end = (segment << 24) | offset_end
        segment_end = self.memory.get_end_address(segment)

        address = (segment << 24) | offset_start
        end = search_end if search_end <= segment_end else segment_end

        # sift through segment data one qword (8 bytes) at a time and try to
        # match the animation header format
        # TODO figure out a better way to load this... "unknown" animation data
        while (address < end):
            try:
                animation = self.load_link_animation(limb_count, address)
                animations.append(animation)
                logger.info("[load_link_animations] Link Animation found at 0x"
                            f"{address:08X} with {animation.max_frame_count} "
                            "frames")
                address += 8
            except InvalidAnimationException as e:
                logger.debug(e.value)
                address += 8

        num_animations = len(animations)
        logger.debug(f"[load_link_animations] Found {num_animations:d} total"
                     f" Link Animations in segment {segment}")

        return animations

import logging

from f3dzex.memory import MemoryException
import f3dzex.memory as memory


logger = logging.getLogger(__name__)


class InvalidLimbException(Exception):
    pass


class Limb:
    translation: tuple
    child_index: int
    sibling_index: int
    display_list_addr: int

    def __init__(self, translation: tuple, child_index: int,
                 sibling_index: int, display_list_addr: int):
        self.translation = translation
        self.child_index = child_index
        self.sibling_index = sibling_index
        self.display_list_addr = display_list_addr


def load(address: int) -> Limb:
    try:
        limb = memory.read_fmt(address, ">3H2BI")
        # xxxxyyyy zzzzaabb dddddddd
        # x: x translation relative to parent
        # y: y translation relative to parent
        # z: z translation relative to parent
        # a: child limb index in list
        # b: sibling limb index in list
        # d: display list address
    except MemoryException as e:
        raise InvalidLimbException("failed to read limb") from e

    return Limb((limb[0], limb[1], limb[2]), limb[3], limb[4], limb[5])

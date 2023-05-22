import logging

from f3dzex2.processmodel import memory
from f3dzex2.processmodel.memory import MemoryException
from . import limb


logger = logging.getLogger(__name__)


class InvalidHierarchyException(Exception):
    pass


class Hierarchy:
    limbs: list
    displaylist_count: int

    def __init__(self, limbs: list, displaylist_count: int):
        self.limbs = limbs
        self.displaylist_count = displaylist_count


def load(address: int) -> Hierarchy:
    # Hierarchy Header
    try:
        header = memory.read_fmt(address, ">IBxxxBxxx")
        # iiiiiiii pp------ xx------
        # i: segment offset of limb index list
        # p: number of parts
        # x: number of display lists
    except MemoryException as e:
        raise InvalidHierarchyException("failed to read header") from e

    lidx_addr = header[0]
    limb_count = header[1]
    displaylist_count = header[2]

    # Limbs
    limbs = []
    for index in range(limb_count):
        try:
            laddr = memory.read_fmt(lidx_addr + (4 * index), ">I")[0]
            limbs.append(limb.load(laddr))
        except MemoryException as e:
            raise InvalidHierarchyException("failed to read segment") from e
        except limb.InvalidLimbException as e:
            raise InvalidHierarchyException("failed to read limb") from e

    if len(limbs) == 0:
        raise InvalidHierarchyException("hierarchy contains no limbs")

    return Hierarchy(limbs, displaylist_count)

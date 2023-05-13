import logging

from .memory import Memory, MemoryException


logger = logging.getLogger(__name__)


class InvalidHierarchyException(Exception):
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


class Hierarchy:
    limbs: list
    displaylist_count: int

    def __init__(self, limbs: list, displaylist_count: int):
        self.limbs = limbs
        self.displaylist_count = displaylist_count


class HierarchyLoader:
    memory: Memory

    def __init__(self, memory: Memory):
        self.memory = memory

    def load_limb(self, address: int) -> Limb:
        # Limb
        try:
            limb = self.memory.read_fmt(">HHHBBI", address)
            # xxxxyyyy zzzzaabb dddddddd
            # x: x translation relative to parent
            # y: y translation relative to parent
            # z: z translation relative to parent
            # a: child limb index in list
            # b: sibling limb index in list
            # d: display list address
        except MemoryException as e:
            raise InvalidHierarchyException(
                "[load_limb] failed to read limb") from e

        return Limb((limb[0], limb[1], limb[2]), limb[3], limb[4], limb[5])

    def load_hierarchy(self, address: int) -> Hierarchy:
        # Hierarchy Header
        try:
            header = self.memory.read_fmt(">IBxxxBxxx", address)
            # iiiiiiii pp000000 xx000000
            # i: segment offset of limb index list
            # p: number of parts
            # x: number of display lists
        except MemoryException as e:
            raise InvalidHierarchyException(
                "[load_hierarchy] failed to read header") from e

        lidx_addr = header[0]
        limb_count = header[1]
        displaylist_count = header[2]

        # Limbs
        limbs = []
        for limb in range(limb_count):
            try:
                laddr = self.memory.read_fmt(">I", lidx_addr + (4 * limb))[0]
                limbs.append(self.load_limb(laddr))
            except MemoryException as e:
                raise InvalidHierarchyException(
                    "[load_hierarchy] failed to read segment") from e

        if len(limbs) == 0:
            raise InvalidHierarchyException(
                "[load_hierarchy] hierarchy contains no limbs")

        return Hierarchy(limbs, displaylist_count)

    def load_hierarchies(self):
        # Hierarchies are found in segment 0x06:

        segment = 0x06
        address = self.memory.get_start_address(segment)
        end = self.memory.get_end_address(segment)

        hierarchies = []

        # sift through segment data one dword (4 bytes) at a time and try to
        # match the animation header format
        # TODO figure out a better way to load this... "unknown" animation data
        while (address < end):
            try:
                hier = self.load_hierarchy(address)
                hierarchies.append(hier)
                logger.info(f"[load_hierarchies] Hierarchy found at"
                            f" 0x{address:08X} with {len(hier.limbs)} limbs")
                address += 12
            except InvalidHierarchyException as e:
                logger.debug(repr(e))
                address += 4

        logger.info(f"[load_hierarchies] Found {len(hierarchies)} total"
                    f" Hierarchies in segment {segment}")

        return hierarchies

import logging

from . import animations, hierarchies, meshes
from . import memory


logger = logging.getLogger(__name__)


def find_all_animations(limb_count: int, external: bool = False):
    # Animations are found in the following segments:
    # 0x06 (Animations)
    # 0x0f (External Animations)

    segment = 0x0f if external else 0x06
    address = segment << 24
    end = memory.get_end_address(segment)

    found_animations = []

    # sift through segment data one dword (4 bytes) at a time and try to
    # match the animation header format
    # TODO figure out a better way to load this... "unknown" animation data
    while (address + 16 < end):
        try:
            animation = animations.load(address, limb_count)
            found_animations.append(animation)
            logger.info(f"Animation found at 0x{address:08X} with "
                        f"{animation.max_frame_count} frames")
            address += 16
        except animations.InvalidAnimationException as e:
            logger.debug(repr(e))
            address += 4

    logger.info(f"Found {len(found_animations)} total Animations in segment "
                f"{segment}")

    return found_animations


def find_all_link_animations(limb_count: int = 21, majoras_mask: bool = False):
    segment = 0x04

    found_animations = []

    offset_start = 0x2310
    offset_end = 0x34f8

    if (majoras_mask):
        offset_start = 0xd000
        offset_end = 0xe4f8

    search_end = (segment << 24) | offset_end
    segment_end = memory.get_end_address(segment)

    address = (segment << 24) | offset_start
    end = search_end if search_end <= segment_end else segment_end

    # sift through segment data one qword (8 bytes) at a time and try to
    # match the animation header format
    # TODO figure out a better way to load this... "unknown" animation data
    while (address < end):
        try:
            animation = animations.load_link(address, limb_count)
            found_animations.append(animation)
            logger.info(f"Link Animation found at 0x{address:08X} with "
                        f"{animation.max_frame_count} frames")
            address += 8
        except animations.InvalidAnimationException as e:
            logger.debug(e.value)
            address += 8

    logger.debug(f"Found {len(found_animations)} total Link Animations in "
                 f"segment {segment}")

    return found_animations


def find_all_hierarchies():
    # Hierarchies are found in segment 0x06:

    segment = 0x06
    address = segment << 24
    end = memory.get_end_address(segment)

    found_hierarchies = []

    # sift through segment data one dword (4 bytes) at a time and try to
    # match the animation header format
    # TODO figure out a better way to load this... "unknown" animation data
    while (address < end):
        try:
            hier = hierarchies.load(address)
            found_hierarchies.append(hier)
            logger.info(f"Hierarchy found at 0x{address:08X} with "
                        f"{len(hier.limbs)} limbs")
            address += 12
        except hierarchies.InvalidHierarchyException as e:
            logger.debug(repr(e))
            address += 4

    logger.info(f"Found {len(found_hierarchies)} total Hierarchies in segment "
                f"{segment}")

    return found_hierarchies


def find_all_meshes():
    segment = 0x03

    address = segment << 24

    # https://wiki.cloudmodding.com/oot/Scenes_and_Rooms

    end = memory.memmem(address, b"\x14\x00\x00\x00\x00\x00\x00\x00")
    if (end < 0):
        logger.warn(f"Could not find end marker in segment {segment}. "
                    "Not attempting search.")
        return []
        # end = memory.get_end_address(segment)

    found_meshes = []

    # try to find meshes by looking for the S2DEX macro gsSPBgRectCopy (0x0A)
    # 0A000000 aaaaaaaa
    # a: uObjBg pointer
    address = memory.memmem(address, b"\x0A\x00\x00\x00") + 4
    while (address < end):
        # (-1) + 4 == 3
        if (address == 3):
            break

        try:
            mesh_header_address = memory.read_fmt(address, ">I")
            mesh = meshes.load(mesh_header_address)
            found_meshes.append(mesh)
            logger.info(f"Mesh found at 0x{mesh_header_address:08X} with "
                        f"{len(mesh.display_lists)} display lists")
        except meshes.InvalidMeshException as e:
            logger.debug(repr(e))

        address = memory.memmem(address, b"\x0A\x00\x00\x00") + 4

    logger.info(f"Found {len(found_meshes)} total Meshes in segment {segment}")

    return found_meshes

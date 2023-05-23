import logging
from typing import NamedTuple

from .. import memory
from ..memory import MemoryException
from . import backgrounds as bgs


logger = logging.getLogger(__name__)


class InvalidMeshException(Exception):
    pass


class Mesh:
    display_lists: list

    def __init__(self, display_lists: list):
        self.display_lists = display_lists


class BackgroundMesh(Mesh):
    backgrounds: list

    def __init__(self, display_lists: list, backgrounds: list = []):
        super.__init__(display_lists)
        self.backgrounds = backgrounds


class Position(NamedTuple):
    x: int
    y: int
    z: int


class CullingMesh(Mesh):
    position: Position
    culling_distance: int

    def __init__(self, display_lists: list, position: Position,
                 culling_distance: int):
        super.__init__(display_lists)
        self.position = position
        self.culling_distance = culling_distance


def load_mesh_type_0(address: int) -> Mesh:
    # Simple mesh format; renders all display lists specified.
    try:
        header = memory.read_fmt(address, ">2BH2I")
        # 00cc0000 ssssssss eeeeeeee
        # c: number of entries
        # s: start of display list entries
        # e: end of display list entries
    except MemoryException as e:
        raise InvalidMeshException("failed to read header") from e

    # fail if first byte or first halfword are not equal to zero
    if (header[0] | header[2]):
        raise InvalidMeshException("bad_header_format")

    count = header[1]
    displaylist_start = header[3]
    # displaylist_end = header[4]
    lists = displaylists.load_array(displaylist_start, count)

    return Mesh(lists)


def load_mesh_type_1(address: int) -> BackgroundMesh:
    # This format is used with certain pre-rendered areas, specifically to
    # render a static background image rather than the panoramas. Notably,
    # the JFIF image is rendered via the S2DEX microcode, rather than the
    # primary rendering microcode (F3DZEX2). The JFIF is drawn using
    # S2DEX's gsSPBgRectCopy (0x0A) macro.
    try:
        header = memory.read_fmt(address, ">2B2xI")
        # 01tt---- pppppppp
        # t: background type
        # p: pointer to entry record
    except MemoryException as e:
        raise InvalidMeshException("failed to read header") from e

    # fail if first byte is not 0x01
    if header[0] != 0x01:
        raise InvalidMeshException("bad header format")

    background_type = header[1]
    entry_record = header[2]

    address += 8
    match background_type:
        case 0x01:
            # single
            records = {0: bgs.load(address)}
            pass
        case 0x02:
            # multiple
            records = bgs.load_all(address)
            pass
        case _:
            raise InvalidMeshException(
                    f"bad background type {background_type}")

    lists = [displaylists.load(entry_record)]

    return BackgroundMesh(lists, records)


def load_mesh_type_2(address: int) -> CullingMesh:
    # Mesh that culls if the camera behind a set point by a certain
    # distance.
    pass


def load(address: int) -> Mesh:
    try:
        mesh_type = memory.read_fmt(address, ">B")[0]
    except MemoryException as e:
        raise InvalidMeshException("failed to read mesh type") from e
    match mesh_type:
        case 0x00:
            return load_mesh_type_0(address)
        case 0x01:
            return load_mesh_type_1(address)
        case 0x02:
            return load_mesh_type_2(address)

    raise InvalidMeshException(f"bad header type {mesh_type:02X}")

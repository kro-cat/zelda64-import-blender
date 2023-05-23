import logging

from .. import memory
from ..memory import MemoryException
from . import jfif


logger = logging.getLogger(__name__)


class InvalidBackgroundException(Exception):
    pass


class Background:
    image: bytes
    width: int
    height: int

    def __init__(self, image: bytes, width: int, height: int):
        self.image = image
        self.width = width
        self.height = height


def load(address: int) -> Background:
    try:
        data = memory.read_fmt(address, ">I8x2H2B2H")
        # iiiiiiii -------- -------- wwwwhhhh ffsspppp llll
        # i: address to JFIF image
        # w: background width (typically 320px)
        # h: background height (typically 240px)
        # f: image format (?)
        # s: image size (?)
        # p: image palette (?)
        # l: image flip (?)
    except MemoryException as e:
        raise InvalidBackgroundException("failed to read background") from e

    width = data[1]
    height = data[1]
    try:
        image = jfif.load(data[0])
    except jfif.InvalidJfifException as e:
        raise InvalidBackgroundException("failed to read JFIF") from e

    return Background(image, width, height)


def load_all(address: int):
    try:
        header = memory.read_fmt(address, ">B3xI")
    except MemoryException as e:
        raise InvalidBackgroundException("failed to read header") from e

    count = header[0]
    bg_addr = header[1]

    records = {}
    for index in range(count):
        offs = (0x1c + index)
        try:
            bg_hdr = memory.read_fmt(bg_addr + offs, ">HB")
        except MemoryException as e:
            raise InvalidBackgroundException(
                    "failed to read background data") from e

        unk_0x0082 = bg_hdr[0]
        bg_id = bg_hdr[1]

        if unk_0x0082 != 0x0082:
            raise InvalidBackgroundException("bad background record")

        records[bg_id] = load(bg_addr + 4 + offs)

    return records

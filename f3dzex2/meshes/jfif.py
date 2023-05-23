import logging

from .. import memory
from ..memory import MemoryException


logger = logging.getLogger(__name__)


class InvalidJfifException(Exception):
    pass


def load(address: int) -> bytes:
    # I'm loading the jfif this way in case we want to make it work with other
    # images.
    try:
        # verify image start marker 0xFFD8
        if (memory.read_fmt(address, ">H")[0] != 0xFFD8):
            raise InvalidJfifException("mark at start of data does not match")

        # verify existence of header start marker 0xFFE0
        header_start = memory.memmem(address, b"\xFF\xE0") + 2
        if (header_start == 1):
            raise InvalidJfifException(
                    "failed to find mark for start of header")

        # first word after start marker 0xFFE0
        header_length = memory.read_fmt(header_start, ">H")
        # llll
        # l: length of header (not counting start or end markers)

        # make sure header length is 16 (all OoT images have a 16-byte header)
        if (header_length != 16):
            raise InvalidJfifException(
                    f"header length is {header_length} (expected 16)")

        # verify end marker 0xFFDB
        end_mark = memory.read_fmt(header_start + header_length, ">H")[0]
        if (end_mark != 0xFFDB):
            raise InvalidJfifException("mark at end of header does not match")

        # verify JFIF identifier: "JFIF\0"
        jfif_ident = memory.read_fmt(header_start + 2, ">5B")
        if (jfif_ident != [0x4A, 0x46, 0x49, 0x46, 0x00]):
            raise InvalidJfifException("JFIF identifier does not match")

        header = memory.read_fmt(header_start + 7, ">3B2H2B")
        # rest of header
        # ... aa iiddxxxx yyyywwvv
        # a: major version (should be 1)
        # i: minor version (should be 1)
        # d: density units (should be zero)
        # x: horizontal pixel density (should be 1)
        # y: vertical pixel density (should be 1)
        # w: thumbnail width (should be zero)
        # h: thumbnail height (should be zero)
        if (header[0] != 1)\
                or (header[1] != 1)\
                or (header[2] != 0)\
                or (header[3] != 1)\
                or (header[4] != 1)\
                or (header[5] != 0)\
                or (header[6] != 0):
            # TODO: make this more helpful, I guess.
            raise InvalidJfifException("JFIF header in unknown state")
    except MemoryException as e:
        raise InvalidJfifException("failed to read JFIF header") from e

    # verify existence of data end marker 0xFFD9
    image_end = memory.memmem(header_start + 18, b"\xFF\xD9") + 2
    if image_end < address:
        raise InvalidJfifException("failed to find mark for end of data")

    # return entire JFIF data
    return memory.read(address, image_end - address)

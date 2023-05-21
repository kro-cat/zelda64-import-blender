import logging

from f3dzex.memory import MemoryException
import f3dzex.memory as memory


logger = logging.getLogger(__name__)


class InvalidJfifException(Exception):
    pass


def load(address: int) -> bytes:
    # I'm loading the jfif this way in case we want to make it work with other
    # images.
    try:
        preamble = memory.read_fmt(address, ">3H5B")
        # FFD8FFE0 llll4A46 494600 ...
        # l: length of header (should be 16)

        # verify this is actually JFIF
        if (preamble[0] != 0xFFD8)\
                or (preamble[1] != 0xFFE0)\
                or (preamble[3:7] != [0x4A, 0x46, 0x49, 0x46, 0x00]):
            raise InvalidJfifException("not a JFIF")

        # verify this is a header we know how to read
        if (preamble[2] != 16):
            raise InvalidJfifException("I can't read this JFIF header!")

        header = memory.read_fmt(address + 11, ">3B2H2B")
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

    end_address = memory.memmem(address + 24, b"\xFF\xD9") + 2

    if end_address < address:
        raise InvalidJfifException("failed to find JFIF end mark")

    return memory.read(address, end_address - address)

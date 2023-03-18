import errno
import logging
import os
from glob import iglob
from mmap import mmap
from struct import unpack, calcsize

from . import cwd


logger = logging.getLogger(__name__)

_segment_cache = {}

class MemoryException(Exception):
    pass

class SegmentNotFoundError(MemoryException):
    pass

class InvalidAddressException(MemoryException):
    pass


class MemorySegment:
    segment: int
    _mmap: mmap

    def __init__(self, segment: int, file_name: str = None):
        if ((segment == 0) or (segment > 16)):
            raise InvalidAddressException("[MemorySegment::__init__]" \
                    f" bad segment 0x{segment:02X}")

        if (file_name == None):
            logger.debug("[MemorySegment::__init__] no file name given," \
                    " attempting segment discovery")
            if (segment == 0x02): # Segment 0x02 is special
                file_name = "segment_02.zdata"
                if (not os.path.isfile("segment_02.zdata")):
                    try:
                        file_name = next(iglob("*.zscene"))
                    except StopIteration:
                        # file_name stays "segment_01.zdata"
                        #   - exception happens before assignment
                        pass
            else:
                file_name = f"segment_{segment:02X}.zdata"

        if (os.path.isfile(file_name)):
            fp = open(file_name, "r+b")
            _segment_cache[segment] = fp
            logger.debug("[MemorySegment::__init__] loaded segment" \
                         f" 0x{segment:02X} from {file_name}")
        else:
            raise SegmentNotFoundError(os.strerror(errno.ENOENT) + " "
                                       + os.path.join(os.getcwd(), file_name))

        self.segment = segment
        self._mmap = mmap(fp.fileno(), 0)

    def read_fmt(self, fmt: str, offset: int) -> bytes:
        offset_end = offset + calcsize(fmt)
        if (offset_end > this._mmap.size()):
            raise InvalidAddressException("[MemorySegment::read_fmt]" \
                    f" offset 0x{offset_end:06X} is out of bounds" \
                    f" for segment 0x{this.segment:02X}")
        return unpack(fmt, this._mmap[offset:offset_end])

    def size():
        return _mmap.size()


def load_segment(segment: int, file_name: str = None) -> MemorySegment:
    memseg = None
    try:
        memseg = _segment_cache[segment]
        logger.debug(f"[load_segment] using memory segment 0x{segment:02X}" \
                     " from cache")
    except KeyError:
        logger.debug(f"[load_segment] segment 0x{segment:02X} not found" \
                     " in cache")
        with cwd(): # switch to f3dzex.prefix
            memseg = MemorySegment(segment, file_name)

    return file


# memory segment/offset splitter helper function - makes occurrences of this
# algorithm way more readable
def segment_offset(address: int):
        return ((address >> 24), (address & 0x00ffffff))

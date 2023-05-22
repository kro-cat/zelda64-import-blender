import logging
from mmap import mmap
from struct import unpack, calcsize


logger = logging.getLogger(__name__)


class MemoryException(Exception):
    pass


class SegmentNotFoundException(MemoryException):
    pass


class InvalidAddressException(MemoryException):
    pass


class Segment:
    # TODO: implement multi-page segments maybe.
    _mmap: mmap

    def __init__(self, _mmap: mmap):
        self._mmap = _mmap

    def memmem(self, offset: int, pattern: bytes) -> int:
        pattern_list = list(pattern)
        pattern_length = len(pattern_list)
        for index in range(offset, len(self._mmap)):
            if self._mmap[index:index + pattern_length] == pattern_list:
                return index
        return -1

    def read(self, offset: int, size: int) -> bytes:
        if size > 0:
            offset_end = offset + size
            if (offset_end > self._mmap.size()):
                raise InvalidAddressException(
                        f"offset 0x{offset_end:06X} is out of bounds")
            return self._mmap[offset:offset_end]
        elif size < 0:
            raise InvalidAddressException("size must be positive")
        else:
            return b""

    def read_fmt(self, offset: int, fmt: str) -> bytes:
        return unpack(fmt, self.read(offset, calcsize(fmt)))

    def size(self) -> int:
        return self._mmap.size()


segment_cache = {}


def segment_offset(address: int):
    return ((address >> 24), (address & 0x00ffffff))


def set_segment(segment: int, segment_data: Segment):
    # if segment not in segment_cache:
    #     segment_cache[segment] = Segment()

    # segment_cache[segment].insert(offset, mmap(fp.fileno(), 0))
    segment_cache[segment] = segment_data


def get_segment(segment: int) -> Segment:
    if segment not in segment_cache:
        raise SegmentNotFoundException(
                f"segment {segment} has not been loaded")
    return segment_cache[segment]


def memmem(self, address: int, pattern: bytes) -> int:
    segment, offset = segment_offset(address)
    return (segment << 24) | get_segment(segment).memmem(offset, pattern)


def read(address: int, size: int) -> bytes:
    segment, offset = segment_offset(address)
    return get_segment(segment).read(offset, size)


def read_fmt(address: int, fmt: str) -> bytes:
    segment, offset = segment_offset(address)
    return get_segment(segment).read_fmt(offset, fmt)


def get_end_address(segment: int) -> int:
    return (segment << 24) | get_segment(segment).size()

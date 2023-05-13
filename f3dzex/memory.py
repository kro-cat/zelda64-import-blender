import logging
from mmap import mmap
from struct import unpack, calcsize
from . import cwd


logger = logging.getLogger(__name__)


class MemoryException(Exception):
    pass


class SegmentNotFoundException(MemoryException):
    pass


class InvalidAddressException(MemoryException):
    pass


class Segment:
    memory_map = {}

    def __init__(self):
        pass

    def insert(self, offset: int, _mmap: mmap):
        self.memory_map[offset] = _mmap

    def read_fmt(self, fmt: str, offset: int) -> bytes:
        selected_offset = 0
        for key in self.memory_map.keys():
            if key > selected_offset and key <= offset:
                selected_offset = key

        _mmap = self.memory_map[selected_offset]

        offset_end = offset + calcsize(fmt)
        if (offset_end > _mmap.size()):
            raise InvalidAddressException("[MemorySegment::read_fmt] offset 0x"
                                          f"{offset_end:06X} is out of bounds")
        return unpack(fmt, _mmap[offset:offset_end])

    def size(self) -> int:
        offset = max(self.memory_map.keys())
        return offset + self.memory_map[offset].size()

    def get_start_offset(self) -> int:
        return min(self.memory_map.keys())


class Memory:
    segment_cache = {}

    def load_memory_from_file(self, address: int, file_name: str):
        segment, offset = segment_offset(address)
        with cwd():
            fp = open(file_name, "r+b")
            logger.debug("[Memory::load_segment_from_file] loaded segment from"
                         f" {file_name}")

            if segment not in self.segment_cache:
                self.segment_cache[segment] = Segment()

            self.segment_cache[segment].insert(offset, mmap(fp.fileno(), 0))

    def read_fmt(self, fmt: str, address: int) -> bytes:
        segment, offset = segment_offset(address)
        return self.get_segment(segment).read_fmt(fmt, offset)

    def get_start_address(self, segment: int) -> int:
        return (segment << 24) | self.get_segment(segment).get_start_offset()

    def get_end_address(self, segment: int) -> int:
        return (segment << 24) | self.get_segment(segment).size()

    def get_segment(self, segment: int) -> Segment:
        if segment not in self.segment_cache:
            raise SegmentNotFoundException("[Memory::get_segment] segment "
                                           f"{segment} has not been loaded")
        return self.segment_cache[segment]


# memory segment/offset splitter helper function - makes occurrences of this
# algorithm way more readable
def segment_offset(address: int):
    return ((address >> 24), (address & 0x00ffffff))

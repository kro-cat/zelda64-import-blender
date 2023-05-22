import logging
import os
from contextlib import contextmanager
from mmap import mmap

from .processmodel import memory


logger = logging.getLogger(__name__)


prefix = os.getcwd()


_cwd = []


@contextmanager
def cwd(path: str = None):
    path = path or prefix
    _cwd.append(os.getcwd())
    os.chdir(path)
    logger.debug(f"[cwd] cwd switched to {path}")
    try:
        yield
    finally:
        path = _cwd.pop()
        os.chdir(path)
        logger.debug(f"[cwd] cwd switched to {path}")


def load_segment_from_file(segment: int, file_name: str):
    with cwd():
        fp = open(file_name, "r+b")
        _mmap = mmap(fp.fileno(), 0)

        logger.debug(f"loaded 0x{(segment << 24):08X} - "
                     f"0x{(segment << 24)+len(_mmap):08X} from {file_name}")

        memory.set_segment(segment, memory.Segment(_mmap))

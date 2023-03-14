import errno
import logging
import os
from glob import iglob
from mmap import mmap

from . import cwd


logger = logging.getLogger(__name__)

_segment_cache = {}

class SegmentNotFoundError(FileNotFoundError):
    pass

def load_segment(segment, file_name=None):
    file = None
    try:
        file = _segment_cache[segment]
        logger.debug(f"[load_segment] using segment 0x{segment:02X}" \
                f" from cache")
    except KeyError:
        logger.debug(f"[load_segment] segment 0x{segment:02X} not found" \
                f" in cache")
        with cwd(): # switch to f3dzex.prefix
            if (file_name == None):
                logger.debug(f"[load_segment] no file name given," \
                        f" attempting segment discovery")
                if (segment == 0x02):
                    file_name = "segment_02.zdata"
                    if (not os.path.isfile("segment_02.zdata")):
                        try:
                            file_name = next(iglob("*.zscene"))
                        except StopIteration:
                            pass
                else:
                    file_name = f"segment_{segment:02X}.zdata"

            if (os.path.isfile(file_name)):
                fp = open(file_name, "r+b")
                file = mmap(fp.fileno(), 0)
                _segment_cache[segment] = file
                logger.debug(f"[load_segment] loaded segment 0x{segment:02X}" \
                        f" from file {file_name}")
            else:
                raise SegmentNotFoundError(
                        errno.ENOENT, os.strerror(errno.ENOENT),
                        os.path.join(os.getcwd(), file_name))
    return file

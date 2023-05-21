import logging

from f3dzex.memory import MemoryException
import f3dzex.memory as memory


logger = logging.getLogger(__name__)


class InvalidDisplayListException(Exception):
    pass


class DisplayList:
    pass


def load(address: int) -> DisplayList:
    pass


def load_all(address: int, count: int):
    pass

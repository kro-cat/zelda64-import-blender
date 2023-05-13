import logging

import os

from contextlib import contextmanager


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

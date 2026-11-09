"""Measure resident memory and release unused import allocations when possible."""

import ctypes
import gc
import os
import sys
from pathlib import Path

from loguru import logger


def resident_bytes() -> int | None:
    try:
        pages = int(Path("/proc/self/statm").read_text().split()[1])
        return pages * os.sysconf("SC_PAGE_SIZE")
    except (OSError, ValueError, IndexError, AttributeError):
        return None


def log_memory(stage: str) -> None:
    rss = resident_bytes()
    if rss is not None:
        logger.info("Memory {}: RSS {:.1f} MiB", stage, rss / 1024**2)


def release_memory() -> None:
    log_memory("before import cleanup")
    gc.collect()
    if sys.platform == "linux":
        try:
            trim = ctypes.CDLL(None).malloc_trim
        except (OSError, AttributeError):
            # Non-glibc systems still benefit from garbage collection.
            pass
        else:
            trim.argtypes = [ctypes.c_size_t]
            trim.restype = ctypes.c_int
            trim(0)
    log_memory("after import cleanup")

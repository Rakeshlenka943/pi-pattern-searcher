"""Python wrapper around the Chudnovsky C extension."""
import ctypes
from typing import Iterator

from . import build


def generate(digits: int, chunk_size: int = 50_000) -> Iterator[str]:
    if digits <= 0:
        return
    lib = build.load()
    ptr = lib.compute_pi_c(digits)
    if not ptr:
        raise RuntimeError("compute_pi_c returned NULL")
    try:
        s = ctypes.string_at(ptr, digits).decode("ascii")
    finally:
        lib.free_pi_string(ptr)
    for i in range(0, len(s), chunk_size):
        yield s[i:i + chunk_size]

"""Pi digit generation — gmpy2 -> mpmath -> spigot backends."""
from __future__ import annotations
from typing import Iterator


def _detect_backend() -> str:
    try:
        from .c_ext import build as _cext_build
        if _cext_build.is_available():
            return "c_ext"
    except Exception:
        pass
    for name in ("gmpy2", "mpmath"):
        try:
            __import__(name)
            return name
        except ImportError:
            continue
    return "spigot"


def _compute_gmpy2(digits: int) -> str:
    import gmpy2
    bits = int(digits * 3.3219280948873626) + 64
    gmpy2.get_context().precision = bits
    s = format(gmpy2.const_pi(), f".{digits}f")
    ip, _, frac = s.partition(".")
    return (ip + frac)[:digits]


def _compute_mpmath(digits: int) -> str:
    from mpmath import mp
    mp.dps = digits + 20
    s = mp.nstr(mp.pi, digits + 10, strip_zeros=False)
    ip, _, frac = s.partition(".")
    return (ip + frac)[:digits]


def _spigot_digits() -> Iterator[int]:
    q, r, t, k, n, l = 1, 0, 1, 1, 3, 3
    while True:
        if 4 * q + r - t < n * t:
            yield n
            q, r, t, k, n, l = (
                10 * q, 10 * (r - n * t), t, k,
                (10 * (3 * q + r)) // t - 10 * n, l,
            )
        else:
            q, r, t, k, n, l = (
                q * k, (2 * q + r) * l, t * l, k + 1,
                (q * (7 * k + 2) + r * l) // (t * l), l + 2,
            )


def _spigot_chunks(digits: int, chunk_size: int) -> Iterator[str]:
    buf: list[str] = []
    seen = 0
    for d in _spigot_digits():
        buf.append(str(d))
        seen += 1
        if len(buf) >= chunk_size:
            yield "".join(buf); buf = []
        if seen >= digits:
            break
    if buf:
        yield "".join(buf)


def generate_pi(
    digits: int,
    backend: str = "auto",
    chunk_size: int = 50_000,
) -> Iterator[str]:
    if digits <= 0:
        return
    if backend == "auto":
        backend = _detect_backend()

    if backend == "c_ext":
        try:
            from .c_ext import backend as c_ext_backend
            yield from c_ext_backend.generate(digits, chunk_size)
            return
        except Exception:
            backend = _detect_backend()

    if backend == "spigot":
        yield from _spigot_chunks(digits, chunk_size)
        return

    if backend == "gmpy2":
        s = _compute_gmpy2(digits)
    elif backend == "mpmath":
        s = _compute_mpmath(digits)
    else:
        raise ValueError(f"unknown backend: {backend!r}")

    for i in range(0, len(s), chunk_size):
        yield s[i:i + chunk_size]

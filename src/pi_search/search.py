"""String-matching algorithms for streaming pi search."""
from __future__ import annotations
from typing import Iterator


def naive_search(text: str, pattern: str, start: int = 0) -> int:
    n, m = len(text), len(pattern)
    if m == 0:
        return start
    if m > n:
        return -1
    for i in range(start, n - m + 1):
        if text[i:i + m] == pattern:
            return i
    return -1


def build_kmp_table(pattern: str) -> list[int]:
    table = [0] * len(pattern)
    j = 0
    for i in range(1, len(pattern)):
        while j > 0 and pattern[i] != pattern[j]:
            j = table[j - 1]
        if pattern[i] == pattern[j]:
            j += 1
        table[i] = j
    return table


def kmp_search(text: str, pattern: str, start: int = 0) -> int:
    if not pattern:
        return start
    table = build_kmp_table(pattern)
    j = 0
    for i in range(start, len(text)):
        while j > 0 and text[i] != pattern[j]:
            j = table[j - 1]
        if text[i] == pattern[j]:
            j += 1
        if j == len(pattern):
            return i - len(pattern) + 1
    return -1


_BASE = 10
_MOD = (1 << 61) - 1


def _roll_hash(s: str, m: int) -> int:
    h = 0
    for ch in s[:m]:
        h = (h * _BASE + (ord(ch) - 48)) % _MOD
    return h


def rabin_karp_search(text: str, pattern: str, start: int = 0) -> int:
    m, n = len(pattern), len(text)
    if m == 0:
        return start
    if m > n:
        return -1
    ph = _roll_hash(pattern, m)
    th = _roll_hash(text[start:start + m], m)
    high = pow(_BASE, m - 1, _MOD)
    for i in range(start, n - m + 1):
        if th == ph and text[i:i + m] == pattern:
            return i
        if i + m < n:
            th = ((th - (ord(text[i]) - 48) * high) * _BASE
                  + (ord(text[i + m]) - 48)) % _MOD
    return -1


def search(text: str, pattern: str, algorithm: str = "auto", start: int = 0) -> int:
    if not pattern:
        return start
    if algorithm == "auto":
        if len(pattern) <= 4:
            algorithm = "naive"
        elif len(pattern) > 100:
            algorithm = "rabin-karp"
        else:
            algorithm = "kmp"
    if algorithm == "naive":
        return naive_search(text, pattern, start)
    if algorithm == "kmp":
        return kmp_search(text, pattern, start)
    if algorithm == "rabin-karp":
        return rabin_karp_search(text, pattern, start)
    raise ValueError(f"unknown algorithm: {algorithm!r}")


def search_stream(
    chunks: Iterator[str],
    pattern: str,
    algorithm: str = "auto",
    progress_cb=None,
    progress_every: int = 1_000_000,
) -> tuple[int, int]:
    """Stream-search a pattern. Optional progress_cb(consumed) fires periodically."""
    m = len(pattern)
    if m == 0:
        return 0, 0
    overlap = ""
    consumed = 0
    next_report = progress_every
    for chunk in chunks:
        combined = overlap + chunk
        idx = search(combined, pattern, algorithm)
        if idx >= 0:
            return consumed - len(overlap) + idx, consumed + len(chunk)
        overlap = combined[-(m - 1):] if m > 1 else ""
        consumed += len(chunk)
        if progress_cb is not None and consumed >= next_report:
            progress_cb(consumed)
            next_report = (consumed // progress_every + 1) * progress_every
    return -1, consumed

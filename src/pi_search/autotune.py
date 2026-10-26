"""Adaptive backend + parameter selection with caching."""
from __future__ import annotations
import hashlib, json, math, time
from dataclasses import dataclass, asdict, field
from pathlib import Path

from .hardware import HardwareProfile, detect
from .pi_generator import generate_pi

CONFIG_PATH = Path.home() / ".pi_search_config.json"

# Representative size for backend benchmarking. Large enough that the
# decimal-conversion cost (which differentiates gmpy2 vs mpmath at
# scale) dominates, small enough that first-run latency is ~1s.
BENCH_DIGITS = 500_000


@dataclass
class TuneConfig:
    backend: str
    chunk_size: int
    threads: int
    algorithm: str
    fingerprint: str = ""
    benchmarked: dict = field(default_factory=dict)
    bench_size: int = 0


def fingerprint(hw: HardwareProfile) -> str:
    blob = "|".join([
        hw.os, hw.arch, hw.cpu_model,
        str(hw.physical_cores), str(hw.ram_gb),
        hw.cuda_name or "-",
    ])
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def prior(hw: HardwareProfile) -> TuneConfig:
    """Math-derived initial guess, refined by benchmark below."""
    threads = max(1, hw.physical_cores)

    # Per-thread working set should fit in L2. py-cpuinfo reports L2 as
    # a total across cores on most CPUs, so divide by physical cores.
    # Floor at 64 KB (below that, syscall and generator overhead dominate).
    per_core_l2_kb = hw.l2_kb
    if hw.physical_cores > 1 and hw.l2_kb > 64:
        per_core_l2_kb = max(64, hw.l2_kb // hw.physical_cores)
    l3_per_thread_kb = max(512, hw.l3_kb // threads) if threads else hw.l3_kb

    target_kb = min(per_core_l2_kb, l3_per_thread_kb)
    target_kb = max(target_kb, 64)

    # 1 byte per digit (ASCII), so KB × 1024 == thousands of digits.
    chunk = 1 << int(math.log2(max(8192, target_kb * 1024)))
    chunk = min(chunk, 1_000_000)

    return TuneConfig(
        backend="auto",
        chunk_size=chunk,
        threads=threads,
        algorithm="auto",
    )


def _benchmark(backend: str, digits: int = BENCH_DIGITS) -> float | None:
    try:
        t0 = time.perf_counter()
        total = 0
        for c in generate_pi(digits, backend, 50_000):
            total += len(c)
            if total >= digits:
                break
        dt = time.perf_counter() - t0
        if total < digits:
            return None
        return round(dt, 4)
    except Exception:
        return None


def tune(hw: HardwareProfile | None = None, force: bool = False) -> TuneConfig:
    hw = hw or detect()
    fp = fingerprint(hw)

    if not force and CONFIG_PATH.exists():
        try:
            saved = TuneConfig(**json.loads(CONFIG_PATH.read_text()))
            if (saved.fingerprint == fp
                    and saved.benchmarked
                    and saved.bench_size == BENCH_DIGITS):
                return saved
        except Exception:
            pass

    cfg = prior(hw)

    candidates = ["gmpy2", "mpmath"]
    results: dict[str, float] = {}
    for b in candidates:
        t = _benchmark(b)
        if t is not None:
            results[b] = t

    if results:
        cfg.backend = min(results, key=results.get)
    cfg.benchmarked = results
    cfg.fingerprint = fp
    cfg.bench_size = BENCH_DIGITS
    CONFIG_PATH.write_text(json.dumps(asdict(cfg), indent=2))
    return cfg


def load_config() -> TuneConfig:
    return tune()

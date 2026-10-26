"""Command-line entry point."""
from __future__ import annotations
import argparse, sys, time

from .encoding import word_to_digits
from .pi_generator import generate_pi
from .search import search_stream
from .probability import match_probability, expected_wait_digits
from .hardware import detect
from .autotune import tune
from . import splash


def _limited(digits: int, backend: str, chunk: int):
    total = 0
    for c in generate_pi(digits + 16, backend, chunk):
        rem = digits - total
        if rem <= 0:
            return
        take = c[:rem]
        yield take
        total += len(take)


def _progress_printer():
    if not sys.stdout.isatty():
        return None
    t0 = time.perf_counter()
    def cb(consumed: int):
        dt = time.perf_counter() - t0
        rate = consumed / dt if dt > 0 else 0
        sys.stdout.write(f"\r  {consumed:>13,} digits  "
                         f"{rate:>12,.0f}/s  {dt:>6.1f}s")
        sys.stdout.flush()
    return cb


def _max_safe_digits(hw) -> int:
    bytes_budget = hw.ram_gb * (1024 ** 3) * 0.4
    digits_budget = int(bytes_budget / 2)
    return max(10_000_000, min(digits_budget, 2_000_000_000))


def _unlimited_search(pattern, backend, chunk, algo, hw, initial, ceiling=None):
    target = max(10_000, initial)
    ram_ceiling = _max_safe_digits(hw)
    if ceiling is None:
        ceiling = ram_ceiling
    else:
        ceiling = min(ceiling, ram_ceiling)
    if target > ceiling:
        target = ceiling

    round_n = 1
    while True:
        print(f"\n[Round {round_n}] Searching first {target:,} digits...")
        cb = _progress_printer()
        t0 = time.perf_counter()
        try:
            found_at, consumed = search_stream(
                _limited(target, backend, chunk), pattern, algo,
                progress_cb=cb,
                progress_every=max(100_000, target // 20),
            )
        except KeyboardInterrupt:
            print("\n\n  Interrupted.")
            return 130, -1, 0
        elapsed = time.perf_counter() - t0
        if cb is not None:
            sys.stdout.write("\r" + " " * 60 + "\r")
        if found_at >= 0:
            print(f"  FOUND at position {found_at:,}")
            print(f"  {consumed:,} digits in {elapsed:.2f}s "
                  f"({consumed/elapsed:,.0f} digits/s)")
            return 0, found_at, consumed
        print(f"  Not found in {target:,} digits "
              f"({elapsed:.2f}s, {consumed/elapsed:,.0f} digits/s)")
        next_target = min(target * 10, ceiling)
        if next_target == target:
            print(f"\n  Reached safety ceiling of {ceiling:,} digits "
                  f"(~{hw.ram_gb:.0f} GB RAM).")
            print(f"  For deeper search: install y-cruncher or use a "
                  f"C binary-splitting backend.")
            return 2, -1, 0
        est_gb = next_target / (1024 ** 3) * 2
        if est_gb > 0.5 * hw.ram_gb:
            print(f"  WARNING: round {round_n+1} will use ~{est_gb:.1f} GB RAM")
        target = next_target
        round_n += 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pi-search",
        description="Search for a numeric pattern or encoded word inside pi.",
    )
    p.add_argument("pattern", help="digits, or a word if --word is set")
    p.add_argument("--word", action="store_true", help="treat PATTERN as text")
    p.add_argument("--encoding", choices=["ascii", "padded"], default="padded")
    p.add_argument("--max-digits", type=int, default=10_000)
    p.add_argument("--unlimited", action="store_true",
                   help="keep searching (doubling) until found or RAM ceiling")
    p.add_argument("--backend",
                   choices=["auto", "gmpy2", "mpmath", "spigot"],
                   default="auto")
    p.add_argument("--chunk-size", type=int, default=0)
    p.add_argument("--algorithm",
                   choices=["auto", "naive", "kmp", "rabin-karp"],
                   default="auto")
    p.add_argument("--save-on-found", metavar="PATH")
    p.add_argument("--tune", action="store_true")
    p.add_argument("--progress", action="store_true",
                   help="live rate display (auto-on in --unlimited)")
    p.add_argument("--no-splash", action="store_true")
    p.add_argument("--no-probability", action="store_true")
    p.add_argument("--quiet", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if not argv or argv[0] in ("-i", "--interactive"):
        from .interactive import run
        return run()
    args = build_parser().parse_args(argv)

    hw = detect()
    cfg = tune(hw, force=args.tune)

    backend = args.backend if args.backend != "auto" else cfg.backend
    chunk   = args.chunk_size or cfg.chunk_size
    algo    = args.algorithm if args.algorithm != "auto" else cfg.algorithm

    if not args.no_splash and not args.quiet:
        print(splash.render(hw, cfg))
        print()

    if args.word:
        pattern = word_to_digits(args.pattern, args.encoding)
        if not args.quiet:
            print(f"Encoded '{args.pattern}' -> '{pattern}' ({args.encoding})")
    else:
        pattern = args.pattern

    if not pattern:
        print("error: empty pattern", file=sys.stderr)
        return 1

    if args.unlimited:
        ceiling = _max_safe_digits(hw)
        if not args.quiet:
            print(f"Unlimited mode: doubling search, ceiling "
                  f"{ceiling:,} digits (RAM-bound)")
        rc, found_at, _consumed = _unlimited_search(
            pattern, backend, chunk, algo, hw, args.max_digits)
        if rc == 0 and args.save_on_found:
            _save(args.save_on_found, found_at + len(pattern), backend, chunk)
            print(f"  Saved to {args.save_on_found}")
        return rc

    if not args.quiet:
        print(f"Searching '{pattern}' (len {len(pattern)}) "
              f"in {args.max_digits:,} digits   "
              f"[backend={backend}, chunk={chunk:,}, algo={algo}]")

    cb = _progress_printer() if args.progress else None
    t0 = time.perf_counter()
    found_at, consumed = search_stream(
        _limited(args.max_digits, backend, chunk), pattern, algo,
        progress_cb=cb,
        progress_every=max(100_000, args.max_digits // 20),
    )
    if cb is not None:
        sys.stdout.write("\r" + " " * 60 + "\r")
    elapsed = time.perf_counter() - t0
    speed = consumed / elapsed if elapsed else 0.0

    if found_at >= 0:
        print(f"\n  FOUND at position {found_at:,}")
        print(f"  {consumed:,} digits in {elapsed:.2f}s "
              f"({speed:,.0f} digits/s)")
        if args.save_on_found:
            _save(args.save_on_found, found_at + len(pattern), backend, chunk)
            print(f"  Saved to {args.save_on_found}")
        return 0

    print(f"\n  Not found in first {consumed:,} digits.")
    print(f"  {elapsed:.2f}s  ({speed:,.0f} digits/s)")
    if not args.no_probability:
        p  = match_probability(len(pattern), consumed)
        ew = expected_wait_digits(len(pattern))
        print(f"  P(match by now) ~ {p * 100:.4f}%")
        print(f"  Expected wait   ~ {ew:,.0f} digits")
    return 2


def _save(path: str, count: int, backend: str, chunk: int) -> None:
    written = 0
    with open(path, "w", encoding="utf-8") as f:
        for c in generate_pi(count, backend, chunk):
            take = c[:count - written]
            f.write(take)
            written += len(take)
            if written >= count:
                break


if __name__ == "__main__":
    raise SystemExit(main())

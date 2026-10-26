"""Interactive Kali-Linux-style menu for pi-search."""
import sys
from .hardware import detect
from .autotune import tune
from .encoding import word_to_digits
from .cli import _limited, _unlimited_search, _max_safe_digits
from . import splash


RESET = "\033[0m"
DIM   = "\033[2m"
CYAN  = "\033[96m"
GREEN = "\033[92m"
YELLOW= "\033[93m"
RED   = "\033[91m"


def _box(title, lines, width=62):
    top = "\u2554" + "\u2550" * width + "\u2557"
    mid = "\u2560" + "\u2550" * width + "\u2563"
    bot = "\u255a" + "\u2550" * width + "\u255d"
    out = [f"{CYAN}{top}{RESET}"]
    out.append(f"{CYAN}\u2551{RESET}{title.center(width)}{CYAN}\u2551{RESET}")
    out.append(f"{CYAN}{mid}{RESET}")
    for line in lines:
        if line == "---":
            out.append(f"{CYAN}{mid}{RESET}")
            continue
        out.append(f"{CYAN}\u2551{RESET} {line.ljust(width - 2)} {CYAN}\u2551{RESET}")
    out.append(f"{CYAN}{bot}{RESET}")
    return "\n".join(out)


def _prompt(msg):
    return input(f"{CYAN}\u279c {RESET}{msg}: ").strip()


def _menu(title, options):
    lines = [f"[{k}] {label}" for k, label in options]
    print(_box(title, lines))
    keys = [k for k, _ in options]
    while True:
        choice = _prompt("Select")
        if choice in keys:
            return choice
        print(f"{RED}Invalid. Options: {', '.join(keys)}{RESET}")


def _ask_int(msg, default=None):
    while True:
        hint = f" [{default}]" if default is not None else ""
        raw = _prompt(msg + hint)
        if raw == "" and default is not None:
            return default
        try:
            return int(raw.replace(",", "").replace("_", ""))
        except ValueError:
            print(f"{RED}Enter a number.{RESET}")


def _confirm(msg):
    return _prompt(msg + " (y/N)").lower() in ("y", "yes")


def _print_settings(cfg, hw):
    ram_cap = _max_safe_digits(hw)
    bench = "  ".join(f"{k}={v:.3f}s" for k, v in cfg.benchmarked.items()) \
            if cfg.benchmarked else "none"
    print(_box("SETTINGS", [
        f"Backend      : {cfg.backend}",
        f"Chunk size   : {cfg.chunk_size:,} digits",
        f"Threads      : {cfg.threads}",
        f"Algorithm    : {cfg.algorithm}",
        f"Benchmark    : {bench}",
        f"RAM safe cap : {ram_cap:,} digits",
    ]))


def _run_fixed(pattern, max_digits, cfg):
    from .search import search_stream
    from .probability import match_probability, expected_wait_digits
    import time

    print(f"{DIM}Searching in {max_digits:,} digits...{RESET}")
    t0 = time.perf_counter()
    try:
        found_at, consumed = search_stream(
            _limited(max_digits, cfg.backend, cfg.chunk_size),
            pattern, cfg.algorithm,
        )
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Search interrupted.{RESET}")
        return 130
    elapsed = time.perf_counter() - t0
    rate = consumed / elapsed if elapsed else 0

    if found_at >= 0:
        print(f"{GREEN}\u2713 FOUND at position {found_at:,}{RESET}")
        print(f"  {consumed:,} digits in {elapsed:.2f}s ({rate:,.0f}/s)")
        return 0

    p = match_probability(len(pattern), consumed)
    ew = expected_wait_digits(len(pattern))
    print(f"{YELLOW}\u2717 Not found in {consumed:,} digits{RESET}")
    print(f"  {elapsed:.2f}s ({rate:,.0f}/s)")
    print(f"  P(match by now) \u2248 {p*100:.4f}%")
    print(f"  Expected wait    \u2248 {ew:,.0f} digits")
    return 2


def _search_flow(cfg, hw):
    kind = _menu("WHAT TO SEARCH", [
        ("1", "Search for a NUMBER (digits)"),
        ("2", "Search for a STRING (encoded as digits)"),
        ("3", "Back to main menu"),
    ])
    if kind == "3":
        return

    if kind == "1":
        pattern = _prompt("Enter digits to search")
        if not pattern or not pattern.isdigit():
            print(f"{RED}Must be digits only.{RESET}")
            return
    else:
        text = _prompt("Enter text to search")
        if not text:
            print(f"{RED}Empty string.{RESET}")
            return
        enc = _menu("ENCODING", [
            ("1", "Padded ASCII \u2014 unambiguous (recommended)"),
            ("2", "Variable ASCII \u2014 shorter, ambiguous"),
        ])
        pattern = word_to_digits(text, "padded" if enc == "1" else "ascii")
        print(f"  {DIM}Encoded '{text}' \u2192 '{pattern}' ({len(pattern)} digits){RESET}")

    ram_cap = _max_safe_digits(hw)
    scope = _menu("SEARCH SCOPE", [
        ("1", "Fixed range \u2014 specify max digits"),
        ("2", f"Indefinitely \u2014 doubling (logical cap 10^12, RAM caps ~{ram_cap:,})"),
        ("3", "Back to main menu"),
    ])
    if scope == "3":
        return

    if scope == "1":
        n = _ask_int("Max digits (0 = until Ctrl+C)")
        if n == 0:
            print(f"{YELLOW}\u26a0 Range 0 = run until Ctrl+C.")
            print(f"  Effective RAM cap on this machine: {ram_cap:,} digits.")
            print(f"  Beyond that the OS will kill the process.{RESET}")
            if not _confirm("Continue?"):
                return
            _unlimited_search(pattern, cfg.backend, cfg.chunk_size,
                              cfg.algorithm, hw, initial=10_000, ceiling=10**15)
        else:
            if n > ram_cap:
                print(f"{YELLOW}\u26a0 Requested {n:,} exceeds RAM-safe cap {ram_cap:,}{RESET}")
                if not _confirm(f"Clamp to {ram_cap:,}?"):
                    return
                n = ram_cap
            _run_fixed(pattern, n, cfg)
    else:
        print(f"{DIM}Doubling search \u2014 will stop at RAM cap or Ctrl+C{RESET}")
        _unlimited_search(pattern, cfg.backend, cfg.chunk_size,
                          cfg.algorithm, hw, initial=10_000, ceiling=10**12)


def _run_loop():
    hw = detect()
    cfg = tune(hw)
    print(splash.render(hw, cfg))

    while True:
        print()
        choice = _menu("PI PATTERN SEARCHER", [
            ("1", "Search"),
            ("2", "View current settings"),
            ("3", "Re-tune for this machine"),
            ("4", "Exit"),
        ])

        if choice == "4":
            print(f"{DIM}Goodbye.{RESET}")
            return 0
        if choice == "2":
            _print_settings(cfg, hw)
            continue
        if choice == "3":
            print(f"{YELLOW}Re-benchmarking (~2s)...{RESET}")
            cfg = tune(hw, force=True)
            print(f"{GREEN}\u2713 Winner: {cfg.backend}{RESET}")
            continue

        _search_flow(cfg, hw)
        if not _confirm("Search again?"):
            return 0


def run():
    try:
        return _run_loop()
    except KeyboardInterrupt:
        print(f"\n{DIM}Interrupted.{RESET}")
        return 130

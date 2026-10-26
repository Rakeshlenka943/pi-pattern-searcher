"""Startup splash: rotating pi ASCII art + autotune report."""
import random
from .hardware import HardwareProfile


ARTS = [
    # 1. Block "PI"
    r"""
   ____  _    ____            _     _
  |  _ \(_)  / ___|  ___  ___| |__ (_)___
  | |_) | |  \___ \ / _ \/ __| '_ \| / __|
  |  __/| |   ___) |  __/ (__| | | | \__ \
  |_|   |_|  |____/ \___|\___|_| |_|_|___/

    3.14159265358979323846264338327950288...
""",
    # 2. Greek pi (square)
    r"""
     ______________
    |  _____ _____ |
    | |     |     ||
    | |     |     ||
    | |     |     ||
    |_|     |_____||

       3.14159265358979...
""",
    # 3. Circular motif
    r"""
        . - ~ - .
      /           \
     |      π      |
     |             |
     |  3.141592   |
     |             |
      \           /
        ' - ~ - '

   3.14159265358979323846...
""",
    # 4. Spiral
    r"""
              *
          *       *
       *             *
     *        π        *
     *                 *
       *             *
          *       *
              *

   3.14159265358979323846...
""",
    # 5. Numeric block
    r"""
   +-------------------+
   | 3.1415926535897   |
   | 9323846264338     |
   | 3279502884197     |
   | 1693993751058     |
   +-------------------+
        ~ pi ~

   3.14159265358979323846...
""",
]


def render(hw: HardwareProfile, cfg, art: str | None = None) -> str:
    if art is None:
        art = random.choice(ARTS)
    lines = [art]
    lines.append(f"  CPU       : {hw.cpu_model}")
    lines.append(f"  Arch      : {hw.arch}  |  "
                 f"Cores: {hw.physical_cores}P / {hw.logical_cores}L")
    lines.append(f"  Cache     : L1 {hw.l1_kb}K  L2 {hw.l2_kb}K  L3 {hw.l3_kb}K")
    lines.append(f"  RAM       : {hw.ram_gb} GB")
    if hw.has_cuda:
        lines.append(f"  GPU       : {hw.cuda_name}  ({hw.cuda_vram_gb} GB VRAM)")
    else:
        lines.append( "  GPU       : none detected")
    lines.append(f"  Compiler  : {hw.compiler or 'not found'}")
    lines.append(f"  Backend   : {cfg.backend.upper()}")
    if cfg.benchmarked:
        ranked = sorted(cfg.benchmarked.items(), key=lambda kv: kv[1])
        lines.append("  Benchmark : " + "   ".join(
            f"{k}={v:.3f}s" for k, v in ranked))
    lines.append(f"  Tuned     : chunk={cfg.chunk_size:,}  "
                 f"threads={cfg.threads}  search={cfg.algorithm}")
    return "\n".join(lines)

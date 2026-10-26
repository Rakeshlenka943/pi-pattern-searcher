"""Deep hardware introspection — Linux-first, portable fallback."""
from __future__ import annotations
import platform, shutil, subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class HardwareProfile:
    os: str
    arch: str
    cpu_model: str
    physical_cores: int
    logical_cores: int
    l1_kb: int
    l2_kb: int
    l3_kb: int
    ram_gb: float
    has_avx2: bool
    has_avx512: bool
    has_neon: bool
    has_cuda: bool
    cuda_name: str
    cuda_vram_gb: float
    has_compiler: bool
    compiler: str
    is_wsl: bool = False
    extra: dict = field(default_factory=dict)


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True,
                              timeout=4).stdout
    except Exception:
        return ""


def _linux_cache_kb(level: int) -> int:
    total = 0
    base = Path("/sys/devices/system/cpu/cpu0/cache")
    if not base.exists():
        return 0
    for idx in base.glob("index*"):
        try:
            lvl = int((idx / "level").read_text().strip())
            typ = (idx / "type").read_text().strip()
            size = (idx / "size").read_text().strip()
            if lvl == level and typ == "Data":
                total += int(size.rstrip("K"))
        except Exception:
            continue
    return total


def _proc_cpuinfo() -> dict[str, str]:
    d: dict[str, str] = {}
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if ":" in line:
                    k, v = line.split(":", 1)
                    d.setdefault(k.strip(), v.strip())
                elif not line.strip():
                    break
    except OSError:
        pass
    return d


def _detect_cuda() -> tuple[bool, str, float]:
    out = _run(["nvidia-smi", "--query-gpu=name,memory.total",
                "--format=csv,noheader,nounits"])
    if not out.strip():
        return False, "", 0.0
    line = out.strip().splitlines()[0]
    parts = [p.strip() for p in line.split(",")]
    if len(parts) < 2:
        return True, parts[0], 0.0
    try:
        vram = round(float(parts[1]) / 1024.0, 1)
    except ValueError:
        vram = 0.0
    return True, parts[0], vram


def detect() -> HardwareProfile:
    import psutil

    flags: set[str] = set()
    model = platform.processor() or "unknown"
    l1 = l2 = l3 = 0

    if platform.system() == "Linux":
        try:
            import cpuinfo
            info = cpuinfo.get_cpu_info()
            model = info.get("brand_raw", model)
            flags = set(info.get("flags", []))
            l1 = int(info.get("l1_data_cache_size") or 0) // 1024
            l2 = int(info.get("l2_cache_size") or 0) // 1024
            l3 = int(info.get("l3_cache_size") or 0) // 1024
        except Exception:
            ci = _proc_cpuinfo()
            model = ci.get("model name", model)
            flags = set(ci.get("flags", "").split())
        if not l1:
            l1 = _linux_cache_kb(1)
        if not l2:
            l2 = _linux_cache_kb(2)
        if not l3:
            l3 = _linux_cache_kb(3)

    has_cuda, cuda_name, vram = _detect_cuda()
    compiler = shutil.which("gcc") or shutil.which("clang") or shutil.which("cc")
    mem = psutil.virtual_memory().total / (1024 ** 3)
    is_wsl = "microsoft" in platform.uname().release.lower()
    arch = platform.machine()

    return HardwareProfile(
        os=platform.system(),
        arch=arch,
        cpu_model=model,
        physical_cores=psutil.cpu_count(logical=False) or 1,
        logical_cores=psutil.cpu_count(logical=True) or 1,
        l1_kb=l1 or 32,
        l2_kb=l2 or 256,
        l3_kb=l3 or 4096,
        ram_gb=round(mem, 1),
        has_avx2="avx2" in flags,
        has_avx512="avx512f" in flags,
        has_neon=("neon" in flags) or arch in ("arm64", "aarch64"),
        has_cuda=has_cuda,
        cuda_name=cuda_name,
        cuda_vram_gb=vram,
        has_compiler=bool(compiler),
        compiler=Path(compiler).name if compiler else "",
        is_wsl=is_wsl,
    )

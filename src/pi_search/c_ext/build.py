"""Compile and load the Chudnovsky C extension on first use."""
import ctypes
import shutil
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).parent
_SRC = _HERE / "chudnovsky.c"

if sys.platform == "darwin":
    _LIB = _HERE / "libpi_chudnovsky.dylib"
elif sys.platform == "win32":
    _LIB = _HERE / "pi_chudnovsky.dll"
else:
    _LIB = _HERE / "libpi_chudnovsky.so"

_loaded = None
_last_error = None


def _find_compiler():
    for name in ("gcc", "cc", "clang"):
        path = shutil.which(name)
        if path:
            return path
    return None


def _needs_build():
    if not _LIB.exists():
        return True
    if not _SRC.exists():
        return False
    return _LIB.stat().st_mtime < _SRC.stat().st_mtime


def _compile():
    global _last_error
    compiler = _find_compiler()
    if compiler is None:
        _last_error = "no C compiler found (gcc/cc/clang)"
        return False

    if sys.platform == "darwin":
        cmd = [compiler, "-O2", "-march=x86-64-v2", "-dynamiclib", "-fPIC",
               str(_SRC), "-o", str(_LIB), "-lgmp"]
    else:
        cmd = [compiler, "-O2", "-march=x86-64-v2", "-shared", "-fPIC",
               str(_SRC), "-o", str(_LIB), "-lgmp"]

    import os as _os
    try:
        _os.nice(19)
    except (AttributeError, OSError):
        pass
    print("[pi-search] Compiling C extension (gentle mode, -O2)…", flush=True)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            _last_error = "compile failed: " + result.stderr.strip()[:300]
            return False
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        _last_error = "compile error: " + str(e)
        return False


def load():
    global _loaded
    if _loaded is not None:
        return _loaded
    if _needs_build():
        if not _compile():
            raise RuntimeError("C extension unavailable: " + (_last_error or "unknown"))
    lib = ctypes.CDLL(str(_LIB))
    lib.compute_pi_c.argtypes = [ctypes.c_int]
    lib.compute_pi_c.restype = ctypes.c_void_p
    lib.free_pi_string.argtypes = [ctypes.c_void_p]
    lib.free_pi_string.restype = None
    _loaded = lib
    return lib


def is_available():
    try:
        load()
        return True
    except Exception:
        return False


def last_error():
    return _last_error

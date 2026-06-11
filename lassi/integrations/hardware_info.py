from __future__ import annotations

import asyncio
import json
import platform
import re
import shutil
import subprocess
from pathlib import Path


# ---------------------------------------------------------------------------
# get_machine_info_impl
# ---------------------------------------------------------------------------


def _run(cmd: list[str], timeout: float = 2.0) -> str | None:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if proc.returncode != 0:
            return None
        return proc.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None


def _sysctl(name: str) -> str | None:
    out = _run(["sysctl", "-n", name])
    return out.strip() if out else None


def _os_info() -> dict:
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "platform": platform.platform(),
        "python": platform.python_version(),
    }


def _memory_info() -> dict:
    try:
        import psutil
    except ImportError:
        return _memory_info_fallback()
    vm = psutil.virtual_memory()
    return {
        "total_gb": round(vm.total / (1024**3), 2),
        "available_gb": round(vm.available / (1024**3), 2),
        "used_gb": round(vm.used / (1024**3), 2),
        "usage_percent": vm.percent,
    }


def _memory_info_fallback() -> dict:
    # macOS: sysctl hw.memsize gives total bytes. Linux: /proc/meminfo MemTotal.
    if platform.system() == "Darwin":
        total = _sysctl("hw.memsize")
        if total and total.isdigit():
            return {"total_gb": round(int(total) / (1024**3), 2), "note": "psutil not installed; only total reported"}
    if platform.system() == "Linux":
        meminfo = Path("/proc/meminfo")
        if meminfo.exists():
            try:
                for line in meminfo.read_text().splitlines():
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        return {"total_gb": round(kb / (1024**2), 2), "note": "psutil not installed; only total reported"}
            except OSError:
                pass
    return {"error": "psutil not installed and OS-native fallback failed"}


def _cpu_info_darwin() -> dict:
    brand = _sysctl("machdep.cpu.brand_string") or platform.processor() or "unknown"
    vendor = _sysctl("machdep.cpu.vendor") or ("Apple" if "Apple" in brand else "unknown")
    info: dict = {
        "architecture": platform.machine(),
        "brand": brand,
        "vendor": vendor,
        "cores_physical": int(_sysctl("hw.physicalcpu") or 0) or None,
        "cores_logical": int(_sysctl("hw.logicalcpu") or 0) or None,
    }

    # Performance vs efficiency cores (Apple Silicon)
    perflevels = _sysctl("hw.nperflevels")
    if perflevels and perflevels.isdigit() and int(perflevels) > 1:
        info["performance_cores"] = int(_sysctl("hw.perflevel0.physicalcpu") or 0) or None
        info["efficiency_cores"] = int(_sysctl("hw.perflevel1.physicalcpu") or 0) or None

    # Frequencies (Hz on macOS Intel; Apple Silicon doesn't expose hw.cpufrequency).
    freq_hz = _sysctl("hw.cpufrequency")
    freq_max = _sysctl("hw.cpufrequency_max")
    if freq_hz or freq_max:
        info["frequency_mhz"] = {
            "current": (int(freq_hz) / 1e6) if freq_hz and freq_hz.isdigit() else None,
            "max": (int(freq_max) / 1e6) if freq_max and freq_max.isdigit() else None,
        }

    # Cache hierarchy
    cache = {}
    for key, label in [
        ("hw.l1icachesize", "l1i_kb"),
        ("hw.l1dcachesize", "l1d_kb"),
        ("hw.l2cachesize", "l2_kb"),
        ("hw.l3cachesize", "l3_kb"),
    ]:
        v = _sysctl(key)
        if v and v.isdigit() and int(v) > 0:
            cache[label] = int(v) // 1024
    if cache:
        info["cache"] = cache

    # Feature/capability flags
    features: list[str] = []
    for src in ("machdep.cpu.features", "machdep.cpu.leaf7_features", "machdep.cpu.extfeatures"):
        v = _sysctl(src)
        if v:
            features.extend(tok.lower() for tok in v.split())
    # Apple Silicon advertises capability via hw.optional.*=1
    if platform.machine() == "arm64":
        out = _run(["sysctl", "-a"], timeout=3.0) or ""
        for line in out.splitlines():
            m = re.match(r"hw\.optional\.([\w.]+):\s*1\s*$", line) or re.match(
                r"hw\.optional\.([\w.]+)\s*=\s*1\s*$", line
            )
            if m:
                features.append(m.group(1))
    if features:
        info["features"] = sorted(set(features))

    return info


def _cpu_info_linux() -> dict:
    info: dict = {
        "architecture": platform.machine(),
        "brand": None,
        "vendor": None,
        "cores_physical": None,
        "cores_logical": None,
    }
    try:
        import psutil
        info["cores_logical"] = psutil.cpu_count(logical=True)
        info["cores_physical"] = psutil.cpu_count(logical=False)
        freq = psutil.cpu_freq()
        if freq:
            info["frequency_mhz"] = {
                "current": freq.current,
                "min": freq.min,
                "max": freq.max,
            }
    except Exception:
        pass

    flags: list[str] = []
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        try:
            text = cpuinfo.read_text()
        except OSError:
            text = ""
        for line in text.splitlines():
            if ":" not in line:
                continue
            key, _, val = line.partition(":")
            key, val = key.strip().lower(), val.strip()
            if key == "model name" and not info.get("brand"):
                info["brand"] = val
            elif key == "vendor_id" and not info.get("vendor"):
                info["vendor"] = val
            elif key in {"flags", "features"} and not flags:
                flags = val.split()
    if flags:
        info["features"] = sorted(set(flags))

    # Cache via lscpu (best-effort, structured output)
    lscpu = _run(["lscpu", "-J"], timeout=2.0)
    if lscpu:
        try:
            data = json.loads(lscpu).get("lscpu", [])
            cache = {}
            for entry in data:
                field = entry.get("field", "").rstrip(":").lower()
                data_val = entry.get("data")
                if field == "l1d cache" and data_val:
                    cache["l1d"] = data_val
                elif field == "l1i cache" and data_val:
                    cache["l1i"] = data_val
                elif field == "l2 cache" and data_val:
                    cache["l2"] = data_val
                elif field == "l3 cache" and data_val:
                    cache["l3"] = data_val
            if cache:
                info["cache"] = cache
        except (json.JSONDecodeError, AttributeError):
            pass

    return info


def _cpu_info() -> dict:
    if platform.system() == "Darwin":
        return _cpu_info_darwin()
    if platform.system() == "Linux":
        return _cpu_info_linux()
    # Fallback for other OSes
    return {
        "architecture": platform.machine(),
        "brand": platform.processor() or "unknown",
        "vendor": "unknown",
    }


def _gpu_summary_sync() -> dict:
    # NVIDIA
    if shutil.which("nvidia-smi"):
        out = _run([
            "nvidia-smi",
            "--query-gpu=name,memory.total,driver_version,compute_cap",
            "--format=csv,noheader,nounits",
        ], timeout=3.0)
        if out:
            gpus = []
            for line in out.strip().splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 4:
                    gpus.append({
                        "name": parts[0],
                        "memory_mb": _try_int(parts[1]),
                        "driver_version": parts[2],
                        "compute_capability": parts[3],
                    })
            return {"vendor": "NVIDIA", "devices": gpus}

    # AMD
    if shutil.which("rocm-smi"):
        out = _run(["rocm-smi", "--showproductname", "--showmeminfo", "vram", "--csv"], timeout=3.0)
        return {"vendor": "AMD", "raw": (out or "").strip()}

    # Intel discrete
    if shutil.which("xpu-smi"):
        out = _run(["xpu-smi", "discovery"], timeout=3.0)
        return {"vendor": "Intel", "raw": (out or "").strip()}

    # Apple Silicon: parse `system_profiler SPDisplaysDataType -json`
    if platform.system() == "Darwin" and shutil.which("system_profiler"):
        out = _run(["system_profiler", "-json", "SPDisplaysDataType"], timeout=4.0)
        if out:
            try:
                data = json.loads(out)
                devices = []
                for entry in data.get("SPDisplaysDataType", []):
                    devices.append({
                        "name": entry.get("sppci_model") or entry.get("_name"),
                        "vendor": entry.get("spdisplays_vendor"),
                        "cores": entry.get("sppci_cores"),
                        "metal": entry.get("spdisplays_metal") or entry.get("spdisplays_metalfamily"),
                        "memory": entry.get("spdisplays_vram") or entry.get("spdisplays_vram_shared"),
                    })
                if devices:
                    return {"vendor": "Apple", "devices": devices}
            except json.JSONDecodeError:
                pass

    return {"vendor": None, "note": "No GPU enumeration tool found (nvidia-smi, rocm-smi, xpu-smi, system_profiler)."}


def _try_int(s: str) -> int | None:
    try:
        return int(float(s))
    except (TypeError, ValueError):
        return None


async def get_machine_info_impl() -> str:
    def _collect():
        return {
            "os": _os_info(),
            "cpu": _cpu_info(),
            "memory": _memory_info(),
            "gpu": _gpu_summary_sync(),
        }

    try:
        info = await asyncio.to_thread(_collect)
        return json.dumps(info, indent=2, sort_keys=False, default=str)
    except Exception as exc:
        return json.dumps({"error": f"Error retrieving machine info: {exc}"}, indent=2)

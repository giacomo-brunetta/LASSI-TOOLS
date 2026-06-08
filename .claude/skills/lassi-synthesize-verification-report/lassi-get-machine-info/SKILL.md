---
name: lassi-get-machine-info
description: Structured machine fingerprint — OS, CPU (architecture, brand, vendor, cores, frequency, cache, capability flags / ISA features), RAM totals, and a GPU summary (vendor + per-device name, memory, compute capability or Metal family). Use when the user asks what hardware this machine has, what ISA extensions are available, or before any roofline / kernel-tuning work that depends on architecture.
allowed-tools:
  - Bash(python cli/lassi-get-machine-info.py*)
  - Bash(python3 cli/lassi-get-machine-info.py*)
---

Returns a single JSON document with four sections:

- **`os`** — `system`, `release`, `version`, `machine` (arch), `platform`, `python`.
- **`cpu`** — `architecture`, `brand`, `vendor`, `cores_physical` / `cores_logical` (plus `performance_cores` / `efficiency_cores` on Apple Silicon), `frequency_mhz`, `cache` (L1i/L1d/L2/L3), `features` (capability flags: `avx2`, `avx512f`, `sse4_2`, `aes`, `neon`, `arm64.fp16`, `arm64.crc`, etc. — exact list depends on platform).
- **`memory`** — `total_gb`, `available_gb`, `used_gb`, `usage_percent`.
- **`gpu`** — `vendor` (NVIDIA / AMD / Intel / Apple / null) plus a `devices` array with per-GPU `name`, `memory`, and architecture markers (`compute_capability` for NVIDIA, `metal` family for Apple, etc.). When no GPU enumeration tool is on PATH, returns `{"vendor": null, "note": "..."}`.

## Invocation

```
python cli/lassi-get-machine-info.py
```

No arguments. Output is pretty-printed JSON on stdout.

## Underlying impl

`lassi.integrations.hardware_info.get_machine_info_impl` — uses `platform`, `psutil`, `sysctl` (macOS), `/proc/cpuinfo` + `lscpu -J` (Linux), and best-effort `nvidia-smi` / `rocm-smi` / `xpu-smi` / `system_profiler SPDisplaysDataType` for the GPU section.

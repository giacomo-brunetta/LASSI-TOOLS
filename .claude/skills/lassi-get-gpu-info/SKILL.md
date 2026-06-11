---
name: lassi-get-gpu-info
description: Retrieve GPU information using whichever vendor tool is available — nvidia-smi, rocm-smi, xpu-smi, or `system_profiler SPDisplaysDataType` on macOS / Apple Silicon. Use when the user asks what GPU is in the machine, its memory, or driver version.
allowed-tools:
  - Bash(nvidia-smi *)
  - Bash(rocm-smi *)
  - Bash(xpu-smi *)
  - Bash(system_profiler *)
  - Bash(which *)
---

There's no LASSI wrapper for this — invoke the vendor SMI tool directly. Try each in turn and stop at the first one that prints output. If you need the structured cross-vendor view, use `lassi-get-machine-info` instead (its `gpu` section already aggregates these).

## Fallback chain

```bash
if command -v nvidia-smi >/dev/null; then
  nvidia-smi --query-gpu=name,memory.total,memory.free,utilization.gpu,driver_version --format=csv
elif command -v rocm-smi >/dev/null; then
  rocm-smi --showproductname --showmeminfo vram --showdriverversion
elif command -v xpu-smi >/dev/null; then
  xpu-smi dump
elif [ "$(uname)" = "Darwin" ]; then
  # macOS / Apple Silicon — JSON form is the most parseable.
  system_profiler -json SPDisplaysDataType
else
  echo "No GPU enumeration tool found (nvidia-smi, rocm-smi, xpu-smi, system_profiler)."
fi
```

## Quick one-liners

- NVIDIA driver + VRAM only: `nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader`
- NVIDIA live usage: `nvidia-smi --query-gpu=utilization.gpu,utilization.memory,temperature.gpu --format=csv -l 1`
- AMD VRAM only: `rocm-smi --showmeminfo vram --csv`
- Apple Silicon chip name only: `system_profiler SPDisplaysDataType | grep -E "Chipset Model|Metal" | head -4`

## Notes

- All four SMIs return non-JSON formats by default. `nvidia-smi --format=csv` is the most automation-friendly; `rocm-smi --csv` and `system_profiler -json` likewise give parseable output.
- On macOS, `system_profiler SPDisplaysDataType` blocks for a couple of seconds the first time it runs (it spins up the display agent). Cache the output if you call it repeatedly.
- If none of these exist the host has no discrete GPU or its driver tools aren't installed — fall back to whatever the OS reports (e.g. `lspci | grep -i vga` on Linux).

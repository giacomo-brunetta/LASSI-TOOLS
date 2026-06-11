---
name: lassi-get-toolchain-info
description: Report effective Python, torch, torch-mlir, and LLVM-related toolchain versions. Use when diagnosing version skew before a translation/export task or when the user asks "what version of torch-mlir do we have".
allowed-tools:
  - Bash(python *)
  - Bash(python3 *)
  - Bash(clang --version)
  - Bash(clang++ --version)
  - Bash(llvm-config *)
  - Bash(mlir-opt --version)
  - Bash(torch-mlir-opt --version)
  - Bash(which *)
---

Probe each component of the C → torch → MLIR → SODA pipeline directly. There's no LASSI wrapper for this — call the tools themselves.

## Python + torch + torch-mlir versions

```bash
python3 - <<'PY'
import sys, platform, json
info = {
    "python": {"executable": sys.executable, "version": sys.version.split()[0], "platform": platform.platform()},
}
try:
    import torch
    info["torch"] = {"version": torch.__version__, "file": torch.__file__}
except Exception as e:
    info["torch"] = {"error": str(e)}
try:
    import torch_mlir
    info["torch_mlir"] = {
        "version": getattr(torch_mlir, "__version__", None),
        "file": torch_mlir.__file__,
        "path": list(torch_mlir.__path__),
    }
    try:
        import torch_mlir.torchscript as ts
        info["torch_mlir"]["torchscript_compile_available"] = hasattr(ts, "compile")
    except Exception as e:
        info["torch_mlir"]["torchscript_error"] = str(e)
except Exception as e:
    info["torch_mlir"] = {"error": str(e)}
print(json.dumps(info, indent=2))
PY
```

## LLVM / MLIR binaries

```bash
for tool in clang clang++ llvm-config mlir-opt torch-mlir-opt; do
  path=$(which "$tool" 2>/dev/null || true)
  if [ -n "$path" ]; then
    echo "=== $tool ($path) ==="
    "$tool" --version 2>&1 | head -3
  else
    echo "=== $tool: NOT FOUND ==="
  fi
done
```

## Notes

- `torch_mlir.__version__` is sometimes absent on dev installs — the `__path__` print above lets you `pip show torch-mlir` for the canonical wheel version.
- `llvm-config --version` prints the LLVM lib version; `clang --version` prints both the clang and bundled LLVM version, which is often what matters for `-fsanitize=fuzzer` availability.
- On macOS Apple-clang reports an Xcode version (e.g. `Apple clang version 15.0.0`); for full upstream LLVM use the Homebrew `llvm` keg's `clang` via `$(brew --prefix llvm)/bin/clang`.

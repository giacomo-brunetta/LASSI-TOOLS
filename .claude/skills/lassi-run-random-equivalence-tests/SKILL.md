---
name: lassi-run-random-equivalence-tests
description: Randomized differential testing between a reference and a candidate implementation. Generate N random inputs, call both, compare with exact or allclose tolerances, persist any minimized counterexamples. Use as the broad-coverage equivalence check before fuzzing.
allowed-tools:
  - Bash(python3 *)
  - Bash(mkdir *)
  - Write
  - Read
---

Write a small Python script tailored to the two implementations and run it. Both impls must share an input schema (same shape/dtype) and the same output type.

## Loading the two implementations

- **Python module callable** — `import importlib.util; spec = importlib.util.spec_from_file_location("m", "candidate.py"); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); kernel = m.kernel`.
- **ctypes shared library (scalar)** — `import ctypes; lib = ctypes.CDLL("./libfoo.so"); lib.kernel.argtypes = [ctypes.c_double]; lib.kernel.restype = ctypes.c_double`.
- **Subprocess binary** — `subprocess.run([bin, str(x)], capture_output=True, text=True, check=True); out = float(r.stdout)`.

## Template (scalar `double(double)` example)

```python
# .verify/random_eq.py — adapt per task
import ctypes, json, random, sys, math
from pathlib import Path

CORPUS = Path(".verify/corpus/equivalence"); CORPUS.mkdir(parents=True, exist_ok=True)
RTOL, ATOL, N = 1e-6, 1e-9, 2000

a = ctypes.CDLL("./build/foo_baseline.so"); a.kernel.argtypes=[ctypes.c_double]; a.kernel.restype=ctypes.c_double
b = ctypes.CDLL("./build/foo_v2.so");       b.kernel.argtypes=[ctypes.c_double]; b.kernel.restype=ctypes.c_double

def close(x, y):
    return math.isclose(x, y, rel_tol=RTOL, abs_tol=ATOL) or (math.isnan(x) and math.isnan(y))

failures = []
rng = random.Random(0xC0FFEE)
for i in range(N):
    x = rng.uniform(-1e3, 1e3)
    ya, yb = a.kernel(x), b.kernel(x)
    if not close(ya, yb):
        failures.append({"input": x, "a": ya, "b": yb})
        (CORPUS / f"diff_{len(failures):04d}.json").write_text(json.dumps({"input": x}))
        if len(failures) >= 25: break

print(json.dumps({"runs": N, "failures": len(failures), "samples": failures[:5]}, indent=2))
sys.exit(1 if failures else 0)
```

## Invocation

```bash
mkdir -p .verify/corpus/equivalence
python3 .verify/random_eq.py
```

## Suggested workflow

1. Start with `N=200` and broad domain to sanity-check both impls execute.
2. If clean, bump to `N=10000+` and narrow ranges where you suspect issues (denormals, near-zero, very large, ±inf, NaN).
3. Persist failing inputs to `.verify/corpus/equivalence/` — they become seed corpus for `lassi-run-differential-fuzzer`.
4. Minimize counterexamples by repeatedly trying `x/2`, `round(x, k)`, etc. until you can't shrink while keeping the divergence.

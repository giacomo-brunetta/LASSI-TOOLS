from __future__ import annotations

import ctypes
import importlib.util
import math
import re
import subprocess
from pathlib import Path

import numpy as np

try:
    import torch
except Exception:
    torch = None


_NUMBER_RE = re.compile(r"[\-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][\-+]?\d+)?")


def _load_python_callable(path, entrypoint):
    spec = importlib.util.spec_from_file_location(Path(path).stem, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    fn = getattr(module, entrypoint)
    return fn


def _ctype(name):
    return {
        "double": ctypes.c_double,
        "float": ctypes.c_float,
        "int": ctypes.c_int,
        "long": ctypes.c_long,
    }[name]


def _parse_signature(signature):
    signature = signature or "double(double)"
    ret, args = signature.split("(", 1)
    args = args.rstrip(")")
    return ret.strip(), [arg.strip() for arg in args.split(",") if arg.strip()]


def _load_shared_scalar(path, entrypoint, signature):
    ret, args = _parse_signature(signature)
    lib = ctypes.CDLL(path)
    fn = getattr(lib, entrypoint)
    fn.restype = _ctype(ret)
    fn.argtypes = [_ctype(arg) for arg in args]
    return fn


def _parse_number_from_stdout(stdout):
    for line in reversed(stdout.splitlines()):
        for token in line.split():
            if "=" in token:
                val = token.rsplit("=", 1)[1]
                m = _NUMBER_RE.fullmatch(val)
                if m:
                    return float(m.group(0))
        for token in line.split():
            m = _NUMBER_RE.fullmatch(token)
            if m:
                return float(m.group(0))
    raise RuntimeError(f"binary produced no numeric stdout token:\n{stdout!r}")


def _load_binary_subprocess(path):
    path = str(path)

    def fn(case):
        cmd = [path]
        if isinstance(case, (list, tuple)):
            cmd.extend(str(c) for c in case)
        else:
            cmd.append(str(case))
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
        if proc.returncode != 0:
            raise RuntimeError(
                f"binary {path} exited {proc.returncode}: {proc.stderr.strip() or proc.stdout.strip()}"
            )
        return _parse_number_from_stdout(proc.stdout)

    return fn


def _load_callable(path, entrypoint, signature=None):
    suffix = Path(path).suffix.lower()
    if suffix == ".py":
        return _load_python_callable(path, entrypoint)
    if suffix in {".so", ".dylib", ".dll"}:
        return _load_shared_scalar(path, entrypoint, signature)
    return _load_binary_subprocess(path)


def _call(fn, input_case):
    if isinstance(input_case, (list, tuple)):
        return fn(*input_case)
    return fn(input_case)


def _to_numpy(value):
    if torch is not None and hasattr(value, "detach"):
        value = value.detach().cpu().numpy()
    return np.asarray(value)


def run_a(input_case):
    return _call(_IMPL_A, input_case)


def run_b(input_case):
    return _call(_IMPL_B, input_case)


def compare_outputs(a_out, b_out, *, rtol=1e-5, atol=1e-6, mode="allclose"):
    a_np = _to_numpy(a_out)
    b_np = _to_numpy(b_out)
    if mode == "exact":
        return bool(np.array_equal(a_np, b_np))
    return bool(np.allclose(a_np, b_np, rtol=rtol, atol=atol, equal_nan=True))


_IMPL_A = None
_IMPL_B = None


def configure(implementation_a, implementation_b, entrypoint="kernel", signature="double(double)"):
    global _IMPL_A, _IMPL_B
    _IMPL_A = _load_callable(implementation_a, entrypoint, signature)
    _IMPL_B = _load_callable(implementation_b, entrypoint, signature)

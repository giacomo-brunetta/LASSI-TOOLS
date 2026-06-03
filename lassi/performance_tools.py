from __future__ import annotations

import json
import math
import os
import platform
import re
import shutil
import socket
import statistics
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

try:
    import psutil
except Exception:  # pragma: no cover - psutil is expected in the MCP env
    psutil = None


PERF_VERDICTS = {"PASS", "REGRESSION", "IMPROVEMENT", "NEUTRAL", "UNSURE", "ERROR"}
DEFAULT_PERF_EVENTS = [
    "cycles",
    "instructions",
    "branches",
    "branch-misses",
    "cache-references",
    "cache-misses",
    "task-clock",
    "context-switches",
    "cpu-migrations",
    "page-faults",
]
SOFTWARE_ONLY_PERF_EVENTS = [
    "task-clock",
    "context-switches",
    "cpu-migrations",
    "page-faults",
    "minor-faults",
    "major-faults",
]


def _is_perf_eperm(text: str) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return (
        "no permission to enable" in lowered
        or "operation not permitted" in lowered
        or "perf_event_open" in lowered and "permitted" in lowered
    )
SPECIAL_HOTSPOT_PATTERNS = [
    "malloc",
    "free",
    "memcpy",
    "memmove",
    "operator new",
    "torch::from_blob",
    "at::native",
    "PyObject_Call",
    "pthread_mutex_lock",
]


class MetricProvider(ABC):
    """Hardware-neutral extension point for future performance backends."""

    @abstractmethod
    def collect_runtime(self, benchmark_case: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def collect_counters(self, benchmark_case: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def collect_memory_traffic(self, benchmark_case: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def collect_flops(self, benchmark_case: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def collect_hardware_model(self) -> dict[str, Any]:
        raise NotImplementedError


def _now_task_id(prefix: str) -> str:
    return f"{prefix}_{time.strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"


def _artifact_dir(default_root: str, artifact_dir: str | None) -> Path:
    if artifact_dir:
        path = Path(artifact_dir)
    else:
        path = Path(default_root) / _now_task_id("task")
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def _short(text: str | None, limit: int = 20000) -> str:
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... truncated {len(text) - limit} bytes ..."


def _json_response(
    verdict: str,
    confidence: float,
    summary: str,
    *,
    metrics: dict[str, Any] | None = None,
    artifacts: list[dict[str, str]] | None = None,
    warnings: list[str] | None = None,
    logs: dict[str, str] | None = None,
) -> str:
    if verdict not in PERF_VERDICTS:
        verdict = "ERROR"
        confidence = 0.0
        summary = f"Internal error: invalid performance verdict. Original summary: {summary}"
    payload = {
        "verdict": verdict,
        "confidence": round(float(confidence), 4),
        "summary": summary,
        "metrics": metrics or {},
        "artifacts": artifacts or [],
        "warnings": warnings or [],
        "logs": logs or {"stdout": "", "stderr": ""},
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def _write_json(path: Path, data: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _merged_env(environment: dict[str, Any] | None) -> dict[str, str]:
    env = os.environ.copy()
    for key, value in (environment or {}).items():
        env[str(key)] = str(value)
    return env


def _run_command(
    cmd: list[str],
    *,
    cwd: str | Path | None = None,
    env: dict[str, Any] | None = None,
    timeout_s: int | float = 600,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=_merged_env(env),
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )


def _run_shell_command(
    command: str,
    shell: str,
    *,
    cwd: str | Path | None = None,
    env: dict[str, Any] | None = None,
    timeout_s: int | float = 600,
) -> subprocess.CompletedProcess[str]:
    return _run_command([shell, "-lc", command], cwd=cwd, env=env, timeout_s=timeout_s)


def _host_context() -> dict[str, Any]:
    cpu_model = "unknown"
    try:
        cpuinfo = Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="ignore")
        match = re.search(r"model name\s*:\s*(.+)", cpuinfo)
        if match:
            cpu_model = match.group(1).strip()
    except OSError:
        pass

    governor = "unknown"
    governor_path = Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
    if governor_path.exists():
        governor = governor_path.read_text(encoding="utf-8", errors="ignore").strip() or "unknown"

    load_1 = None
    try:
        load_1 = os.getloadavg()[0]
    except OSError:
        pass

    cpu_count = psutil.cpu_count(logical=True) if psutil else (os.cpu_count() or 0)
    physical_count = psutil.cpu_count(logical=False) if psutil else None
    return {
        "host": {
            "hostname": socket.gethostname(),
            "kernel": platform.release(),
            "cpu_model": cpu_model,
            "num_cores": physical_count or cpu_count,
            "num_threads": cpu_count,
        },
        "runtime_context": {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "governor": governor,
            "cpu_affinity": _format_affinity(),
            "numa_policy": _numa_policy(),
            "thermal_warning": False,
            "load_1m": load_1,
        },
        "software": {
            "python_version": sys.version.split()[0],
            "torch_version": _torch_version(),
            "compiler": shutil.which("cc") or shutil.which("gcc") or "unknown",
            "compiler_version": _compiler_version(),
        },
    }


def _format_affinity() -> str:
    try:
        affinity = os.sched_getaffinity(0)
        return ",".join(str(cpu) for cpu in sorted(affinity))
    except Exception:
        return "unknown"


def _numa_policy() -> str:
    if not shutil.which("numactl"):
        return "unknown"
    try:
        proc = _run_command(["numactl", "--show"], timeout_s=5)
    except Exception:
        return "unknown"
    if proc.returncode != 0:
        return "unknown"
    return _short(proc.stdout.strip(), 1000)


def _torch_version() -> str:
    try:
        import torch

        return str(torch.__version__)
    except Exception:
        return "unavailable"


def _compiler_version() -> str:
    compiler = shutil.which("cc") or shutil.which("gcc")
    if not compiler:
        return "unknown"
    try:
        proc = _run_command([compiler, "--version"], timeout_s=5)
    except Exception:
        return "unknown"
    return proc.stdout.splitlines()[0] if proc.stdout else "unknown"


def _hygiene_warnings(context: dict[str, Any], cases: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    governor = context.get("runtime_context", {}).get("governor")
    if governor not in {"performance", "unknown"}:
        warnings.append(f"CPU frequency governor is '{governor}', not 'performance'.")
    load_1 = context.get("runtime_context", {}).get("load_1m")
    threads = context.get("host", {}).get("num_threads") or 1
    if isinstance(load_1, (int, float)) and load_1 > max(1.0, 0.75 * threads):
        warnings.append(f"System load is high for benchmarking: load_1m={load_1:.2f}.")
    for case in cases:
        env = case.get("environment")
        if isinstance(env, dict) and not any(key.endswith("NUM_THREADS") or key == "OMP_NUM_THREADS" for key in env):
            warnings.append(f"Case {case.get('case_id', 'unknown')} does not pin thread-count environment variables.")
    return warnings


def _cv_pct(mean: float | None, stddev: float | None) -> float | None:
    if not mean or mean <= 0 or stddev is None:
        return None
    return 100.0 * stddev / mean


def _pct_delta(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or a == 0:
        return None
    return 100.0 * (b - a) / a


def _geomean(values: list[float]) -> float | None:
    positives = [v for v in values if v > 0 and math.isfinite(v)]
    if not positives:
        return None
    return math.exp(sum(math.log(v) for v in positives) / len(positives))


def _benchmark_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Benchmark Report", "", payload["summary"], ""]
    lines.append("| Case | Speedup | Mean A (s) | Mean B (s) | Verdict |")
    lines.append("|---|---:|---:|---:|---|")
    for case in payload.get("metrics", {}).get("cases", []):
        lines.append(
            "| {case_id} | {speedup} | {mean_a} | {mean_b} | {verdict} |".format(
                case_id=case.get("case_id"),
                speedup=_fmt(case.get("speedup")),
                mean_a=_fmt(case.get("mean_a_s")),
                mean_b=_fmt(case.get("mean_b_s")),
                verdict=case.get("verdict"),
            )
        )
    return "\n".join(lines) + "\n"


def _fmt(value: Any, digits: int = 4) -> str:
    if value is None:
        return "-"
    if isinstance(value, (int, float)):
        return f"{value:.{digits}g}"
    return str(value)


def _shell_quote(value: Any) -> str:
    text = str(value)
    if re.fullmatch(r"[A-Za-z0-9_./:=,+-]+", text):
        return text
    return "'" + text.replace("'", "'\"'\"'") + "'"


async def run_benchmark_impl(
    benchmark_cases: list[dict[str, Any]],
    mode: str = "differential",
    warmup: int = 3,
    min_runs: int = 10,
    max_runs: int = 100,
    timeout_s: int = 600,
    shell: str = "bash",
    export_json: bool = True,
    prepare_command: str | None = None,
    cleanup_command: str | None = None,
    artifact_dir: str | None = None,
    thresholds: dict[str, Any] | None = None,
) -> str:
    import asyncio

    return await asyncio.to_thread(
        _run_benchmark_sync,
        benchmark_cases,
        mode,
        warmup,
        min_runs,
        max_runs,
        timeout_s,
        shell,
        export_json,
        prepare_command,
        cleanup_command,
        artifact_dir,
        thresholds,
    )


def _run_benchmark_sync(
    benchmark_cases: list[dict[str, Any]],
    mode: str,
    warmup: int,
    min_runs: int,
    max_runs: int,
    timeout_s: int,
    shell: str,
    export_json: bool,
    prepare_command: str | None,
    cleanup_command: str | None,
    artifact_dir: str | None,
    thresholds: dict[str, Any] | None,
) -> str:
    out_dir = _artifact_dir(".perf/benchmarks", artifact_dir)
    context = _host_context()
    warnings = _hygiene_warnings(context, benchmark_cases)
    artifacts: list[dict[str, str]] = []
    stdout_parts: list[str] = []
    stderr_parts: list[str] = []
    if not shutil.which("hyperfine"):
        return _json_response(
            "ERROR",
            0.0,
            "hyperfine is unavailable; install hyperfine or use the MCP Docker image.",
            metrics={"context": context},
            warnings=warnings,
        )

    min_effect_pct = float((thresholds or {}).get("min_effect_size_pct", 3.0))
    max_cv_pct = float((thresholds or {}).get("max_cv_pct", 10.0))
    case_results: list[dict[str, Any]] = []

    for index, case in enumerate(benchmark_cases):
        case_id = str(case.get("case_id") or f"case_{index + 1:03d}")
        case_json = out_dir / f"{case_id}_hyperfine.json"
        commands = _case_commands(case, mode)
        if not commands:
            return _json_response("ERROR", 0.0, f"Case {case_id} is missing benchmark command fields.")
        cmd = [
            "hyperfine",
            "--warmup",
            str(warmup),
            "--min-runs",
            str(min_runs),
            "--max-runs",
            str(max_runs),
            "--shell",
            shell,
        ]
        if prepare_command:
            cmd.extend(["--prepare", prepare_command])
        if cleanup_command:
            cmd.extend(["--cleanup", cleanup_command])
        if export_json:
            cmd.extend(["--export-json", str(case_json)])
        cmd.extend(commands)
        reproduce = " ".join(_shell_quote(part) for part in cmd)
        try:
            proc = _run_command(
                cmd,
                cwd=case.get("working_dir"),
                env=case.get("environment"),
                timeout_s=timeout_s,
            )
        except subprocess.TimeoutExpired as exc:
            return _json_response(
                "ERROR",
                0.0,
                f"Benchmark case {case_id} timed out after {timeout_s}s.",
                metrics={"context": context},
                warnings=warnings,
                logs={"stdout": _short(exc.stdout), "stderr": _short(exc.stderr)},
            )
        stdout_parts.append(proc.stdout)
        stderr_parts.append(proc.stderr)
        if proc.returncode != 0:
            return _json_response(
                "ERROR",
                0.0,
                f"Benchmark case {case_id} failed with exit code {proc.returncode}.",
                metrics={"context": context},
                artifacts=artifacts,
                warnings=warnings,
                logs={"stdout": _short("\n".join(stdout_parts)), "stderr": _short("\n".join(stderr_parts))},
            )
        if case_json.exists():
            artifacts.append({"kind": "hyperfine_json", "path": str(case_json)})
            parsed = _load_json(case_json)
            summarized = _summarize_hyperfine_case(case_id, parsed, mode, min_effect_pct, max_cv_pct)
            summarized["reproduce"] = reproduce
            case_results.append(summarized)

    verdict = _aggregate_case_verdicts(case_results)
    speedups = [c["speedup"] for c in case_results if c.get("speedup")]
    geomean_speedup = _geomean(speedups)
    confidence = _benchmark_confidence(case_results)
    summary = _benchmark_summary(verdict, case_results, geomean_speedup)
    metrics = {
        "cases": case_results,
        "geomean_speedup": geomean_speedup,
        "regression_count": sum(1 for c in case_results if c.get("verdict") == "REGRESSION"),
        "improvement_count": sum(1 for c in case_results if c.get("verdict") == "IMPROVEMENT"),
        "neutral_count": sum(1 for c in case_results if c.get("verdict") == "NEUTRAL"),
        "context": context,
    }
    payload = json.loads(
        _json_response(
            verdict,
            confidence,
            summary,
            metrics=metrics,
            artifacts=artifacts,
            warnings=warnings,
            logs={"stdout": _short("\n".join(stdout_parts)), "stderr": _short("\n".join(stderr_parts))},
        )
    )
    result_path = _write_json(out_dir / "result.json", payload)
    report_path = _write_text(out_dir / "report.md", _benchmark_markdown(payload))
    payload["artifacts"].extend(
        [
            {"kind": "benchmark_result_json", "path": str(result_path)},
            {"kind": "benchmark_report", "path": str(report_path)},
        ]
    )
    _write_json(result_path, payload)
    return json.dumps(payload, indent=2, sort_keys=True)


def _case_commands(case: dict[str, Any], mode: str) -> list[str]:
    normalized = mode.lower().strip()
    if normalized == "single":
        command = case.get("command") or case.get("command_a")
        return [command] if command else []
    return [case.get("command_a"), case.get("command_b")] if case.get("command_a") and case.get("command_b") else []


def _summarize_hyperfine_case(
    case_id: str,
    parsed: dict[str, Any],
    mode: str,
    min_effect_pct: float,
    max_cv_pct: float,
) -> dict[str, Any]:
    results = parsed.get("results", [])
    if mode.lower().strip() == "single":
        first = results[0] if results else {}
        mean = first.get("mean")
        stddev = first.get("stddev")
        cv = _cv_pct(mean, stddev)
        verdict = "UNSURE" if cv is not None and cv > max_cv_pct else "PASS"
        return {
            "case_id": case_id,
            "command": first.get("command"),
            "mean_s": mean,
            "median_s": first.get("median"),
            "stddev_s": stddev,
            "min_s": first.get("min"),
            "max_s": first.get("max"),
            "runs": len(first.get("times", [])),
            "cv_pct": cv,
            "verdict": verdict,
        }

    a = results[0] if len(results) >= 1 else {}
    b = results[1] if len(results) >= 2 else {}
    mean_a = a.get("mean")
    mean_b = b.get("mean")
    speedup = mean_a / mean_b if mean_a and mean_b else None
    rel_change = _pct_delta(mean_a, mean_b)
    cv_a = _cv_pct(mean_a, a.get("stddev"))
    cv_b = _cv_pct(mean_b, b.get("stddev"))
    noisy = any(cv is not None and cv > max_cv_pct for cv in [cv_a, cv_b])
    if noisy:
        verdict = "UNSURE"
    elif rel_change is None:
        verdict = "UNSURE"
    elif rel_change <= -min_effect_pct:
        verdict = "IMPROVEMENT"
    elif rel_change >= min_effect_pct:
        verdict = "REGRESSION"
    else:
        verdict = "NEUTRAL"
    return {
        "case_id": case_id,
        "command_a": a.get("command"),
        "command_b": b.get("command"),
        "mean_a_s": mean_a,
        "mean_b_s": mean_b,
        "median_a_s": a.get("median"),
        "median_b_s": b.get("median"),
        "stddev_a_s": a.get("stddev"),
        "stddev_b_s": b.get("stddev"),
        "min_a_s": a.get("min"),
        "min_b_s": b.get("min"),
        "max_a_s": a.get("max"),
        "max_b_s": b.get("max"),
        "runs_a": len(a.get("times", [])),
        "runs_b": len(b.get("times", [])),
        "cv_a_pct": cv_a,
        "cv_b_pct": cv_b,
        "speedup": speedup,
        "relative_change_pct": rel_change,
        "verdict": verdict,
    }


def _aggregate_case_verdicts(cases: list[dict[str, Any]]) -> str:
    verdicts = [case.get("verdict") for case in cases]
    if not verdicts:
        return "ERROR"
    if any(v == "UNSURE" for v in verdicts):
        return "UNSURE"
    if any(v == "REGRESSION" for v in verdicts):
        return "REGRESSION"
    if any(v == "IMPROVEMENT" for v in verdicts):
        return "IMPROVEMENT"
    if all(v == "PASS" for v in verdicts):
        return "PASS"
    return "NEUTRAL"


def _benchmark_confidence(cases: list[dict[str, Any]]) -> float:
    if not cases:
        return 0.0
    cvs = []
    for case in cases:
        for key in ("cv_pct", "cv_a_pct", "cv_b_pct"):
            if case.get(key) is not None:
                cvs.append(float(case[key]))
    if not cvs:
        return 0.6
    max_cv = max(cvs)
    return max(0.35, min(0.95, 0.95 - max(0.0, max_cv - 2.0) / 25.0))


def _benchmark_summary(verdict: str, cases: list[dict[str, Any]], geomean_speedup: float | None) -> str:
    if not cases:
        return "No benchmark cases were measured."
    if geomean_speedup:
        return f"{verdict}: candidate geomean speedup is {geomean_speedup:.3g}x across {len(cases)} case(s)."
    return f"{verdict}: measured {len(cases)} single-target benchmark case(s)."


async def collect_perf_stats_impl(
    cases: list[dict[str, Any]],
    mode: str = "differential",
    events: list[str] | None = None,
    repeat: int = 5,
    timeout_s: int = 600,
    artifact_dir: str | None = None,
    use_json_output_if_available: bool = True,
    shell: str = "bash",
) -> str:
    import asyncio

    return await asyncio.to_thread(
        _collect_perf_stats_sync,
        cases,
        mode,
        events,
        repeat,
        timeout_s,
        artifact_dir,
        use_json_output_if_available,
        shell,
    )


def _collect_perf_stats_sync(
    cases: list[dict[str, Any]],
    mode: str,
    events: list[str] | None,
    repeat: int,
    timeout_s: int,
    artifact_dir: str | None,
    use_json_output_if_available: bool,
    shell: str,
) -> str:
    del use_json_output_if_available
    out_dir = _artifact_dir(".perf/perf_stats", artifact_dir)
    context = _host_context()
    warnings = _hygiene_warnings(context, cases)
    if not shutil.which("perf"):
        return _json_response("ERROR", 0.0, "perf is unavailable in this environment.", metrics={"context": context})
    events = events or DEFAULT_PERF_EVENTS
    artifacts: list[dict[str, str]] = []
    stdout_parts: list[str] = []
    stderr_parts: list[str] = []
    metrics_cases: list[dict[str, Any]] = []
    all_unavailable: set[str] = set()

    for index, case in enumerate(cases):
        case_id = str(case.get("case_id") or f"case_{index + 1:03d}")
        targets = _perf_targets(case, mode)
        if not targets:
            return _json_response("ERROR", 0.0, f"Case {case_id} is missing perf command fields.")
        case_metric: dict[str, Any] = {"case_id": case_id}
        for suffix, command in targets:
            raw_path = out_dir / f"{case_id}_{suffix}.csv"
            events_to_use = list(events)
            proc = _perf_stat_command(
                command,
                events_to_use,
                repeat,
                raw_path,
                shell,
                cwd=case.get("working_dir"),
                env=case.get("environment"),
                timeout_s=timeout_s,
            )
            if proc.returncode != 0 and _is_perf_eperm(proc.stderr or ""):
                hardware_in_use = bool(set(events_to_use) - set(SOFTWARE_ONLY_PERF_EVENTS))
                if hardware_in_use:
                    events_to_use = list(SOFTWARE_ONLY_PERF_EVENTS)
                    warnings.append(
                        f"{case_id}_{suffix}: PMU access denied; retrying with software-only events."
                    )
                    proc = _perf_stat_command(
                        command,
                        events_to_use,
                        repeat,
                        raw_path,
                        shell,
                        cwd=case.get("working_dir"),
                        env=case.get("environment"),
                        timeout_s=timeout_s,
                    )
            reproduce = _perf_stat_reproduce(command, events_to_use, repeat, raw_path, shell)
            stdout_parts.append(proc.stdout)
            stderr_parts.append(proc.stderr)
            artifacts.append({"kind": "perf_stat_raw", "path": str(raw_path)})
            if proc.returncode != 0:
                eperm = _is_perf_eperm(proc.stderr or "")
                verdict = "UNSURE" if eperm else "ERROR"
                summary = (
                    f"perf stat denied PMU access for case {case_id}_{suffix}; "
                    f"no usable counters available in this environment."
                    if eperm
                    else f"perf stat failed for case {case_id}_{suffix} with exit code {proc.returncode}."
                )
                return _json_response(
                    verdict,
                    0.0,
                    summary,
                    metrics={"context": context},
                    artifacts=artifacts,
                    warnings=warnings,
                    logs={"stdout": _short("\n".join(stdout_parts)), "stderr": _short("\n".join(stderr_parts))},
                )
            parsed, unavailable = _parse_perf_stat_csv(raw_path)
            all_unavailable.update(unavailable)
            case_metric[suffix] = _derive_counter_metrics(parsed, case.get("metadata") or {})
            case_metric.setdefault("reproduce", {})[suffix] = reproduce
        if mode.lower().strip() == "differential" and "a" in case_metric and "b" in case_metric:
            case_metric["delta"] = _counter_delta(case_metric["a"], case_metric["b"])
        metrics_cases.append(case_metric)

    if all_unavailable:
        warnings.append("Some requested perf events were unavailable: " + ", ".join(sorted(all_unavailable)))
    confidence = 0.88 if not all_unavailable else max(0.45, 0.88 - len(all_unavailable) / max(1, len(events)))
    summary = _perf_stats_summary(metrics_cases)
    metrics = {"cases": metrics_cases, "context": context}
    payload = json.loads(
        _json_response(
            "PASS" if confidence >= 0.6 else "UNSURE",
            confidence,
            summary,
            metrics=metrics,
            artifacts=artifacts,
            warnings=warnings,
            logs={"stdout": _short("\n".join(stdout_parts)), "stderr": _short("\n".join(stderr_parts))},
        )
    )
    result_path = _write_json(out_dir / "result.json", payload)
    report_path = _write_text(out_dir / "report.md", _perf_stats_markdown(payload))
    payload["artifacts"].extend(
        [
            {"kind": "perf_stats_result_json", "path": str(result_path)},
            {"kind": "perf_stats_report", "path": str(report_path)},
        ]
    )
    _write_json(result_path, payload)
    return json.dumps(payload, indent=2, sort_keys=True)


def _perf_targets(case: dict[str, Any], mode: str) -> list[tuple[str, str]]:
    if mode.lower().strip() == "single":
        command = case.get("command") or case.get("command_a")
        return [("single", command)] if command else []
    if not case.get("command_a") or not case.get("command_b"):
        return []
    return [("a", case["command_a"]), ("b", case["command_b"])]


def _perf_stat_command(
    command: str,
    events: list[str],
    repeat: int,
    output_path: Path,
    shell: str,
    *,
    cwd: str | Path | None,
    env: dict[str, Any] | None,
    timeout_s: int,
) -> subprocess.CompletedProcess[str]:
    cmd = [
        "perf",
        "stat",
        "-r",
        str(repeat),
        "-e",
        ",".join(events),
        "-x",
        ",",
        "-o",
        str(output_path),
        "--",
        shell,
        "-lc",
        command,
    ]
    return _run_command(cmd, cwd=cwd, env=env, timeout_s=timeout_s)


def _perf_stat_reproduce(command: str, events: list[str], repeat: int, output_path: Path, shell: str) -> str:
    cmd = [
        "perf",
        "stat",
        "-r",
        str(repeat),
        "-e",
        ",".join(events),
        "-x",
        ",",
        "-o",
        str(output_path),
        "--",
        shell,
        "-lc",
        command,
    ]
    return " ".join(_shell_quote(part) for part in cmd)


def _parse_perf_stat_csv(path: Path) -> tuple[dict[str, float], set[str]]:
    metrics: dict[str, list[float]] = {}
    unavailable: set[str] = set()
    if not path.exists():
        return {}, unavailable
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 3:
            continue
        value_raw = parts[0]
        event = parts[2] or (parts[1] if len(parts) > 1 else "")
        event = _normalize_event_name(event)
        if not event:
            continue
        lowered_value = value_raw.lower()
        if "not supported" in lowered_value or "not counted" in lowered_value:
            unavailable.add(event)
            continue
        try:
            value = float(value_raw.replace(",", ""))
        except ValueError:
            continue
        metrics.setdefault(event, []).append(value)
    return {event: statistics.fmean(values) for event, values in metrics.items() if values}, unavailable


def _normalize_event_name(event: str) -> str:
    event = event.strip().strip('"')
    event = event.replace("-", "_").replace(":", "_").replace(".", "_")
    event = re.sub(r"[^A-Za-z0-9_]+", "_", event)
    return event.strip("_")


def _derive_counter_metrics(raw: dict[str, float], metadata: dict[str, Any]) -> dict[str, Any]:
    metrics = dict(raw)
    cycles = raw.get("cycles")
    instructions = raw.get("instructions")
    branches = raw.get("branches")
    branch_misses = raw.get("branch_misses")
    cache_refs = raw.get("cache_references")
    cache_misses = raw.get("cache_misses")
    if cycles and instructions:
        metrics["ipc"] = instructions / cycles
    if branches and branch_misses is not None:
        metrics["branch_miss_rate"] = branch_misses / branches
    if cache_refs and cache_misses is not None:
        metrics["cache_miss_rate"] = cache_misses / cache_refs
    problem_size = metadata.get("problem_size")
    if problem_size:
        if cycles:
            metrics["cycles_per_input_element"] = cycles / float(problem_size)
        if instructions:
            metrics["instructions_per_input_element"] = instructions / float(problem_size)
    return metrics


def _counter_delta(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "cycles",
        "instructions",
        "ipc",
        "branch_miss_rate",
        "cache_miss_rate",
        "cycles_per_input_element",
        "instructions_per_input_element",
    ]
    return {f"{key}_pct": _pct_delta(a.get(key), b.get(key)) for key in keys if _pct_delta(a.get(key), b.get(key)) is not None}


def _perf_stats_summary(cases: list[dict[str, Any]]) -> str:
    if not cases:
        return "No perf stat cases were collected."
    deltas = [case.get("delta", {}).get("cycles_pct") for case in cases]
    deltas = [delta for delta in deltas if delta is not None]
    if deltas:
        return f"Collected perf counters for {len(cases)} case(s); average cycles delta is {statistics.fmean(deltas):.3g}%."
    return f"Collected perf counters for {len(cases)} case(s)."


def _perf_stats_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Perf Stat Report", "", payload["summary"], ""]
    lines.append("| Case | Cycles Delta % | Instructions Delta % | IPC Delta % |")
    lines.append("|---|---:|---:|---:|")
    for case in payload.get("metrics", {}).get("cases", []):
        delta = case.get("delta", {})
        lines.append(
            f"| {case.get('case_id')} | {_fmt(delta.get('cycles_pct'))} | "
            f"{_fmt(delta.get('instructions_pct'))} | {_fmt(delta.get('ipc_pct'))} |"
        )
    return "\n".join(lines) + "\n"


async def profile_hotspots_impl(
    cases: list[dict[str, Any]],
    mode: str = "differential",
    callgraph: bool = True,
    frequency: int = 999,
    timeout_s: int = 600,
    generate_flamegraph: bool = False,
    artifact_dir: str | None = None,
    shell: str = "bash",
) -> str:
    import asyncio

    return await asyncio.to_thread(
        _profile_hotspots_sync,
        cases,
        mode,
        callgraph,
        frequency,
        timeout_s,
        generate_flamegraph,
        artifact_dir,
        shell,
    )


def _profile_hotspots_sync(
    cases: list[dict[str, Any]],
    mode: str,
    callgraph: bool,
    frequency: int,
    timeout_s: int,
    generate_flamegraph: bool,
    artifact_dir: str | None,
    shell: str,
) -> str:
    out_dir = _artifact_dir(".perf/profiles", artifact_dir)
    context = _host_context()
    warnings = _hygiene_warnings(context, cases)
    if not shutil.which("perf"):
        return _json_response("ERROR", 0.0, "perf is unavailable in this environment.", metrics={"context": context})
    artifacts: list[dict[str, str]] = []
    stdout_parts: list[str] = []
    stderr_parts: list[str] = []
    metrics_cases: list[dict[str, Any]] = []

    for index, case in enumerate(cases):
        case_id = str(case.get("case_id") or f"case_{index + 1:03d}")
        case_metric: dict[str, Any] = {"case_id": case_id}
        for suffix, command in _perf_targets(case, mode):
            data_path = out_dir / f"{case_id}_{suffix}.perf.data"
            report_path = out_dir / f"{case_id}_{suffix}.report.txt"
            script_path = out_dir / f"{case_id}_{suffix}.perf.script"
            cmd = ["perf", "record", "-F", str(frequency), "-o", str(data_path)]
            if callgraph:
                cmd.append("-g")
            cmd.extend(["--", shell, "-lc", command])
            proc = _run_command(cmd, cwd=case.get("working_dir"), env=case.get("environment"), timeout_s=timeout_s)
            stdout_parts.append(proc.stdout)
            stderr_parts.append(proc.stderr)
            artifacts.append({"kind": "perf_data", "path": str(data_path)})
            if proc.returncode != 0:
                eperm = _is_perf_eperm(proc.stderr or "")
                verdict = "UNSURE" if eperm else "ERROR"
                summary = (
                    f"perf record denied PMU access for case {case_id}_{suffix}; "
                    f"hotspot profiling unavailable in this environment."
                    if eperm
                    else f"perf record failed for case {case_id}_{suffix} with exit code {proc.returncode}."
                )
                return _json_response(
                    verdict,
                    0.0,
                    summary,
                    metrics={"context": context},
                    artifacts=artifacts,
                    warnings=warnings,
                    logs={"stdout": _short("\n".join(stdout_parts)), "stderr": _short("\n".join(stderr_parts))},
                )
            report_proc = _run_command(["perf", "report", "--stdio", "-i", str(data_path)], timeout_s=timeout_s)
            script_proc = _run_command(["perf", "script", "-i", str(data_path)], timeout_s=timeout_s)
            _write_text(report_path, report_proc.stdout + report_proc.stderr)
            _write_text(script_path, script_proc.stdout + script_proc.stderr)
            artifacts.extend(
                [
                    {"kind": "perf_report", "path": str(report_path)},
                    {"kind": "perf_script", "path": str(script_path)},
                ]
            )
            top_functions = _parse_perf_report(report_path)
            case_metric[f"top_functions_{suffix}"] = top_functions
            if generate_flamegraph:
                flame = _try_flamegraph(script_path, out_dir / f"{case_id}_{suffix}.flame.svg")
                if flame:
                    artifacts.append({"kind": "flamegraph_svg", "path": str(flame)})
                else:
                    warnings.append("FlameGraph tools were unavailable; skipped SVG generation.")
        if mode.lower().strip() == "differential":
            case_metric["hotspot_shift"] = _hotspot_shift(
                case_metric.get("top_functions_a", []),
                case_metric.get("top_functions_b", []),
            )
        metrics_cases.append(case_metric)

    summary = _hotspot_summary(metrics_cases)
    payload = json.loads(
        _json_response(
            "PASS",
            0.82,
            summary,
            metrics={"cases": metrics_cases, "context": context},
            artifacts=artifacts,
            warnings=warnings,
            logs={"stdout": _short("\n".join(stdout_parts)), "stderr": _short("\n".join(stderr_parts))},
        )
    )
    result_path = _write_json(out_dir / "result.json", payload)
    report_path = _write_text(out_dir / "report.md", _hotspot_markdown(payload))
    payload["artifacts"].extend(
        [
            {"kind": "profile_result_json", "path": str(result_path)},
            {"kind": "profile_report", "path": str(report_path)},
        ]
    )
    _write_json(result_path, payload)
    return json.dumps(payload, indent=2, sort_keys=True)


def _parse_perf_report(path: Path, limit: int = 15) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    functions: list[dict[str, Any]] = []
    for line in text.splitlines():
        match = re.match(r"\s*([0-9]+(?:\.[0-9]+)?)%\s+(.+)$", line)
        if not match:
            continue
        percent = float(match.group(1))
        rest = match.group(2).strip()
        symbol_match = re.search(r"\]\s+(.+)$", rest)
        symbol = symbol_match.group(1).strip() if symbol_match else rest.split()[-1]
        symbol = re.sub(r"\s+", " ", symbol)
        if symbol and not symbol.startswith("["):
            functions.append({"symbol": symbol, "percent": percent})
        if len(functions) >= limit:
            break
    return functions


def _hotspot_shift(a: list[dict[str, Any]], b: list[dict[str, Any]]) -> list[dict[str, Any]]:
    a_map = {entry["symbol"]: float(entry["percent"]) for entry in a}
    b_map = {entry["symbol"]: float(entry["percent"]) for entry in b}
    shifts: list[dict[str, Any]] = []
    for symbol, b_pct in sorted(b_map.items(), key=lambda item: item[1], reverse=True):
        delta = b_pct - a_map.get(symbol, 0.0)
        if abs(delta) < 5.0 and not _is_special_hotspot(symbol):
            continue
        interpretation = "new overhead in candidate" if symbol not in a_map else "large percentage shift"
        if _is_special_hotspot(symbol):
            interpretation = "candidate contains allocation/copy/dispatch overhead"
        shifts.append({"symbol": symbol, "delta_percent": delta, "interpretation": interpretation})
    return shifts[:10]


def _is_special_hotspot(symbol: str) -> bool:
    lowered = symbol.lower()
    return any(pattern.lower() in lowered for pattern in SPECIAL_HOTSPOT_PATTERNS)


def _try_flamegraph(script_path: Path, output_path: Path) -> Path | None:
    stackcollapse = shutil.which("stackcollapse-perf.pl")
    flamegraph = shutil.which("flamegraph.pl")
    if not stackcollapse or not flamegraph:
        return None
    collapsed = subprocess.run([stackcollapse, str(script_path)], capture_output=True, text=True, check=False)
    if collapsed.returncode != 0:
        return None
    svg = subprocess.run([flamegraph], input=collapsed.stdout, capture_output=True, text=True, check=False)
    if svg.returncode != 0:
        return None
    _write_text(output_path, svg.stdout)
    return output_path


def _hotspot_summary(cases: list[dict[str, Any]]) -> str:
    shifts = sum(len(case.get("hotspot_shift", [])) for case in cases)
    if shifts:
        return f"Collected hotspot profiles for {len(cases)} case(s); detected {shifts} notable hotspot shift(s)."
    return f"Collected hotspot profiles for {len(cases)} case(s)."


def _hotspot_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Hotspot Profile Report", "", payload["summary"], ""]
    for case in payload.get("metrics", {}).get("cases", []):
        lines.append(f"## {case.get('case_id')}")
        shifts = case.get("hotspot_shift", [])
        if shifts:
            for shift in shifts[:8]:
                lines.append(f"- {shift['symbol']}: {shift['delta_percent']:.3g}% ({shift['interpretation']})")
        else:
            lines.append("- No notable hotspot shift detected.")
    return "\n".join(lines) + "\n"


async def compare_performance_impl(
    benchmark_result_path: str | None = None,
    perf_stats_result_path: str | None = None,
    profile_result_path: str | None = None,
    policy: dict[str, Any] | None = None,
    artifact_dir: str | None = None,
) -> str:
    import asyncio

    return await asyncio.to_thread(
        _compare_performance_sync,
        benchmark_result_path,
        perf_stats_result_path,
        profile_result_path,
        policy,
        artifact_dir,
    )


def _compare_performance_sync(
    benchmark_result_path: str | None,
    perf_stats_result_path: str | None,
    profile_result_path: str | None,
    policy: dict[str, Any] | None,
    artifact_dir: str | None,
) -> str:
    out_dir = _artifact_dir(".perf/reports", artifact_dir)
    warnings: list[str] = []
    benchmark = _load_optional_result(benchmark_result_path, warnings, "benchmark")
    perf_stats = _load_optional_result(perf_stats_result_path, warnings, "perf stats")
    profile = _load_optional_result(profile_result_path, warnings, "profile")
    if not benchmark:
        return _json_response("ERROR", 0.0, "compare_performance requires a benchmark_result_path.")

    min_speedup = float((policy or {}).get("min_speedup_for_improvement", 1.03))
    max_slowdown_for_neutral = float((policy or {}).get("max_slowdown_for_neutral", 1.03))
    cases: list[dict[str, Any]] = []
    counts = {"IMPROVEMENT": 0, "REGRESSION": 0, "NEUTRAL": 0, "UNSURE": 0}
    stat_cases = {case.get("case_id"): case for case in (perf_stats or {}).get("metrics", {}).get("cases", [])}
    for bcase in benchmark.get("metrics", {}).get("cases", []):
        case_id = bcase.get("case_id")
        speedup = bcase.get("speedup")
        verdict = "UNSURE"
        if speedup:
            if speedup >= min_speedup:
                verdict = "IMPROVEMENT"
            elif speedup <= 1.0 / max_slowdown_for_neutral:
                verdict = "REGRESSION"
            else:
                verdict = "NEUTRAL"
        stat_delta = stat_cases.get(case_id, {}).get("delta", {})
        record = {
            "case_id": case_id,
            "runtime_speedup": speedup,
            "runtime_delta_pct": bcase.get("relative_change_pct"),
            "cycles_delta_pct": stat_delta.get("cycles_pct"),
            "instructions_delta_pct": stat_delta.get("instructions_pct"),
            "ipc_delta_pct": stat_delta.get("ipc_pct"),
            "cache_miss_rate_delta_pct": stat_delta.get("cache_miss_rate_pct"),
            "branch_miss_rate_delta_pct": stat_delta.get("branch_miss_rate_pct"),
            "verdict": verdict,
        }
        counts[verdict] += 1
        cases.append(record)

    top_verdict = _aggregate_case_verdicts(cases)
    geomean_speedup = benchmark.get("metrics", {}).get("geomean_speedup")
    confidence = min(float(benchmark.get("confidence", 0.6)), float((perf_stats or {}).get("confidence", 0.95)))
    if profile and profile.get("verdict") == "PASS":
        confidence = min(0.95, confidence + 0.03)
    summary = _compare_performance_summary(top_verdict, geomean_speedup, perf_stats)
    metrics = {
        "geomean_speedup": geomean_speedup,
        "cases": cases,
        "regression_count": counts["REGRESSION"],
        "improvement_count": counts["IMPROVEMENT"],
        "neutral_count": counts["NEUTRAL"],
        "unsure_count": counts["UNSURE"],
        "benchmark": _compact_status(benchmark),
        "perf_stats": _compact_status(perf_stats),
        "hotspots": _compact_status(profile),
    }
    payload = json.loads(_json_response(top_verdict, confidence, summary, metrics=metrics, warnings=warnings))
    json_path = _write_json(out_dir / "performance_report.json", payload)
    md_path = _write_text(out_dir / "performance_report.md", _compare_performance_markdown(payload))
    payload["artifacts"].extend(
        [
            {"kind": "performance_report_json", "path": str(json_path)},
            {"kind": "performance_report_md", "path": str(md_path)},
        ]
    )
    _write_json(json_path, payload)
    return json.dumps(payload, indent=2, sort_keys=True)


def _load_optional_result(path: str | None, warnings: list[str], label: str) -> dict[str, Any] | None:
    if not path:
        return None
    try:
        return _load_json(path)
    except Exception as exc:
        warnings.append(f"Could not load {label} result at {path}: {exc}")
        return None


def _compact_status(result: dict[str, Any] | None) -> dict[str, Any] | None:
    if not result:
        return None
    return {
        "verdict": result.get("verdict"),
        "confidence": result.get("confidence"),
        "summary": result.get("summary"),
    }


def _compare_performance_summary(verdict: str, geomean_speedup: float | None, perf_stats: dict[str, Any] | None) -> str:
    counter_hint = ""
    if perf_stats:
        deltas = [
            case.get("delta", {}).get("cycles_pct")
            for case in perf_stats.get("metrics", {}).get("cases", [])
            if case.get("delta", {}).get("cycles_pct") is not None
        ]
        if deltas:
            counter_hint = f"; average cycles delta {statistics.fmean(deltas):.3g}%"
    if geomean_speedup:
        return f"{verdict}: candidate geomean runtime speedup is {geomean_speedup:.3g}x{counter_hint}."
    return f"{verdict}: benchmark evidence was insufficient for a runtime speedup."


def _compare_performance_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Performance Comparison", "", payload["summary"], ""]
    lines.append("| Case | Runtime Speedup | Cycles Delta % | IPC Delta % | Verdict |")
    lines.append("|---|---:|---:|---:|---|")
    for case in payload.get("metrics", {}).get("cases", []):
        lines.append(
            f"| {case.get('case_id')} | {_fmt(case.get('runtime_speedup'))} | "
            f"{_fmt(case.get('cycles_delta_pct'))} | {_fmt(case.get('ipc_delta_pct'))} | {case.get('verdict')} |"
        )
    return "\n".join(lines) + "\n"


async def collect_hardware_model_impl(
    device_selector: dict[str, Any] | None = None,
    precision_modes: list[str] | None = None,
    bandwidth_levels: list[str] | None = None,
    manual_overrides: dict[str, Any] | None = None,
    artifact_dir: str | None = None,
) -> str:
    import asyncio

    return await asyncio.to_thread(
        _collect_hardware_model_sync,
        device_selector,
        precision_modes,
        bandwidth_levels,
        manual_overrides,
        artifact_dir,
    )


def _collect_hardware_model_sync(
    device_selector: dict[str, Any] | None,
    precision_modes: list[str] | None,
    bandwidth_levels: list[str] | None,
    manual_overrides: dict[str, Any] | None,
    artifact_dir: str | None,
) -> str:
    out_dir = _artifact_dir(".perf/hardware", artifact_dir)
    context = _host_context()
    precision_modes = precision_modes or ["fp32", "fp64"]
    bandwidth_levels = bandwidth_levels or ["dram"]
    manual_overrides = manual_overrides or {}
    selector_type = (device_selector or {}).get("type", "auto")
    device_type = "CPU" if selector_type in {"auto", "CPU", None} else str(selector_type)
    cpu_name = context["host"]["cpu_model"]
    peak_flops = {mode: None for mode in precision_modes}
    peak_flops.update(manual_overrides.get("peak_flops") or {})
    peak_bandwidth = {level: None for level in bandwidth_levels}
    peak_bandwidth.update(manual_overrides.get("peak_bandwidth_Bps") or {})
    model = {
        "device_id": (device_selector or {}).get("id") or ("cpu_0" if device_type == "CPU" else "device_0"),
        "device_type": device_type,
        "name": cpu_name,
        "peak_flops": peak_flops,
        "peak_bandwidth_Bps": peak_bandwidth,
        "memory_hierarchy": _memory_hierarchy(),
        "metadata": {"context": context, "manual_overrides": manual_overrides},
    }
    warnings = []
    if any(value is None for value in peak_flops.values()):
        warnings.append("Some peak FLOP/s values are unknown; provide manual_overrides for roofline analysis.")
    if any(value is None for value in peak_bandwidth.values()):
        warnings.append("Some peak bandwidth values are unknown; provide manual_overrides for roofline analysis.")
    path = _write_json(out_dir / "hardware_model.json", model)
    confidence = 0.8 if not warnings else 0.55
    return _json_response(
        "PASS",
        confidence,
        f"Collected {device_type} hardware model for {model['name']}.",
        metrics={"hardware_model": model},
        artifacts=[{"kind": "hardware_model_json", "path": str(path)}],
        warnings=warnings,
    )


def _memory_hierarchy() -> list[dict[str, Any]]:
    hierarchy: list[dict[str, Any]] = []
    cache_root = Path("/sys/devices/system/cpu/cpu0/cache")
    if cache_root.exists():
        for index_dir in sorted(cache_root.glob("index*")):
            try:
                level = (index_dir / "level").read_text(encoding="utf-8").strip()
                size = (index_dir / "size").read_text(encoding="utf-8").strip()
                hierarchy.append({"level": f"L{level}", "bandwidth_Bps": None, "capacity_bytes": _parse_size_to_bytes(size)})
            except OSError:
                continue
    hierarchy.append({"level": "DRAM", "bandwidth_Bps": None, "capacity_bytes": None})
    return hierarchy


def _parse_size_to_bytes(size: str) -> int | None:
    match = re.match(r"([0-9]+)\s*([KMG])?", size.strip(), re.IGNORECASE)
    if not match:
        return None
    value = int(match.group(1))
    unit = (match.group(2) or "").upper()
    multiplier = {"K": 1024, "M": 1024**2, "G": 1024**3}.get(unit, 1)
    return value * multiplier


async def estimate_workload_model_impl(
    benchmark_cases: list[dict[str, Any]],
    source_a: str | None = None,
    source_b: str | None = None,
    estimation_mode: str = "formula",
    artifact_dir: str | None = None,
) -> str:
    import asyncio

    return await asyncio.to_thread(
        _estimate_workload_model_sync,
        benchmark_cases,
        source_a,
        source_b,
        estimation_mode,
        artifact_dir,
    )


def _estimate_workload_model_sync(
    benchmark_cases: list[dict[str, Any]],
    source_a: str | None,
    source_b: str | None,
    estimation_mode: str,
    artifact_dir: str | None,
) -> str:
    if artifact_dir:
        out_dir = _artifact_dir(".perf/roofline", artifact_dir)
    else:
        out_dir = (Path(".perf/roofline") / _now_task_id("task") / "workload_model").resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
    warnings = ["Memory traffic estimates are lower bounds unless manually measured."]
    cases: list[dict[str, Any]] = []
    unsure = 0
    for index, case in enumerate(benchmark_cases):
        case_id = str(case.get("case_id") or f"case_{index + 1:03d}")
        try:
            estimated = _estimate_case_workload(case, estimation_mode)
        except ValueError as exc:
            unsure += 1
            warnings.append(f"{case_id}: {exc}")
            estimated = {
                "case_id": case_id,
                "operation": case.get("operation", "unknown"),
                "flops": None,
                "bytes_moved": None,
                "arithmetic_intensity": None,
                "flops_source": "unknown",
                "bytes_source": "unknown",
            }
        estimated["case_id"] = case_id
        cases.append(estimated)
    model = {"source_a": source_a, "source_b": source_b, "estimation_mode": estimation_mode, "cases": cases}
    path = _write_json(out_dir / "model.json", model)
    verdict = "UNSURE" if unsure else "PASS"
    confidence = max(0.35, 0.75 - 0.15 * unsure)
    return _json_response(
        verdict,
        confidence,
        f"Estimated workload model for {len(cases)} case(s).",
        metrics={"cases": cases},
        artifacts=[{"kind": "workload_model_json", "path": str(path)}],
        warnings=warnings,
    )


def _estimate_case_workload(case: dict[str, Any], estimation_mode: str) -> dict[str, Any]:
    metadata = case.get("metadata") or {}
    dtype_size = _dtype_size(metadata.get("dtype", case.get("dtype", "float32")))
    manual_flops = case.get("manual_flops") or metadata.get("manual_flops")
    manual_bytes = case.get("manual_bytes") or metadata.get("manual_bytes")
    operation = str(case.get("operation") or metadata.get("operation") or "unknown").lower()
    if manual_flops is not None and manual_bytes is not None:
        flops = float(manual_flops)
        bytes_moved = float(manual_bytes)
        return _workload_record(operation, flops, bytes_moved, "manual", "manual")
    if estimation_mode == "manual":
        raise ValueError("manual estimation requested but manual_flops/manual_bytes were not both provided")
    if operation == "matmul":
        m = _metadata_number(metadata, "m")
        n = _metadata_number(metadata, "n")
        k = _metadata_number(metadata, "k")
        if not all([m, n, k]):
            shape = metadata.get("shape")
            if isinstance(shape, list) and len(shape) >= 3:
                m, n, k = shape[:3]
        if not all([m, n, k]):
            raise ValueError("matmul requires m, n, and k metadata")
        flops = 2.0 * float(m) * float(n) * float(k)
        bytes_moved = dtype_size * (float(m) * float(k) + float(k) * float(n) + float(m) * float(n))
        return _workload_record(operation, flops, bytes_moved, "formula", "formula_lower_bound")
    if operation in {"elementwise", "elementwise_unary", "unary"}:
        n = _problem_size(metadata)
        flops = n * float(metadata.get("flops_per_element", 1))
        bytes_moved = dtype_size * (2.0 * n)
        return _workload_record(operation, flops, bytes_moved, "formula", "formula_lower_bound")
    if operation in {"elementwise_binary", "binary"}:
        n = _problem_size(metadata)
        flops = n * float(metadata.get("flops_per_element", 1))
        bytes_moved = dtype_size * (3.0 * n)
        return _workload_record(operation, flops, bytes_moved, "formula", "formula_lower_bound")
    if operation == "reduction":
        n = _problem_size(metadata)
        flops = max(0.0, n - 1.0)
        bytes_moved = dtype_size * (n + 1.0)
        return _workload_record(operation, flops, bytes_moved, "formula", "formula_lower_bound")
    if operation == "conv2d":
        n = _metadata_number(metadata, "batch", default=1)
        cout = _metadata_number(metadata, "out_channels")
        cin = _metadata_number(metadata, "in_channels")
        oh = _metadata_number(metadata, "out_h")
        ow = _metadata_number(metadata, "out_w")
        kh = _metadata_number(metadata, "kernel_h")
        kw = _metadata_number(metadata, "kernel_w")
        if not all([cout, cin, oh, ow, kh, kw]):
            raise ValueError("conv2d requires out/in channels, output shape, and kernel shape metadata")
        flops = 2.0 * float(n) * float(cout) * float(oh) * float(ow) * float(cin) * float(kh) * float(kw)
        bytes_moved = dtype_size * (
            float(n) * float(cin) * (float(oh) + float(kh) - 1.0) * (float(ow) + float(kw) - 1.0)
            + float(cout) * float(cin) * float(kh) * float(kw)
            + float(n) * float(cout) * float(oh) * float(ow)
        )
        return _workload_record(operation, flops, bytes_moved, "formula", "formula_lower_bound")
    if operation in {"stencil", "stencil_like"}:
        n = _problem_size(metadata)
        dimensions = int(metadata.get("dimensions", len(metadata.get("shape", [])) or 1))
        stencil_points = float(metadata.get("stencil_points", 2 * dimensions + 1))
        flops_per_point = float(metadata.get("flops_per_point", max(1.0, stencil_points)))
        flops = n * flops_per_point
        bytes_moved = dtype_size * n * (stencil_points + 1.0)
        return _workload_record(operation, flops, bytes_moved, "formula", "formula_lower_bound")
    raise ValueError(f"unsupported or unknown operation '{operation}'")


def _dtype_size(dtype: Any) -> int:
    lowered = str(dtype).lower()
    if any(token in lowered for token in ["float64", "double", "int64"]):
        return 8
    if any(token in lowered for token in ["float16", "bfloat16", "half", "int16"]):
        return 2
    if "int8" in lowered or "uint8" in lowered or "bool" in lowered:
        return 1
    return 4


def _metadata_number(metadata: dict[str, Any], key: str, default: float | None = None) -> float | None:
    value = metadata.get(key, default)
    return float(value) if value is not None else None


def _problem_size(metadata: dict[str, Any]) -> float:
    if metadata.get("problem_size"):
        return float(metadata["problem_size"])
    shape = metadata.get("shape")
    if isinstance(shape, list) and shape:
        product = 1.0
        for dim in shape:
            product *= float(dim)
        return product
    raise ValueError("problem_size or shape metadata is required")


def _workload_record(operation: str, flops: float, bytes_moved: float, flops_source: str, bytes_source: str) -> dict[str, Any]:
    return {
        "operation": operation,
        "flops": flops,
        "bytes_moved": bytes_moved,
        "arithmetic_intensity": flops / bytes_moved if bytes_moved else None,
        "flops_source": flops_source,
        "bytes_source": bytes_source,
    }


async def run_roofline_analysis_impl(
    benchmark_result_path: str,
    workload_model_path: str,
    hardware_model_path: str,
    precision: str = "fp32",
    memory_level: str = "dram",
    mode: str = "differential",
    artifact_dir: str | None = None,
    policy: dict[str, Any] | None = None,
) -> str:
    import asyncio

    return await asyncio.to_thread(
        _run_roofline_analysis_sync,
        benchmark_result_path,
        workload_model_path,
        hardware_model_path,
        precision,
        memory_level,
        mode,
        artifact_dir,
        policy,
    )


def _run_roofline_analysis_sync(
    benchmark_result_path: str,
    workload_model_path: str,
    hardware_model_path: str,
    precision: str,
    memory_level: str,
    mode: str,
    artifact_dir: str | None,
    policy: dict[str, Any] | None,
) -> str:
    out_dir = _artifact_dir(".perf/roofline", artifact_dir)
    benchmark = _load_json(benchmark_result_path)
    workload = _load_json(workload_model_path)
    hardware_payload = _load_json(hardware_model_path)
    hardware = hardware_payload.get("metrics", {}).get("hardware_model") or hardware_payload
    peak_flops = _as_float((hardware.get("peak_flops") or {}).get(precision))
    peak_bw = _as_float((hardware.get("peak_bandwidth_Bps") or {}).get(memory_level))
    warnings = []
    if not peak_flops or not peak_bw:
        return _json_response(
            "UNSURE",
            0.35,
            "Roofline analysis requires peak FLOP/s and peak bandwidth in the hardware model.",
            warnings=["Provide manual_overrides.peak_flops and manual_overrides.peak_bandwidth_Bps."],
        )
    workload_cases = {case.get("case_id"): case for case in workload.get("cases", workload.get("metrics", {}).get("cases", []))}
    cases: list[dict[str, Any]] = []
    for bcase in benchmark.get("metrics", {}).get("cases", []):
        case_id = bcase.get("case_id")
        wcase = workload_cases.get(case_id)
        if not wcase:
            warnings.append(f"No workload model for benchmark case {case_id}; skipped.")
            continue
        if mode.lower().strip() == "single":
            cases.append({"case_id": case_id, "single": _roofline_point(wcase, bcase.get("mean_s"), peak_flops, peak_bw)})
        else:
            a_point = _roofline_point(wcase, bcase.get("mean_a_s"), peak_flops, peak_bw)
            b_point = _roofline_point(wcase, bcase.get("mean_b_s"), peak_flops, peak_bw)
            cases.append(
                {
                    "case_id": case_id,
                    "a": a_point,
                    "b": b_point,
                    "delta": {
                        "achieved_flops_speedup": _ratio(b_point.get("achieved_flops"), a_point.get("achieved_flops")),
                        "utilization_delta": _sub(b_point.get("utilization"), a_point.get("utilization")),
                        "bound_changed": a_point.get("bound") != b_point.get("bound"),
                    },
                }
            )
    verdict = _roofline_verdict(cases, mode, policy)
    summary = _roofline_summary(verdict, cases)
    payload = json.loads(
        _json_response(
            verdict,
            0.82 if cases else 0.4,
            summary,
            metrics={"cases": cases, "hardware_model": hardware},
            warnings=warnings,
        )
    )
    json_path = _write_json(out_dir / "roofline_report.json", payload)
    md_path = _write_text(out_dir / "roofline_report.md", _roofline_markdown(payload))
    payload["artifacts"].extend(
        [
            {"kind": "roofline_report_json", "path": str(json_path)},
            {"kind": "roofline_report_md", "path": str(md_path)},
        ]
    )
    plot_path = _try_roofline_plot(out_dir / "roofline.png", cases, peak_flops, peak_bw)
    if plot_path:
        payload["artifacts"].append({"kind": "roofline_plot", "path": str(plot_path)})
    else:
        payload["warnings"].append("matplotlib unavailable or plot generation failed; skipped roofline plot.")
    _write_json(json_path, payload)
    return json.dumps(payload, indent=2, sort_keys=True)


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _roofline_point(wcase: dict[str, Any], runtime_s: float | None, peak_flops: float, peak_bw: float) -> dict[str, Any]:
    flops = _as_float(wcase.get("flops"))
    bytes_moved = _as_float(wcase.get("bytes_moved"))
    ai = _as_float(wcase.get("arithmetic_intensity"))
    memory_roof = (ai or 0.0) * peak_bw
    attainable = min(peak_flops, memory_roof) if memory_roof else None
    achieved_flops = flops / runtime_s if flops and runtime_s else None
    achieved_bw = bytes_moved / runtime_s if bytes_moved and runtime_s else None
    return {
        "runtime_s": runtime_s,
        "flops": flops,
        "bytes_moved": bytes_moved,
        "arithmetic_intensity": ai,
        "achieved_flops": achieved_flops,
        "achieved_bandwidth_Bps": achieved_bw,
        "attainable_flops": attainable,
        "utilization": achieved_flops / attainable if achieved_flops and attainable else None,
        "bound": "memory" if memory_roof and memory_roof < peak_flops else "compute",
    }


def _ratio(numerator: float | None, denominator: float | None) -> float | None:
    return numerator / denominator if numerator is not None and denominator else None


def _sub(a: float | None, b: float | None) -> float | None:
    return a - b if a is not None and b is not None else None


def _roofline_verdict(cases: list[dict[str, Any]], mode: str, policy: dict[str, Any] | None) -> str:
    if not cases:
        return "UNSURE"
    if mode.lower().strip() == "single":
        return "PASS"
    min_util_delta = float((policy or {}).get("min_utilization_delta", 0.03))
    min_speedup = float((policy or {}).get("min_achieved_flops_speedup", 1.03))
    verdicts = []
    for case in cases:
        delta = case.get("delta", {})
        util_delta = delta.get("utilization_delta")
        speedup = delta.get("achieved_flops_speedup")
        if util_delta is None or speedup is None:
            verdicts.append("UNSURE")
        elif util_delta >= min_util_delta and speedup >= min_speedup:
            verdicts.append("IMPROVEMENT")
        elif util_delta <= -min_util_delta and speedup <= 1.0 / min_speedup:
            verdicts.append("REGRESSION")
        else:
            verdicts.append("NEUTRAL")
    return _aggregate_case_verdicts([{"verdict": verdict} for verdict in verdicts])


def _roofline_summary(verdict: str, cases: list[dict[str, Any]]) -> str:
    if not cases:
        return "No roofline cases were analyzed."
    speedups = [case.get("delta", {}).get("achieved_flops_speedup") for case in cases]
    speedups = [s for s in speedups if s]
    if speedups:
        return f"{verdict}: average achieved FLOP/s speedup is {statistics.fmean(speedups):.3g}x across {len(speedups)} case(s)."
    return f"{verdict}: roofline analysis completed for {len(cases)} case(s)."


def _roofline_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Roofline Report", "", payload["summary"], ""]
    lines.append("| Case | A Util | B Util | Speedup | Bound A | Bound B |")
    lines.append("|---|---:|---:|---:|---|---|")
    for case in payload.get("metrics", {}).get("cases", []):
        lines.append(
            f"| {case.get('case_id')} | {_fmt(case.get('a', {}).get('utilization'))} | "
            f"{_fmt(case.get('b', {}).get('utilization'))} | "
            f"{_fmt(case.get('delta', {}).get('achieved_flops_speedup'))} | "
            f"{case.get('a', {}).get('bound', '-')} | {case.get('b', {}).get('bound', '-')} |"
        )
    return "\n".join(lines) + "\n"


def _try_roofline_plot(path: Path, cases: list[dict[str, Any]], peak_flops: float, peak_bw: float) -> Path | None:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return None
    points = []
    for case in cases:
        for label in ("a", "b", "single"):
            point = case.get(label)
            if point and point.get("arithmetic_intensity") and point.get("achieved_flops"):
                points.append((case.get("case_id"), label, point["arithmetic_intensity"], point["achieved_flops"]))
    if not points:
        return None
    min_ai = min(p[2] for p in points) / 10.0
    max_ai = max(p[2] for p in points) * 10.0
    xs = [10 ** (math.log10(max(min_ai, 1e-9)) + i * (math.log10(max_ai) - math.log10(max(min_ai, 1e-9))) / 100) for i in range(101)]
    ys = [min(peak_flops, x * peak_bw) for x in xs]
    plt.figure(figsize=(7, 5))
    plt.loglog(xs, ys, label="roofline")
    for case_id, label, ai, achieved in points:
        plt.scatter([ai], [achieved], label=f"{case_id}_{label}")
    plt.xlabel("Arithmetic intensity (FLOP/byte)")
    plt.ylabel("FLOP/s")
    plt.legend(fontsize="small")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return path


async def compare_roofline_impl(
    roofline_result_path: str,
    policy: dict[str, Any] | None = None,
    artifact_dir: str | None = None,
) -> str:
    import asyncio

    return await asyncio.to_thread(_compare_roofline_sync, roofline_result_path, policy, artifact_dir)


def _compare_roofline_sync(
    roofline_result_path: str,
    policy: dict[str, Any] | None,
    artifact_dir: str | None,
) -> str:
    out_dir = _artifact_dir(".perf/roofline/comparison", artifact_dir)
    roofline = _load_json(roofline_result_path)
    min_util_delta = float((policy or {}).get("min_utilization_delta", 0.03))
    min_speedup = float((policy or {}).get("min_achieved_flops_speedup", 1.03))
    cases: list[dict[str, Any]] = []
    counts = {"IMPROVEMENT": 0, "REGRESSION": 0, "NEUTRAL": 0, "UNSURE": 0}
    for case in roofline.get("metrics", {}).get("cases", []):
        a = case.get("a", {})
        b = case.get("b", {})
        delta = case.get("delta", {})
        util_delta = delta.get("utilization_delta")
        speedup = delta.get("achieved_flops_speedup")
        if util_delta is None or speedup is None:
            verdict = "UNSURE"
        elif util_delta >= min_util_delta and speedup >= min_speedup:
            verdict = "IMPROVEMENT"
        elif util_delta <= -min_util_delta and speedup <= 1.0 / min_speedup:
            verdict = "REGRESSION"
        else:
            verdict = "NEUTRAL"
        counts[verdict] += 1
        cases.append(
            {
                "case_id": case.get("case_id"),
                "a_utilization": a.get("utilization"),
                "b_utilization": b.get("utilization"),
                "utilization_delta": util_delta,
                "a_bound": a.get("bound"),
                "b_bound": b.get("bound"),
                "bound_changed": delta.get("bound_changed"),
                "achieved_flops_speedup": speedup,
                "verdict": verdict,
            }
        )
    verdict = _aggregate_case_verdicts(cases)
    summary = _compare_roofline_summary(verdict, cases)
    payload = json.loads(
        _json_response(
            verdict,
            min(0.9, float(roofline.get("confidence", 0.75))),
            summary,
            metrics={
                "cases": cases,
                "improvement_count": counts["IMPROVEMENT"],
                "regression_count": counts["REGRESSION"],
                "neutral_count": counts["NEUTRAL"],
                "unsure_count": counts["UNSURE"],
            },
            warnings=roofline.get("warnings", []),
        )
    )
    json_path = _write_json(out_dir / "report.json", payload)
    md_path = _write_text(out_dir / "report.md", _compare_roofline_markdown(payload))
    payload["artifacts"].extend(
        [
            {"kind": "roofline_comparison_json", "path": str(json_path)},
            {"kind": "roofline_comparison_md", "path": str(md_path)},
        ]
    )
    _write_json(json_path, payload)
    return json.dumps(payload, indent=2, sort_keys=True)


def _compare_roofline_summary(verdict: str, cases: list[dict[str, Any]]) -> str:
    if not cases:
        return "No differential roofline cases were available."
    deltas = [case.get("utilization_delta") for case in cases if case.get("utilization_delta") is not None]
    if deltas:
        return f"{verdict}: average utilization delta is {statistics.fmean(deltas):.3g}."
    return f"{verdict}: roofline comparison completed for {len(cases)} case(s)."


def _compare_roofline_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Roofline Comparison", "", payload["summary"], ""]
    lines.append("| Case | Util Delta | FLOP/s Speedup | Bound Changed | Verdict |")
    lines.append("|---|---:|---:|---|---|")
    for case in payload.get("metrics", {}).get("cases", []):
        lines.append(
            f"| {case.get('case_id')} | {_fmt(case.get('utilization_delta'))} | "
            f"{_fmt(case.get('achieved_flops_speedup'))} | {case.get('bound_changed')} | {case.get('verdict')} |"
        )
    return "\n".join(lines) + "\n"

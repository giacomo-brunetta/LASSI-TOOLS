"""Profiling primitives and performance MCP tool implementations.

Modules:

- :mod:`lassi.profiling.profiler` — ``Profiler``/``MultiProfiler``, timers,
  CPU/GPU/ARM/NVIDIA power probes used by ``execute_with_latency`` and
  ``execute_with_profile``.
- :mod:`lassi.profiling.gprof` — gprof orchestrator backing ``gprof_profiling``.
- :mod:`lassi.profiling.performance_tools` — implementations for
  ``run_benchmark``, ``collect_perf_stats``, ``profile_hotspots``,
  ``compare_performance``, ``collect_hardware_model``,
  ``estimate_workload_model``, ``run_roofline_analysis``, and
  ``compare_roofline``.
"""

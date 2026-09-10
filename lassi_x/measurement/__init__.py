"""Measurement backends and matrix orchestration."""

from .common import Backend, _base_measurement, _enforce_architectural_timing
from .groq import GroqBackend, _reap_stale_groq_requests
from .native import NativeBackend
from .orchestration import build_backends, measure_compensation_variants, measure_variants
from .torch import TorchBackend

__all__ = [
    "Backend",
    "GroqBackend",
    "NativeBackend",
    "TorchBackend",
    "build_backends",
    "measure_compensation_variants",
    "measure_variants",
    "_base_measurement",
    "_enforce_architectural_timing",
    "_reap_stale_groq_requests",
]

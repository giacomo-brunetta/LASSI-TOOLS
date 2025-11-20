from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Tuple, Union

from pydantic import BaseModel, Field


# =============================================================================
# System Information Models
# =============================================================================

class SysInfo(BaseModel):
    """
    Base class for all system-information models.

    This class is a common parent type for system-level models (such as CPU and
    GPU descriptors). It enables polymorphic handling of different system info
    objects.
    """
    pass


class CpuSysInfo(SysInfo):
    """
    Static information about a CPU-based system or device.

    This model represents high-level properties of a CPU configuration that
    are relevant for performance and capacity planning.
    """

    ram_memory_size: float = Field(
        ...,
        title="System RAM size",
        description=(
            "Total amount of installed system memory (RAM) in gigabytes (GB). "
            "This typically reflects the physical memory available to the OS, "
            "not including swap or virtual memory."
        ),
        gt=0.0,
    )
    cores: int = Field(
        ...,
        title="CPU core count",
        description=(
            "Total number of logical CPU cores (hardware threads) available on "
            "the system. This value usually corresponds to the number reported "
            "by tools like `nproc` or `multiprocessing.cpu_count()`, and may be "
            "higher than the number of physical cores if hyper-threading is enabled."
        ),
        ge=1,
    )


class GPUSysInfo(SysInfo):
    """
    Static information about the GPU configuration of a system.

    This model summarizes key capacity information for one or more GPUs.
    """

    memory_size: float = Field(
        ...,
        title="GPU memory size",
        description=(
            "Total available GPU memory per device in gigabytes (GB). "
            "For multi-GPU setups, this is typically the memory capacity of a "
            "single GPU, assuming a homogeneous configuration."
        ),
        gt=0.0,
    )
    gpu_count: int = Field(
        ...,
        title="Number of GPUs",
        description=(
            "Total number of GPUs visible and available on the system. "
            "This may be the number reported by libraries such as CUDA, "
            "ROCm, or vendor-specific runtime APIs."
        ),
        ge=0,
    )


class MultiDeviceSysInfo(SysInfo):
    """
    Aggregated system information for both CPU and GPU devices.

    This model groups CPU and GPU information into separate lists.
    """

    cpus: List[CpuSysInfo] = Field(
        default_factory=list,
        title="Per-CPU system information",
        description=(
            "A list of system information entries, one per CPU configuration. "
            "On a typical single-socket system, this list will contain a single "
            "`CpuSysInfo` instance. On multi-socket or heterogeneous systems, "
            "multiple entries can be included."
        ),
    )
    gpus: List[GPUSysInfo] = Field(
        default_factory=list,
        title="Per-GPU system information",
        description=(
            "A list of system information entries, one per GPU configuration. "
            "In homogeneous multi-GPU setups, there may be several identical "
            "entries; in heterogeneous setups, each `GPUSysInfo` can capture "
            "distinct memory sizes or counts."
        ),
    )


# =============================================================================
# Runtime Monitoring Report Models
# =============================================================================

class Report(BaseModel):
    """
    Base class for all runtime monitoring reports.

    Specific report types (latency, energy, usage, etc.) derive from this base
    class to allow uniform handling and composition.
    """
    pass


class TimerReport(Report):
    """
    Timing and latency report for a measured workload.

    Describes how long a single run or an aggregate of runs took to execute,
    expressed as a non-negative duration in seconds.
    """

    latency: float = Field(
        ...,
        title="Latency",
        description=(
            "Execution time in seconds for the measured workload. "
            "This may represent a single run, an average over multiple runs, "
            "or another aggregate, depending on the measurement procedure."
        ),
        ge=0.0,
    )


class EnergyReport(Report):
    """
    Energy and power consumption report.

    Summarizes energy usage during execution, as well as average
    and peak power draw.
    """

    average_power: float = Field(
        ...,
        title="Average power",
        description=(
            "Average power consumption during the measured interval, expressed "
            "in Watts (W). This is typically computed as total energy divided "
            "by total measurement duration."
        ),
        ge=0.0,
    )
    power_peak: float = Field(
        ...,
        title="Peak power",
        description=(
            "Maximum instantaneous or short-window power usage observed during "
            "the measurement, expressed in Watts (W)."
        ),
        ge=0.0,
    )
    energy: float = Field(
        ...,
        title="Total energy",
        description=(
            "Total energy consumed over the measurement interval, expressed in "
            "Joules (J). This is often obtained by integrating power over time "
            "or from energy counters provided by the hardware."
        ),
        ge=0.0,
    )


class UsageReport(Report):
    """
    Generic utilization and memory usage report.

    This model captures average and peak utilization metrics for a device,
    expressed as percentages, along with average and peak memory usage
    expressed in mebibytes (MiB).
    """

    memory_usage_avg: float = Field(
        ...,
        title="Average memory usage (MiB)",
        description=(
            "Average memory usage over the measurement period, expressed in "
            "mebibytes (MiB). This value represents the mean amount of memory "
            "actively allocated by the device during the sampling window."
        ),
        ge=0.0,
    )
    memory_usage_peak: float = Field(
        ...,
        title="Peak memory usage (MiB)",
        description=(
            "Maximum observed memory usage during the measurement period, "
            "expressed in mebibytes (MiB)."
        ),
        ge=0.0,
    )
    utilization_avg: float = Field(
        ...,
        title="Average device usage (%)",
        description=(
            "Average device utilization over the measurement period, expressed "
            "as a percentage of the maximum achievable usage (0–100%). For "
            "example, the average CPU or GPU busy time."
        ),
        ge=0.0,
        le=100.0,
    )
    utilization_peak: float = Field(
        ...,
        title="Peak device usage (%)",
        description=(
            "Maximum observed device utilization during the measurement period, "
            "expressed as a percentage of the maximum achievable usage (0–100%)."
        ),
        ge=0.0,
        le=100.0,
    )


class DeviceReport(UsageReport, EnergyReport):
    @classmethod
    def from_sampling(cls, data: "SamplingData") -> "DeviceReport":
        """
        Build a DeviceReport from raw SamplingData collected by PowerProbe.

        Assumes SamplingData has:
          - power: list[float]           # Watts
          - time_intervals: list[float]  # seconds between samples
          - mem_used_mib: list[float]    # MiB
          - gpu_util_pct: list[float]    # %
        """

        # Avoid division by zero / empty lists
        n = len(data.power)
        if n == 0:
            # You can decide to raise instead if this should never happen
            avg_power = 0.0
            peak_power = 0.0
        else:
            avg_power = sum(data.power) / n
            peak_power = max(data.power)

        # Total duration from sample intervals (if provided)
        duration_s = sum(data.time_intervals) if data.time_intervals else 0.0

        # Energy in Joules: sum(P * dt)
        if data.time_intervals:
            total_energy_j = sum(
                p * dt for p, dt in zip(data.power, data.time_intervals)
            )
        else:
            total_energy_j = 0.0

        # Memory usage
        if data.mem_used_mib:
            avg_mem_mib = sum(data.mem_used_mib) / len(data.mem_used_mib)
            peak_mem_mib = max(data.mem_used_mib)
        else:
            avg_mem_mib = 0.0
            peak_mem_mib = 0.0

        # GPU utilization
        if data.gpu_util_pct:
            avg_util_pct = sum(data.gpu_util_pct) / len(data.gpu_util_pct)
            peak_util_pct = max(data.gpu_util_pct)
        else:
            avg_util_pct = 0.0
            peak_util_pct = 0.0

        return cls(
            # EnergyReport-like fields:
            average_power=avg_power,
            power_peak=peak_power,
            energy=total_energy_j,

            # UsageReport-like fields:
            memory_usage_avg=avg_mem_mib,
            memory_usage_peak=peak_mem_mib,
            utilization_avg=avg_util_pct,
            utilization_peak=peak_util_pct,
        )


class MultiDeviceReport(Report):
    """
    Aggregated runtime report for CPU and GPU devices.

    Groups multiple `DeviceReport` instances into separate lists for CPU and
    GPU devices.
    """

    cpus: List[DeviceReport] = Field(
        default_factory=list,
        title="Per-CPU runtime reports",
        description=(
            "A list of `DeviceReport` objects, one per CPU device or CPU group. "
            "Each report contains combined utilization and energy metrics."
        ),
    )
    gpus: List[DeviceReport] = Field(
        default_factory=list,
        title="Per-GPU runtime reports",
        description=(
            "A list of `DeviceReport` objects, one per GPU device. Each report "
            "contains combined utilization and energy metrics."
        ),
    )


# =============================================================================
# SamplingData: time-series samples -> DeviceReport
# =============================================================================

@dataclass
class SamplingData:
    """
    Container for raw time-series samples collected from device monitoring.

    Each list must have the same length and corresponds index-by-index to one
    collected sampling instant.

    Attributes
    ----------
    power:
        Instantaneous power measurements (e.g., in Watts).
    time_intervals:
        Time deltas between consecutive samples (seconds).
    mem_used_mib:
        Memory usage samples in MiB.
    gpu_util_pct:
        GPU (or device) utilization samples in percent (0–100).
    """

    power: List[float] = field(default_factory=list)
    time_intervals: List[float] = field(default_factory=list)
    mem_used_mib: List[float] = field(default_factory=list)
    gpu_util_pct: List[float] = field(default_factory=list)

    def __add__(self, other: "SamplingData") -> "SamplingData":
        """
        Element-wise addition of two SamplingData objects.

        All lists must have identical length. The returned SamplingData contains
        the element-wise sum of power, memory usage, and utilization, while
        time_intervals are copied from `self` (they are assumed identical).
        """
        if not isinstance(other, type(self)):
            return NotImplemented

        assert len(self.power) == len(other.power), "power list length mismatch"
        assert len(self.time_intervals) == len(other.time_intervals), "time_intervals length mismatch"
        assert len(self.mem_used_mib) == len(other.mem_used_mib), "mem_used_mib length mismatch"
        assert len(self.gpu_util_pct) == len(other.gpu_util_pct), "gpu_util_pct length mismatch"

        return type(self)(
            power=[a + b for a, b in zip(self.power, other.power)],
            time_intervals=list(self.time_intervals),
            mem_used_mib=[a + b for a, b in zip(self.mem_used_mib, other.mem_used_mib)],
            gpu_util_pct=[a + b for a, b in zip(self.gpu_util_pct, other.gpu_util_pct)],
        )

    def to_device_report(self) -> DeviceReport:
        """
        Convert raw sampling data into an aggregated DeviceReport.

        - Average and peak power are derived from the `power` samples.
        - Total energy is computed as sum(power_i * dt_i).
        - Memory metrics (average and peak) are in MiB.
        - Utilization metrics (average and peak) are in percent.
        """
        if not self.power or not self.time_intervals:
            raise ValueError("SamplingData missing power or time interval samples.")

        if len(self.time_intervals) != len(self.power):
            raise ValueError("time_intervals and power must have the same length.")
        if len(self.mem_used_mib) != len(self.power):
            raise ValueError("mem_used_mib and power must have the same length.")
        if len(self.gpu_util_pct) != len(self.power):
            raise ValueError("gpu_util_pct and power must have the same length.")

        # Power stats
        avg_power = sum(self.power) / len(self.power)
        peak_power = max(self.power)

        # Memory stats (MiB)
        avg_mem = sum(self.mem_used_mib) / len(self.mem_used_mib)
        peak_mem = max(self.mem_used_mib)

        # Utilization stats (%)
        avg_util = sum(self.gpu_util_pct) / len(self.gpu_util_pct)
        peak_util = max(self.gpu_util_pct)

        # Energy in Joules = integral of power over time (discrete sum)
        energy = sum(p * dt for p, dt in zip(self.power, self.time_intervals))

        return DeviceReport(
            memory_usage=avg_mem,
            memory_peak=peak_mem,
            usage=avg_util,
            peak=peak_util,
            average_power=avg_power,
            power_peak=peak_power,
            energy=energy,
        )
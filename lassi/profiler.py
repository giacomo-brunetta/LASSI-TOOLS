from abc import ABC, abstractmethod
from typing import Callable, List, Tuple, Union
import multiprocessing
import subprocess
import time
import time
from typing import Optional
from lassi.lassi_data_classes import *
from enum import Enum
from pathlib import Path
import re

class Vendor(Enum):
    AMD = 'AMD'
    NVIDIA = 'NVIDIA'
    INTEL = 'INTEL'

# =============================================================================
# Profiler API + MultiProfiler
# =============================================================================

class Profiler(ABC):
    @abstractmethod
    def start(self) -> None:
        """Begin profiling (start timers, sampling, counters, etc.)."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop profiling and finalize data collection."""
        pass

    @abstractmethod
    def get_report(self) -> Union[Report, List[Report]]:
        """
        Build and return one or more Report objects summarizing
        the collected profiling data.
        """
        pass

    def profile_task(self, f: Callable[[], subprocess.CompletedProcess]) -> Tuple[subprocess.CompletedProcess, Union[Report, List[Report]]]:
        """
        Convenience method to profile the execution of a callable.

        The callable `f` is expected to return a `subprocess.CompletedProcess`
        (for example, the result of `subprocess.run(...)`), but you can adapt
        this signature if you prefer other return types.

        Ensures that `stop()` is called even if `f()` raises.
        """
        self.start()
        try:
            output = f()
        finally:
            self.stop()

        return output, self.get_report()

class Timer(Profiler):
    """
    Wall-clock timer profiler.

    Measures elapsed time between `start()` and `stop()` using time.perf_counter()
    and exposes it as a TimerReport via `get_report()`.
    """

    def __init__(self) -> None:
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None

    def start(self) -> None:
        """Begin timing."""
        if self._start_time is not None and self._end_time is None:
            # Already started and not yet stopped
            raise RuntimeError("Timer.start() called while timer is already running.")
        self._start_time = time.perf_counter()
        self._end_time = None

    def stop(self) -> None:
        """Stop timing."""
        if self._start_time is None:
            raise RuntimeError("Timer.stop() called before Timer.start().")
        if self._end_time is not None:
            # Already stopped
            raise RuntimeError("Timer.stop() called but timer is already stopped.")
        self._end_time = time.perf_counter()

    def get_report(self) -> TimerReport:
        """
        Build and return a TimerReport summarizing the elapsed time.

        Raises:
            RuntimeError if the timer has not been both started and stopped.
        """
        if self._start_time is None or self._end_time is None:
            raise RuntimeError("Timer has not been both started and stopped.")

        latency = self._end_time - self._start_time
        return TimerReport(latency=latency)

class MultiProfiler(Profiler):
    """
    Composite profiler that manages multiple Profiler instances.

    - `start()` starts all profilers.
    - `stop()` stops all profilers.
    - `get_report()` returns a flat list of all reports.
    """

    def __init__(self, profilers: List[Profiler]):
        self.profilers = profilers

    def start(self) -> None:
        for profiler in self.profilers:
            profiler.start()

    def stop(self) -> None:
        for profiler in self.profilers:
            profiler.stop()

    def get_report(self) -> List[Report]:
        reports: List[Report] = []
        for profiler in self.profilers:
            r = profiler.get_report()
            if isinstance(r, list):
                reports.extend(r)
            else:
                reports.append(r)
        return reports

# =============================================================================
# PowerProbe base class + Nvidia/AMD implementations
# =============================================================================

# Maximum number of samples to keep in the circular-ish buffers.
# Effective buffer length per probe is int(MAX_VALUES / interval).
MAX_VALUES: int = 10_000

class PowerProbe(ABC):
    """
    Abstract base class for power/usage sampling probes using multiprocessing.

    A worker process runs `_get_gpu_data` in a loop and writes samples into
    shared memory buffers.
    """

    @abstractmethod
    def _get_gpu_data(
        self,
        powers,
        times,
        mem_used,
        gpu_utils,
        gpu_id,
        count,
        halt,
        alive,
        isrunning,
        prevTime,
        interval,
    ) -> None:
        """
        Worker function run in a separate process.

        Subclasses must implement this method and perform the actual sampling.
        """
        ...

    def __init__(self, interval: float = 0.01, gpu_id: int = -1):
        self.interval = multiprocessing.Value('d', interval)
        self.len = int(MAX_VALUES / interval)

        self.powers = multiprocessing.Array('d', self.len)
        self.times = multiprocessing.Array('d', self.len)
        self.mem_used = multiprocessing.Array('d', self.len)
        self.gpu_utils = multiprocessing.Array('d', self.len)

        self.gpu_id = multiprocessing.Value('i', gpu_id)
        self.process: multiprocessing.Process | None = None
        self.prevTime = multiprocessing.Value('d', time.time())
        self.halt = multiprocessing.Value('i', 1)
        self.count = multiprocessing.Value('i', 0)
        self.isrunning = multiprocessing.Value('i', 0)
        self.alive = multiprocessing.Value('i', 0)

        self._init_process()

    def _init_process(self) -> None:
        self.halt.value = 1
        self.alive.value = 1
        args = (
            self.powers,
            self.times,
            self.mem_used,
            self.gpu_utils,
            self.gpu_id,
            self.count,
            self.halt,
            self.alive,
            self.isrunning,
            self.prevTime,
            self.interval,
        )
        self.process = multiprocessing.Process(target=self._get_gpu_data, args=args)
        self.process.start()

    def start(self) -> None:
        """
        Begin sampling.

        Resets the sample counter, resets the reference time, and clears the halt flag.
        """
        self.count.value = 0
        self.prevTime.value = time.time()
        self.halt.value = 0

    def stop(self) -> SamplingData:
        """
        Stop sampling and return the collected SamplingData.

        Sets the halt flag, waits until the worker has completed any ongoing
        iteration (or the process dies), then snapshots the shared arrays up to
        the current count value.
        """
        self.halt.value = 1

        # Wait until not running, but avoid infinite busy-loop if the process dies.
        if self.process is not None:
            while self.isrunning.value and self.process.is_alive():
                time.sleep(0.001)

        n = self.count.value

        return SamplingData(
            power=list(self.powers[:n]),
            time_intervals=list(self.times[:n]),
            mem_used_mib=list(self.mem_used[:n]),
            gpu_util_pct=list(self.gpu_utils[:n]),
        )

    def destroy(self) -> None:
        """
        Terminate the worker process gracefully.

        Sets `alive` to 0 and joins the process.
        """
        self.alive.value = 0
        if self.process is not None:
            self.process.join()
            self.process = None

class ArmPowerProbe(PowerProbe):
    """
    PowerProbe implementation using NVIDIA's NVML interface via py3nvml.
    """
    
    def lookup_power_file(self) -> Path:
        hwmon_base = Path("/sys/class/hwmon")
        # Only consider directories matching hwmon<number>
        for hwmon_dir in hwmon_base.iterdir():
            if not hwmon_dir.is_dir():
                continue
            if not re.fullmatch(r"hwmon\d+", hwmon_dir.name):
                continue
            # Try every powerN_label + powerN_input pair in this hwmon directory
                #print(f"Exploring {hwmon_dir}")
            for entry in hwmon_dir.iterdir():
                #print(f"entry: {entry}")
                m = re.match(r"power(\d+)_label$", entry.name)
                if not m:
                    continue
                idx = m.group(1)
                label_file = hwmon_dir / f"power{idx}_label"
                try:
                    label_value = label_file.read_text().strip()
                except Exception:
                    continue
                if re.search("CPU power", label_value):
                    input_file = hwmon_dir / f"power{idx}_input"
                    if input_file.exists():
                        # Found the matching file
                        return input_file
        raise FileNotFoundError(f"No power*_input file found for label 'CPU Power'")

    def __init__(self, interval: float = 0.1, gpu_id: int = -1, path: Path = None):
        self.power_file_path = self.lookup_power_file() if path is None else path
        super().__init__(interval=interval, gpu_id=gpu_id)

    def _get_gpu_data(
        self,
        powers,
        times,
        mem_used,
        gpu_utils,
        gpu_id,
        count,
        halt,
        alive,
        isrunning,
        prevTime,
        interval,
    ) -> None:
        import time as _time

        while alive.value:
            while not halt.value and alive.value:
                isrunning.value = 1
                try:
                    with open(self.power_file_path.resolve(), "r", encoding="utf-8") as f:
                        power = float(f.read()) / 10**6

                    # Wait until next interval
                    new_time = _time.time()
                    while (new_time - prevTime.value) < interval.value and alive.value and not halt.value:
                        new_time = _time.time()

                    # Log everything at this timestamp index
                    idx = count.value
                    if idx < len(powers):
                        powers[idx] = power
                        times[idx] = new_time - prevTime.value
                        mem_used[idx] = 0
                        gpu_utils[idx] = 0

                        count.value += 1
                        prevTime.value = new_time
                finally:
                    isrunning.value = 0

class IntelPowerProbe(PowerProbe):
    """
    TODO this will use RAPL or pyjoules
    """
    pass

class CPUProfiler(Profiler):
    """
    Profiler implementation that uses a PowerProbe to collect CPU power
    over time, and summarizes them as a DeviceReport.
    """

    def __init__(self, probe: PowerProbe = ArmPowerProbe()):
        self._probe = probe
        self._sampling: Optional[SamplingData] = None

    def start(self) -> None:
        """
        Begin profiling by starting the underlying PowerProbe sampling.
        """
        self._sampling = None
        self._probe.start()

    def stop(self) -> None:
        """
        Stop profiling and snapshot the SamplingData from the PowerProbe.
        """
        self._sampling = self._probe.stop()

    def get_report(self) -> CPUReport:
        """
        Convert the collected SamplingData into a CPUReport combining
        usage and energy information.
        """
        if self._sampling is None:
            raise RuntimeError(
                "GPUProfiler.get_report() called before profiling data was collected. "
                "Ensure start() and stop() have been called."
            )

        return CPUReport.from_sampling(self._sampling)

class NvidiaPowerProbe(PowerProbe):
    """
    PowerProbe implementation using NVIDIA's NVML interface via py3nvml.
    """

    def __init__(self, interval: float = 0.01, gpu_id: int = -1):
        # Lazy import happens ONLY when an NvidiaPowerProbe is instantiated
        try:
            from py3nvml.py3nvml import (
                nvmlDeviceGetPowerUsage,
                nvmlDeviceGetCount,
                nvmlDeviceGetHandleByIndex,
                nvmlDeviceGetMemoryInfo,
                nvmlDeviceGetUtilizationRates,
                nvmlInit,
                nvmlShutdown,
            )
        except ImportError as e:
            raise RuntimeError(
                "py3nvml is required for NvidiaPowerProbe but is not installed."
            ) from e

        # Store function refs on the instance
        self.nvmlDeviceGetPowerUsage = nvmlDeviceGetPowerUsage
        self.nvmlDeviceGetCount = nvmlDeviceGetCount
        self.nvmlDeviceGetHandleByIndex = nvmlDeviceGetHandleByIndex
        self.nvmlDeviceGetMemoryInfo = nvmlDeviceGetMemoryInfo
        self.nvmlDeviceGetUtilizationRates = nvmlDeviceGetUtilizationRates
        self.nvmlInit = nvmlInit
        self.nvmlShutdown = nvmlShutdown

        super().__init__(interval=interval, gpu_id=gpu_id)

    def _get_gpu_data(
        self,
        powers,
        times,
        mem_used,
        gpu_utils,
        gpu_id,
        count,
        halt,
        alive,
        isrunning,
        prevTime,
        interval,
    ) -> None:
        import time as _time

        self.nvmlInit()
        try:
            while alive.value:
                while not halt.value and alive.value:
                    isrunning.value = 1
                    try:
                        # Determine which GPUs to query
                        if gpu_id.value > -1:
                            handles = [self.nvmlDeviceGetHandleByIndex(gpu_id.value)]
                        else:
                            num_gpus = self.nvmlDeviceGetCount()
                            handles = [self.nvmlDeviceGetHandleByIndex(i) for i in range(num_gpus)]

                        # --- Power measurement ---
                        power = 0.0
                        for h in handles:
                            # NVML returns mW; convert to W if needed.
                            power += self.nvmlDeviceGetPowerUsage(h) / 1000.0

                        # --- Memory measurement (MiB) ---
                        total_mem_used = 0.0
                        for h in handles:
                            mem_info = self.nvmlDeviceGetMemoryInfo(h)
                            total_mem_used += mem_info.used / (1024 ** 2)

                        # --- Utilization measurement (%)
                        gpu_util_sum = 0.0
                        for h in handles:
                            util = self.nvmlDeviceGetUtilizationRates(h)
                            gpu_util_sum += util.gpu
                        avg_gpu_util = gpu_util_sum / len(handles)

                        # Wait until next interval
                        new_time = _time.time()
                        while (new_time - prevTime.value) < interval.value and alive.value and not halt.value:
                            new_time = _time.time()

                        # Log everything at this timestamp index
                        idx = count.value
                        if idx < len(powers):
                            powers[idx] = power
                            times[idx] = new_time - prevTime.value
                            mem_used[idx] = total_mem_used
                            gpu_utils[idx] = avg_gpu_util

                            count.value += 1
                            prevTime.value = new_time
                    finally:
                        isrunning.value = 0
        finally:
            self.nvmlShutdown()

class AMDPowerProbe(PowerProbe):
    """
    PowerProbe implementation using AMD's amdsmi interface.

    Note: Requires the `amdsmi` package and a supported AMD GPU.
    """

    def __init__(self, interval: float = 0.01, gpu_id: int = 0):
        try:
            from amdsmi import (
                amdsmi_init,
                amdsmi_get_processor_handles,
                amdsmi_get_power_info,
                amdsmi_get_gpu_vram_usage,
                amdsmi_get_gpu_activity,
                amdsmi_shut_down,
            )
        except ImportError as e:
            raise RuntimeError(
                "amdsmi is required for AMDPowerProbe but is not installed."
            ) from e

        self.amdsmi_init = amdsmi_init
        self.amdsmi_get_processor_handles = amdsmi_get_processor_handles
        self.amdsmi_get_power_info = amdsmi_get_power_info
        self.amdsmi_get_gpu_vram_usage = amdsmi_get_gpu_vram_usage
        self.amdsmi_get_gpu_activity = amdsmi_get_gpu_activity
        self.amdsmi_shut_down = amdsmi_shut_down

        super().__init__(interval=interval, gpu_id=gpu_id)

    def _get_gpu_data(
        self,
        powers,
        times,
        mem_used,
        gpu_utils,
        gpu_id,
        count,
        halt,
        alive,
        isrunning,
        prevTime,
        interval,
    ) -> None:
        import time as _time

        self.amdsmi_init()
        handles = self.amdsmi_get_processor_handles()
        h = handles[gpu_id.value]

        try:
            while alive.value:
                while not halt.value and alive.value:
                    isrunning.value = 1
                    try:
                        # --- Power measurement ---
                        power_str = self.amdsmi_get_power_info(h)["current_socket_power"]
                        # amdsmi may return a string like "120" (W) or "N/A"
                        power = float(power_str) if power_str != "N/A" else 0.0

                        # --- Memory measurement (MiB) ---
                        mem_info = self.amdsmi_get_gpu_vram_usage(h)["vram_used"] / 1024.0

                        # --- Utilization measurement (%)
                        gpu_util = self.amdsmi_get_gpu_activity(h)["gfx_activity"]

                        # Wait until next interval
                        new_time = _time.time()
                        while (new_time - prevTime.value) < interval.value and alive.value and not halt.value:
                            new_time = _time.time()

                        idx = int(count.value)
                        if idx < len(powers):
                            powers[idx] = power
                            times[idx] = new_time - prevTime.value
                            mem_used[idx] = mem_info
                            gpu_utils[idx] = gpu_util

                            count.value += 1
                            prevTime.value = new_time
                    finally:
                        isrunning.value = 0
        finally:
            self.amdsmi_shut_down()

class XPUPowerProbe(PowerProbe):
    pass

class GPUProfiler(Profiler):
    """
    Profiler implementation that uses a PowerProbe to collect GPU power,
    memory usage, and utilization samples over time, and summarizes them
    as a DeviceReport.
    """

    def __init__(self, probe: PowerProbe = NvidiaPowerProbe()):
        self._probe = probe
        self._sampling: Optional[SamplingData] = None

    def start(self) -> None:
        """
        Begin profiling by starting the underlying PowerProbe sampling.
        """
        self._sampling = None
        self._probe.start()

    def stop(self) -> None:
        """
        Stop profiling and snapshot the SamplingData from the PowerProbe.
        """
        self._sampling = self._probe.stop()

    def get_report(self) -> GPUReport:
        """
        Convert the collected SamplingData into a GPUReport combining
        usage and energy information.
        """
        if self._sampling is None:
            raise RuntimeError(
                "GPUProfiler.get_report() called before profiling data was collected. "
                "Ensure start() and stop() have been called."
            )

        return GPUReport.from_sampling(self._sampling)
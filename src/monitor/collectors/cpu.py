"""CPU metrics collector."""

from typing import Any

from monitor.collectors.base import BaseCollector


class CPUCollector(BaseCollector):
    """Collects CPU usage and frequency metrics."""

    def __init__(self):
        self._last_idle = 0
        self._last_total = 0

    @property
    def name(self) -> str:
        return "cpu"

    def collect(self) -> dict[str, Any]:
        """Collect CPU metrics from /proc/stat and /sys/.../cpufreq.

        Returns:
            {
                "percent": float,  # CPU usage percentage (0-100)
                "freq": int,       # Current frequency in MHz
            }
        """
        result = {"percent": 0.0, "freq": 0}

        # 1. Calculate CPU % using /proc/stat
        try:
            with open("/proc/stat") as f:
                line = f.readline()
                if line.startswith("cpu"):
                    # cpu  user nice system idle iowait irq softirq steal guest guest_nice
                    parts = [int(x) for x in line.split()[1:]]
                    idle = parts[3] + parts[4]  # idle + iowait
                    total = sum(parts)

                    diff_idle = idle - self._last_idle
                    diff_total = total - self._last_total

                    cpu_percent = 0.0
                    if diff_total > 0:
                        cpu_percent = 100.0 * (1.0 - diff_idle / diff_total)

                    self._last_idle = idle
                    self._last_total = total
                    result["percent"] = round(cpu_percent, 1)
        except Exception:
            pass

        # 2. Get CPU Frequency
        try:
            with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq") as f:
                result["freq"] = int(f.read().strip()) // 1000
        except Exception:
            pass

        return result

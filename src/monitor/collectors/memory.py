"""Memory metrics collector."""

from typing import Any

from monitor.collectors.base import BaseCollector


class MemoryCollector(BaseCollector):
    """Collects memory (RAM and Swap) usage metrics."""

    @property
    def name(self) -> str:
        return "memory"

    def collect(self) -> dict[str, Any]:
        """Collect memory metrics from /proc/meminfo.

        Returns:
            {
                "percent": float,      # RAM usage percentage
                "used_gb": float,      # Used RAM in GB
                "total_gb": float,     # Total RAM in GB
                "swap_percent": float, # Swap usage percentage
                "swap_total_gb": float,
                "swap_used_gb": float,
            }
        """
        result = {"percent": 0.0, "used_gb": 0.0, "total_gb": 1.0, "swap_percent": 0.0}

        try:
            meminfo = {}
            with open("/proc/meminfo") as f:
                for line in f:
                    parts = line.split(":")
                    key = parts[0].strip()
                    value = int(parts[1].strip().split()[0])
                    meminfo[key] = value

            total_kb = meminfo.get("MemTotal", 0)
            available_kb = meminfo.get("MemAvailable", meminfo.get("MemFree", 0))
            used_kb = total_kb - available_kb

            total_gb = total_kb / 1024 / 1024
            used_gb = used_kb / 1024 / 1024
            percent = (used_kb / total_kb * 100) if total_kb > 0 else 0

            swap_total = meminfo.get("SwapTotal", 0)
            swap_free = meminfo.get("SwapFree", 0)
            swap_used = swap_total - swap_free
            swap_percent = (swap_used / swap_total * 100) if swap_total > 0 else 0

            result = {
                "percent": round(percent, 1),
                "used_gb": round(used_gb, 2),
                "total_gb": round(total_gb, 2),
                "swap_percent": round(swap_percent, 1),
                "swap_total_gb": round(swap_total / 1024 / 1024, 2),
                "swap_used_gb": round(swap_used / 1024 / 1024, 2),
            }
        except Exception:
            pass

        return result

"""Process metrics collector."""

import subprocess
from typing import Any

from monitor.collectors.base import BaseCollector


class ProcessCollector(BaseCollector):
    """Collects top processes by CPU usage."""

    def __init__(self, limit: int = 10):
        self._limit = limit

    @property
    def name(self) -> str:
        return "process"

    def collect(self) -> list[dict[str, Any]]:
        """Collect top processes by CPU usage.

        Returns:
            List of process info dicts:
            [
                {"pid": int, "name": str, "cpu": float, "mem": float},
                ...
            ]
        """
        processes = []
        cores = self._get_cpu_core_count()

        try:
            result = subprocess.run(
                ["ps", "aux", "--sort=-%cpu"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                for line in lines[:20]:  # Get top 20, will limit later
                    parts = line.split(None, 10)
                    if len(parts) >= 11:
                        try:
                            # ps %CPU = percentage of one core; normalize so 100% = all cores
                            raw_cpu = float(parts[2])
                            cpu_pct = min(100.0, round(raw_cpu / cores, 1))
                            processes.append(
                                {
                                    "pid": int(parts[1]),
                                    "name": parts[10][:50],
                                    "cpu": cpu_pct,
                                    "mem": round(float(parts[3]), 1),
                                }
                            )
                        except (ValueError, IndexError):
                            continue
        except Exception:
            pass

        return processes[: self._limit]

    def _get_cpu_core_count(self) -> int:
        """Get the number of CPU cores."""
        try:
            with open("/proc/cpuinfo") as f:
                return sum(1 for line in f if line.strip().startswith("processor"))
        except Exception:
            return 1

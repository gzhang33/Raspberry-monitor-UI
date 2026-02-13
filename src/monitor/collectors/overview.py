"""System overview collector."""

import os
import subprocess
from typing import Any, Dict

from monitor.collectors.base import BaseCollector


class OverviewCollector(BaseCollector):
    """Collects system overview information."""

    @property
    def name(self) -> str:
        return "overview"

    def collect(self) -> Dict[str, Any]:
        """Collect system overview.

        Returns:
            {
                "os": str,           # OS name
                "uptime": str,       # Formatted uptime
                "load_1": str,       # 1-minute load average
                "load_5": str,       # 5-minute load average
                "load_15": str,      # 15-minute load average
                "ip": str,           # Local IP address
                "docker": dict or None,  # Docker container status
            }
        """
        result = {
            "os": "Linux",
            "uptime": self._format_uptime(self._get_uptime()),
            "load_1": "0.00",
            "load_5": "0.00",
            "load_15": "0.00",
            "ip": self._get_local_ip(),
            "docker": None,
        }

        # Load averages
        try:
            if hasattr(os, "getloadavg"):
                load_avg = os.getloadavg()
                result["load_1"] = f"{load_avg[0]:.2f}"
                result["load_5"] = f"{load_avg[1]:.2f}"
                result["load_15"] = f"{load_avg[2]:.2f}"
        except Exception:
            pass

        return result

    def _get_uptime(self) -> float:
        """Get system uptime in seconds."""
        try:
            with open("/proc/uptime", "r") as f:
                return float(f.read().split()[0])
        except Exception:
            return 0

    def _format_uptime(self, seconds: float) -> str:
        """Format uptime seconds to human readable string."""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{days}d {hours}h {mins}m"

    def _get_local_ip(self) -> str:
        """Get local IP address."""
        try:
            result = subprocess.run(
                ["hostname", "-I"], capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                ips = result.stdout.strip().split()
                for ip in ips:
                    if not ip.startswith("127.") and not ip.startswith("::1"):
                        return ip
        except Exception:
            pass
        return "-"

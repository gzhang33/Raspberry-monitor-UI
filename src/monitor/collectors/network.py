"""Network metrics collector."""

import subprocess
import threading
import time
from typing import Any, Dict, Optional

from monitor.cache import RateCalculator
from monitor.collectors.base import BaseCollector


class NetworkCollector(BaseCollector):
    """Collects network usage metrics."""

    def __init__(self):
        self._rx_calculator = RateCalculator()
        self._tx_calculator = RateCalculator()

    @property
    def name(self) -> str:
        return "network"

    def collect(self) -> Dict[str, Any]:
        """Collect network metrics from /proc/net/dev.

        Returns:
            {
                "rx_mb_s": float,      # Download rate in MB/s
                "tx_mb_s": float,      # Upload rate in MB/s
                "rx_total_gb": float,  # Total downloaded in GB
                "tx_total_gb": float,  # Total uploaded in GB
            }
        """
        result = {
            "rx_mb_s": 0.0,
            "tx_mb_s": 0.0,
            "rx_total_gb": 0.0,
            "tx_total_gb": 0.0,
        }

        try:
            rx_bytes = 0
            tx_bytes = 0

            with open("/proc/net/dev", "r") as f:
                for line in f:
                    if ":" in line:
                        parts = line.split(":")
                        iface = parts[0].strip()
                        if iface not in ["lo"]:
                            stats = parts[1].split()
                            if len(stats) >= 9:
                                rx_bytes += int(stats[0])
                                tx_bytes += int(stats[8])

            rx_rate = self._rx_calculator.calculate_rate(rx_bytes)
            tx_rate = self._tx_calculator.calculate_rate(tx_bytes)

            result = {
                "rx_mb_s": round(rx_rate / 1024 / 1024, 3),
                "tx_mb_s": round(tx_rate / 1024 / 1024, 3),
                "rx_total_gb": round(rx_bytes / 1024 / 1024 / 1024, 2),
                "tx_total_gb": round(tx_bytes / 1024 / 1024 / 1024, 2),
            }
        except Exception:
            pass

        return result

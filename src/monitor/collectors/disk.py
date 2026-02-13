"""Disk metrics collector."""

import subprocess
import time
from typing import Any, Dict

from monitor.cache import RateCalculator
from monitor.collectors.base import BaseCollector


class DiskCollector(BaseCollector):
    """Collects disk usage and I/O metrics."""

    def __init__(self):
        self._read_calculator = RateCalculator()
        self._write_calculator = RateCalculator()

    @property
    def name(self) -> str:
        return "disk"

    def collect(self) -> Dict[str, Any]:
        """Collect disk metrics from df and /proc/diskstats.

        Returns:
            {
                "percent": float,    # Disk usage percentage
                "used_gb": float,    # Used space in GB
                "total_gb": float,   # Total space in GB
                "read_mb_s": float,  # Read rate in MB/s
                "write_mb_s": float, # Write rate in MB/s
            }
        """
        result = {
            "percent": 0.0,
            "used_gb": 0.0,
            "total_gb": 100.0,
            "read_mb_s": 0.0,
            "write_mb_s": 0.0,
        }

        # 1. Storage Usage from df
        try:
            df_result = subprocess.run(
                ["df", "/"], capture_output=True, text=True, timeout=2
            )
            if df_result.returncode == 0:
                lines = df_result.stdout.strip().split("\n")
                if len(lines) >= 2:
                    parts = lines[1].split()
                    total = int(parts[1])
                    used = int(parts[2])
                    percent = float(parts[4].replace("%", ""))
                    result["percent"] = round(percent, 1)
                    result["total_gb"] = round(total / 1024 / 1024, 2)
                    result["used_gb"] = round(used / 1024 / 1024, 2)
        except Exception:
            pass

        # 2. Disk I/O Rate from /proc/diskstats
        try:
            curr_read = 0
            curr_write = 0
            with open("/proc/diskstats", "r") as f:
                for line in f:
                    parts = line.split()
                    # Looking for mmcblk0 (SD card), sda (SSD), or vda (virtio)
                    if parts[2] in ["mmcblk0", "sda", "vda"]:
                        # Field 5: sectors read, Field 9: sectors written (512 bytes each)
                        curr_read += int(parts[5]) * 512
                        curr_write += int(parts[9]) * 512

            read_rate = self._read_calculator.calculate_rate(curr_read)
            write_rate = self._write_calculator.calculate_rate(curr_write)

            result["read_mb_s"] = round(read_rate / 1024 / 1024, 2)
            result["write_mb_s"] = round(write_rate / 1024 / 1024, 2)
        except Exception:
            pass

        return result

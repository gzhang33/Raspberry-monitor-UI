"""Sensors metrics collector (Raspberry Pi specific)."""

import subprocess
from typing import Any, Dict

from monitor.collectors.base import BaseCollector


class SensorsCollector(BaseCollector):
    """Collects sensor data (temperature, voltage, throttling) from vcgencmd.

    Note: This collector is specific to Raspberry Pi hardware.
    """

    @property
    def name(self) -> str:
        return "sensors"

    def collect(self) -> Dict[str, Any]:
        """Collect sensor metrics using vcgencmd.

        Returns:
            {
                "temp": float or None,       # CPU temperature in Celsius
                "voltage": float or None,    # Core voltage
                "throttled": dict or None,   # Throttling status
            }
        """
        result = {"temp": None, "voltage": None, "throttled": None}

        # Temperature
        try:
            res = subprocess.run(
                ["/usr/bin/vcgencmd", "measure_temp"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if res.returncode == 0:
                temp_str = res.stdout.strip().split("=")[1]
                result["temp"] = float(temp_str.replace("'C", "").replace("C", ""))
        except Exception:
            pass

        # Voltage
        try:
            res = subprocess.run(
                ["/usr/bin/vcgencmd", "measure_volts", "core"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if res.returncode == 0:
                volt_str = res.stdout.strip().split("=")[1]
                result["voltage"] = float(volt_str.replace("V", ""))
        except Exception:
            pass

        # Throttling status
        try:
            res = subprocess.run(
                ["/usr/bin/vcgencmd", "get_throttled"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if res.returncode == 0:
                throttled_str = res.stdout.strip().split("=")[1].strip()
                result["throttled"] = self._parse_throttled(throttled_str)
        except Exception:
            pass

        return result

    def _parse_throttled(self, status: str) -> Dict[str, Any]:
        """Parse the throttled status hex value."""
        try:
            raw = int(status, 16)
            return {
                "raw": raw,
                "current_undervolt": bool(raw & 0x1),
                "current_throttled": bool(raw & 0x4),
                "current_soft_temp": bool(raw & 0x8),
                "current_arm_freq_capped": bool(raw & 0x2),
            }
        except Exception:
            return {"raw": 0}

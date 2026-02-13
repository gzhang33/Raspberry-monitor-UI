"""Tailscale status collector."""

import json
import subprocess
import threading
import time
from typing import Any, Optional

from monitor.collectors.base import BaseCollector


class TailscaleCollector(BaseCollector):
    """Collects Tailscale connection status."""

    def __init__(self, cache_ttl: float = 15.0):
        self._cache_ttl = cache_ttl
        self._cache: Optional[dict[str, Any]] = None
        self._cache_time: float = 0
        self._lock = threading.Lock()

    @property
    def name(self) -> str:
        return "tailscale"

    def collect(self) -> dict[str, Any]:
        """Collect Tailscale status.

        Returns:
            {
                "tailscale_connected": bool,
                "tailscale_ip": str,
            }
        """
        now = time.time()

        with self._lock:
            if self._cache_time and (now - self._cache_time) < self._cache_ttl:
                return self._cache.copy() if self._cache else self._default_result()

        result = self._fetch_status()

        with self._lock:
            self._cache = result
            self._cache_time = now

        return result

    def _fetch_status(self) -> dict[str, Any]:
        """Fetch Tailscale status from CLI."""
        try:
            result = subprocess.run(
                ["tailscale", "status", "--json"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                status = json.loads(result.stdout)
                tailscale_ips = status.get("TailscaleIPs", [])
                return {
                    "tailscale_connected": True,
                    "tailscale_ip": tailscale_ips[0] if tailscale_ips else "-",
                }
        except Exception:
            pass

        return self._default_result()

    def _default_result(self) -> dict[str, Any]:
        """Return default disconnected status."""
        return {"tailscale_connected": False, "tailscale_ip": "-"}

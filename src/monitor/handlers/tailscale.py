"""Tailscale info handler."""

from typing import Any

from monitor.collectors import TailscaleCollector
from monitor.config import get_config


class TailscaleHandler:
    """Handler for Tailscale info endpoint."""

    def __init__(self):
        config = get_config()
        self._collector = TailscaleCollector(
            cache_ttl=config.cache.tailscale_cache_ttl
        )

    def get_info(self) -> dict[str, Any]:
        """Get Tailscale connection info.

        Returns:
            {
                "tailscale_connected": bool,
                "tailscale_ip": str,
            }
        """
        return self._collector.collect()

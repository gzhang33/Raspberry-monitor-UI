"""System stats API handler."""

import time
from typing import Any, Dict, List

from monitor.cache import TTLCache
from monitor.collectors import (
    CPUCollector,
    DiskCollector,
    MemoryCollector,
    NetworkCollector,
    OverviewCollector,
    ProcessCollector,
    SensorsCollector,
    TailscaleCollector,
)
from monitor.config import Config, get_config


class SystemStatsHandler:
    """Handler for system statistics API."""

    def __init__(self, config: Config = None):
        self._config = config or get_config()

        # Initialize collectors
        self._cpu = CPUCollector()
        self._memory = MemoryCollector()
        self._disk = DiskCollector()
        self._network = NetworkCollector()
        self._sensors = SensorsCollector()
        self._overview = OverviewCollector()
        self._tailscale = TailscaleCollector(
            cache_ttl=self._config.cache.tailscale_cache_ttl
        )

        # Process collector has its own cache
        self._process_cache = TTLCache[List[Dict[str, Any]]](
            ttl=self._config.cache.process_list_ttl
        )

        # Main stats cache
        self._stats_cache = TTLCache[Dict[str, Any]](
            ttl=self._config.cache.system_stats_ttl
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get complete system statistics.

        Uses caching to reduce system call overhead.
        """
        return self._stats_cache.get_or_compute(self._collect_all_stats)

    def _collect_all_stats(self) -> Dict[str, Any]:
        """Collect all statistics."""
        now = time.time()

        # Get process list with its own TTL
        processes = self._process_cache.get_or_compute(
            lambda: self._process_collector.collect(),
            ttl=self._config.cache.process_list_ttl,
        )

        return {
            "overview": self._overview.collect(),
            "cpu": self._cpu.collect(),
            "memory": self._memory.collect(),
            "disk": self._disk.collect(),
            "network": self._network.collect(),
            "sensors": self._sensors.collect(),
            "processes": processes[:10],
            "tailscale": self._tailscale.collect(),
        }

    @property
    def _process_collector(self) -> ProcessCollector:
        """Lazy process collector."""
        if not hasattr(self, "_process_collector_instance"):
            self._process_collector_instance = ProcessCollector()
        return self._process_collector_instance

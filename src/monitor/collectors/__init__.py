"""Collectors package for system metrics."""

from monitor.collectors.base import BaseCollector
from monitor.collectors.cpu import CPUCollector
from monitor.collectors.memory import MemoryCollector
from monitor.collectors.disk import DiskCollector
from monitor.collectors.network import NetworkCollector
from monitor.collectors.process import ProcessCollector
from monitor.collectors.sensors import SensorsCollector
from monitor.collectors.tailscale import TailscaleCollector
from monitor.collectors.overview import OverviewCollector

__all__ = [
    "BaseCollector",
    "CPUCollector",
    "MemoryCollector",
    "DiskCollector",
    "NetworkCollector",
    "ProcessCollector",
    "SensorsCollector",
    "TailscaleCollector",
    "OverviewCollector",
]

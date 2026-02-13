"""Request handlers package."""

from monitor.handlers.health import HealthHandler
from monitor.handlers.system import SystemStatsHandler
from monitor.handlers.tailscale import TailscaleHandler

__all__ = ["SystemStatsHandler", "HealthHandler", "TailscaleHandler"]

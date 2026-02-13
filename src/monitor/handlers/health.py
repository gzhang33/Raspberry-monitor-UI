"""Health check handler."""

from typing import Dict, Any


class HealthHandler:
    """Handler for health check endpoint."""

    @staticmethod
    def check() -> Dict[str, Any]:
        """Return health status.

        Returns:
            {"ok": True} if service is healthy
        """
        return {"ok": True}

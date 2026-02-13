"""Health check handler."""

from typing import Any


class HealthHandler:
    """Handler for health check endpoint."""

    @staticmethod
    def check() -> dict[str, Any]:
        """Return health status.

        Returns:
            {"ok": True} if service is healthy
        """
        return {"ok": True}

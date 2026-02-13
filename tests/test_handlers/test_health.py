"""Tests for health handler."""

from monitor.handlers.health import HealthHandler


class TestHealthHandler:
    """Tests for HealthHandler."""

    def test_check_returns_ok(self):
        """Test that health check returns ok."""
        result = HealthHandler.check()
        assert result == {"ok": True}

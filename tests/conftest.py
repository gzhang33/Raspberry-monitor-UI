"""Pytest configuration and fixtures."""

import pytest

from monitor.config import CacheConfig, Config, ServerConfig, SpeedtestConfig


@pytest.fixture
def test_config():
    """Provide a test configuration."""
    return Config(
        server=ServerConfig(host="127.0.0.1", port=18000),
        cache=CacheConfig(
            system_stats_ttl=0.1,  # Short TTL for testing
            process_list_ttl=0.1,
            tailscale_cache_ttl=0.1,
        ),
        speedtest=SpeedtestConfig(
            enabled=False,  # Disable speedtest in tests
            interval_sec=1,
            timeout_sec=1,
            cli_path="/nonexistent/speedtest",
        ),
    )

"""Tests for configuration module."""

import pytest

from monitor.config import CacheConfig, Config, ServerConfig, SpeedtestConfig


class TestServerConfig:
    """Tests for ServerConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ServerConfig()
        assert config.host == "0.0.0.0"
        assert config.port == 10000

    def test_custom_values(self):
        """Test custom configuration values."""
        config = ServerConfig(host="127.0.0.1", port=8080)
        assert config.host == "127.0.0.1"
        assert config.port == 8080


class TestCacheConfig:
    """Tests for CacheConfig."""

    def test_default_values(self):
        """Test default cache TTL values."""
        config = CacheConfig()
        assert config.system_stats_ttl == 2.0
        assert config.process_list_ttl == 8.0
        assert config.tailscale_cache_ttl == 15.0


class TestSpeedtestConfig:
    """Tests for SpeedtestConfig."""

    def test_default_values(self):
        """Test default speedtest configuration."""
        config = SpeedtestConfig()
        assert config.enabled is True
        assert config.interval_sec == 60.0
        assert config.timeout_sec == 60.0
        assert config.cli_path == "/usr/bin/speedtest"


class TestConfig:
    """Tests for main Config class."""

    def test_default_config(self):
        """Test default configuration composition."""
        config = Config()
        assert isinstance(config.server, ServerConfig)
        assert isinstance(config.cache, CacheConfig)
        assert isinstance(config.speedtest, SpeedtestConfig)

    def test_invalid_port(self):
        """Test that invalid port raises error."""
        with pytest.raises(ValueError):
            Config(server=ServerConfig(port=0))

        with pytest.raises(ValueError):
            Config(server=ServerConfig(port=70000))

    def test_invalid_speedtest_interval(self):
        """Test that invalid speedtest interval raises error."""
        with pytest.raises(ValueError):
            Config(speedtest=SpeedtestConfig(interval_sec=5))

"""Configuration management for OpenClaw Monitor.

Supports configuration via environment variables with sensible defaults.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ServerConfig:
    """HTTP server configuration."""

    host: str = "0.0.0.0"
    port: int = field(default_factory=lambda: int(os.getenv("MONITOR_PORT", "10000")))


@dataclass
class CacheConfig:
    """Cache TTL configuration (in seconds)."""

    system_stats_ttl: float = 2.0
    process_list_ttl: float = 8.0  # Heavy operation, refresh less often
    tailscale_cache_ttl: float = field(
        default_factory=lambda: float(os.getenv("TAILSCALE_CACHE_TTL_SEC", "15"))
    )


@dataclass
class SpeedtestConfig:
    """Speedtest configuration."""

    enabled: bool = True
    interval_sec: float = field(
        default_factory=lambda: float(os.getenv("SPEEDTEST_INTERVAL_SEC", "60"))
    )
    timeout_sec: float = field(
        default_factory=lambda: float(os.getenv("SPEEDTEST_TIMEOUT_SEC", "60"))
    )
    cli_path: str = field(
        default_factory=lambda: os.getenv("SPEEDTEST_CLI_PATH", "/usr/bin/speedtest")
    )


@dataclass
class Config:
    """Main application configuration."""

    server: ServerConfig = field(default_factory=ServerConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    speedtest: SpeedtestConfig = field(default_factory=SpeedtestConfig)

    # Static files directory
    static_dir: Path = field(
        default_factory=lambda: Path(__file__).parent / "static"
    )

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls()

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.server.port < 1 or self.server.port > 65535:
            raise ValueError(f"Invalid port: {self.server.port}")

        if self.speedtest.interval_sec < 10:
            raise ValueError("Speedtest interval must be at least 10 seconds")


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def reload_config() -> Config:
    """Reload configuration from environment."""
    global _config
    _config = Config.from_env()
    return _config

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-02-13

### Added
- Modern Python package structure with `src/` layout
- `pyproject.toml` for modern Python packaging (PEP 517/518)
- Modular architecture with separate collectors and handlers
- Configuration management with dataclasses
- Thread-safe TTL caching system
- Rate calculator for network/disk I/O metrics
- Comprehensive test suite with pytest
- Type hints throughout the codebase
- MIT License
- Contributing guidelines
- Code of Conduct
- English (README.md) and Chinese (README_CN.md) documentation
- Detailed systemd service setup instructions

### Changed
- **BREAKING**: Project structure reorganized to `src/monitor/`
- Package renamed to `raspberry-monitor`
- Single `server.py` split into modular components:
  - `collectors/` - CPU, Memory, Disk, Network, Process, Sensors, Tailscale
  - `handlers/` - System stats, Health, Tailscale endpoints
  - `cache.py` - Caching infrastructure
  - `speedtest.py` - Speedtest management
  - `config.py` - Configuration management
- Use `logging` module instead of `print` statements
- Static files moved to `src/monitor/static/`

### Removed
- Old flat project structure
- Hardcoded configuration values

## [1.0.0] - 2025-01-15

### Added
- Initial release
- Real-time system monitoring dashboard
- CPU, Memory, Disk, Network metrics
- Process list with CPU/Memory usage
- Raspberry Pi sensors (temperature, voltage, throttling)
- Tailscale integration
- Speedtest support
- Canvas-based trend charts
- Responsive dark theme UI
- Zero external dependencies (Python stdlib only)
- Systemd service integration

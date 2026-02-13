# Raspberry Monitor

[![PyPI version](https://badge.fury.io/py/raspberry-monitor.svg)](https://badge.fury.io/py/raspberry-monitor)
[![Python](https://img.shields.io/pypi/pyversions/raspberry-monitor.svg)](https://pypi.org/project/raspberry-monitor/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight, real-time system monitoring service for Raspberry Pi/Linux systems. Uses Python's built-in `http.server` with **zero external dependencies**.

[中文文档](README_CN.md)

## Features

- **CPU Monitoring**: Usage, frequency, temperature, throttling status
- **Memory Monitoring**: RAM and Swap usage
- **Disk Monitoring**: Storage usage, read/write speeds
- **Network Monitoring**: Upload/download rates, total traffic, Speedtest integration
- **Process Monitoring**: Top 10 processes by CPU/memory
- **System Overview**: OS info, uptime, load average, IP address, Docker status
- **Tailscale Status**: Connection status and Tailscale IP
- **Trend Charts**: Canvas-based historical trends (click cards to toggle)
- **Real-time Updates**: 5-second polling with visibility-based pause
- **Responsive Design**: GitHub-inspired dark theme, mobile-friendly

## Installation

### From PyPI (Recommended)

```bash
pip install raspberry-monitor
```

### From Source

```bash
git clone https://github.com/raspberry-monitor/monitor.git
cd monitor
pip install -e .
```

## Quick Start

### Command Line

```bash
# Start with default settings (port 10000)
raspberry-monitor

# Or run as module
python -m monitor
```

### Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MONITOR_PORT` | 10000 | Server port |
| `SPEEDTEST_INTERVAL_SEC` | 60 | Speedtest interval |
| `SPEEDTEST_TIMEOUT_SEC` | 60 | Speedtest timeout |
| `TAILSCALE_CACHE_TTL_SEC` | 15 | Tailscale cache TTL |

## Systemd Service Setup

### Option 1: User-level Service (Recommended)

User-level services start when you log in and don't require root privileges.

```bash
# Run the installation script
./deployment/install.sh

# Manual setup (if you prefer)
mkdir -p ~/.config/systemd/user
cp deployment/monitor.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now monitor
```

**Commands:**
```bash
systemctl --user start monitor      # Start
systemctl --user stop monitor       # Stop
systemctl --user restart monitor    # Restart
systemctl --user status monitor     # Status
journalctl --user -u monitor -f     # View logs
```

### Option 2: System-level Service (Boot-time Start)

System-level services start at boot time before any user logs in.

```bash
# Copy service file to system directory
sudo cp deployment/monitor.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start
sudo systemctl enable --now monitor

# Check status
sudo systemctl status monitor
```

**Commands:**
```bash
sudo systemctl start monitor        # Start
sudo systemctl stop monitor         # Stop
sudo systemctl restart monitor      # Restart
sudo systemctl status monitor       # Status
sudo journalctl -u monitor -f       # View logs
```

### Custom Port Configuration

Edit the service file to change the port:

```bash
# For user-level service
nano ~/.config/systemd/user/monitor.service

# For system-level service
sudo nano /etc/systemd/system/monitor.service
```

Add or modify the `Environment` line:
```ini
[Service]
Environment=MONITOR_PORT=8080
```

Then reload and restart:
```bash
# User-level
systemctl --user daemon-reload
systemctl --user restart monitor

# System-level
sudo systemctl daemon-reload
sudo systemctl restart monitor
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Main dashboard |
| `GET /api/system-stats` | Complete system metrics |
| `GET /api/tailscale-ip` | Tailscale connection info |
| `GET /api/health` | Health check |

### Example Response

```json
{
  "overview": {
    "os": "Linux 6.12.62+rpt-rpi-v8",
    "uptime": "15d 4h 32m",
    "load_1": "0.45",
    "ip": "192.168.1.100"
  },
  "cpu": {"percent": 12.3, "freq": 1200},
  "memory": {"percent": 45.6, "used_gb": 1.85, "total_gb": 4.00},
  "disk": {"percent": 67.2, "used_gb": 27.5, "total_gb": 40.9},
  "network": {"rx_mb_s": 0.125, "tx_mb_s": 0.032},
  "sensors": {"temp": 42.5, "voltage": 1.2}
}
```

## System Requirements

### Required
- Python 3.9+
- Linux (tested on Raspberry Pi OS)

### Optional
- `vcgencmd` - Raspberry Pi sensors (temperature, voltage, throttling)
- `tailscale` - Tailscale status
- `speedtest-cli` - Network speed testing
- `docker` - Docker container status

## Project Structure

```
raspberry-monitor/
├── pyproject.toml              # Modern Python packaging
├── README.md                   # This file
├── README_CN.md               # Chinese documentation
├── LICENSE                     # MIT License
├── CHANGELOG.md               # Version history
├── CONTRIBUTING.md            # Contribution guidelines
│
├── src/monitor/               # Main package
│   ├── __init__.py            # Package entry
│   ├── __main__.py            # CLI entry point
│   ├── config.py              # Configuration management
│   ├── server.py              # HTTP server
│   ├── cache.py               # TTL caching
│   ├── speedtest.py           # Speedtest manager
│   ├── collectors/            # Metric collectors
│   │   ├── cpu.py
│   │   ├── memory.py
│   │   ├── disk.py
│   │   ├── network.py
│   │   └── ...
│   ├── handlers/              # HTTP handlers
│   └── static/                # Frontend files
│
├── tests/                     # Test suite
├── deployment/                # Deployment configs
│   ├── monitor.service        # Systemd service
│   └── install.sh             # Installation script
│
└── .github/                   # GitHub configurations
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check src tests

# Type check
mypy src
```

## Performance

- **Caching**: System stats cached for 2s, process list for 8s
- **Network Rate**: Uses `/proc/net/dev` counters with delta calculations
- **Speedtest**: Runs every 60s to avoid network overhead
- **Frontend**: 5s polling, pauses when tab is hidden

## Notes

1. **Raspberry Pi Specific**: Some sensors (`vcgencmd`) only work on Raspberry Pi
2. **No Auth**: Currently open access; consider adding auth for public exposure
3. **Zero Dependencies**: Uses only Python standard library

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

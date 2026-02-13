# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenClaw System Monitor is a lightweight, real-time system monitoring service for Raspberry Pi/Linux systems. It uses Python's built-in `http.server` with no external dependencies.

## Commands

### Running the Server

```bash
# Manual start (development)
python3 server.py

# User-level systemd (recommended for production)
./start.sh                                          # Initial setup
systemctl --user {start|stop|restart|status} monitor

# System-level systemd (requires root)
sudo systemctl {start|stop|restart|status} monitor.service
```

### Configuration via Environment Variables

- `MONITOR_PORT` - Server port (default: 10000)
- `SPEEDTEST_INTERVAL_SEC` - Speedtest interval (default: 60)
- `SPEEDTEST_TIMEOUT_SEC` - Speedtest timeout (default: 60)
- `SPEEDTEST_CLI_PATH` - Custom speedtest-cli path
- `TAILSCALE_CACHE_TTL_SEC` - Tailscale cache TTL (default: 15)

## Architecture

### Backend (server.py)

Single-file Python HTTP server using standard library only:

- **HTTP Handler**: `MonitorHandler` extends `SimpleHTTPRequestHandler`
- **Caching Strategy**: Multiple TTL-based caches to reduce system call overhead:
  - System stats: 2s TTL
  - Process list: 8s TTL (heavy operation due to `ps` scanning `/proc`)
  - Tailscale status: 15s TTL
- **Rate Calculations**: Uses `/proc/net/dev` and `/proc/diskstats` counters with delta calculations
- **Path Normalization**: `_normalize_path()` strips `/monitor` prefix for Tailscale Funnel compatibility

### Frontend (index.html)

Self-contained single-page app with no external dependencies:

- Canvas-based trend charts (click cards to toggle)
- 5-second polling with visibility-based pause
- GitHub-inspired dark theme via CSS variables

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Main dashboard HTML |
| `GET /api/system-stats` | Complete system metrics (JSON) |
| `GET /api/tailscale-ip` | Tailscale connection info |
| `GET /api/health` | Health check |

### System Dependencies

- **Required**: `top`, `ps`, `df`, `hostname`
- **Raspberry Pi specific**: `vcgencmd` (temperature, voltage, throttling)
- **Optional**: `docker`, `tailscale`, `speedtest-cli`

## Key Implementation Details

1. **Thread Safety**: `SPEEDTEST_STATE_LOCK` and `TAILSCALE_CACHE_LOCK` protect shared state
2. **Graceful Degradation**: Missing optional dependencies don't break the server
3. **Error Handling**: Subprocess failures return graceful fallbacks (e.g., `None` values)
4. **No Authentication**: Currently open access; consider adding auth for production exposure

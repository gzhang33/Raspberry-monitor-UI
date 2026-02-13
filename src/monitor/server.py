"""HTTP server for Raspberry Monitor.

A lightweight HTTP server using Python's built-in http.server.
"""

import http.server
import json
import logging
import os
import socketserver
from pathlib import Path
from typing import Any, Dict, Optional

from monitor.config import Config, get_config
from monitor.handlers import HealthHandler, SystemStatsHandler, TailscaleHandler
from monitor.speedtest import SpeedtestManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _normalize_path(path: str) -> str:
    """Strip /monitor prefix for Tailscale Funnel compatibility."""
    if path.startswith("/monitor/"):
        return path[9:] or "/"
    if path == "/monitor":
        return "/"
    return path


class MonitorHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler for monitor endpoints."""

    # Class-level handlers (initialized in serve_forever)
    _system_handler: Optional[SystemStatsHandler] = None
    _tailscale_handler: Optional[TailscaleHandler] = None
    _speedtest_manager: Optional[SpeedtestManager] = None
    _static_dir: Optional[Path] = None

    def do_GET(self) -> None:
        """Handle GET requests."""
        raw_path = self.path.split("?")[0]
        path = _normalize_path(raw_path)

        if path == "/" or path == "":
            self._serve_html()
        elif path == "/api/system-stats":
            self._serve_system_stats()
        elif path == "/api/tailscale-ip":
            self._serve_tailscale()
        elif path == "/api/health":
            self._serve_json(200, HealthHandler.check())
        else:
            self._serve_json(404, {"error": "Not found"})

    def _serve_json(self, code: int, obj: Any) -> None:
        """Send JSON response."""
        body = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
        try:
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass  # Client disconnected

    def _serve_html(self) -> None:
        """Serve the main HTML page."""
        if self._static_dir is None:
            self._serve_json(500, {"error": "Static directory not configured"})
            return

        html_path = self._static_dir / "index.html"
        if html_path.exists():
            with open(html_path, "rb") as f:
                data = f.read()
            try:
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
                self.send_header("Pragma", "no-cache")
                self.send_header("Expires", "0")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass
        else:
            self._serve_json(404, {"error": "index.html not found"})

    def _serve_system_stats(self) -> None:
        """Serve system statistics."""
        if self._system_handler is None:
            self._serve_json(500, {"error": "Handler not initialized"})
            return
        stats = self._system_handler.get_stats()

        # Add speedtest data to network stats
        if self._speedtest_manager:
            speedtest_status = self._speedtest_manager.get_status()
            if "network" in stats:
                stats["network"]["speedtest"] = speedtest_status
                stats["network"]["ping_ms"] = speedtest_status.get("ping_ms")

        self._serve_json(200, stats)

    def _serve_tailscale(self) -> None:
        """Serve Tailscale info."""
        if self._tailscale_handler is None:
            self._serve_json(500, {"error": "Handler not initialized"})
            return
        self._serve_json(200, self._tailscale_handler.get_info())

    def log_message(self, format: str, *args) -> None:
        """Suppress default logging."""
        pass


class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Threaded TCP server for handling concurrent requests."""

    allow_reuse_address = True
    daemon_threads = True


def create_server(config: Config = None) -> ThreadingTCPServer:
    """Create and configure the HTTP server."""
    config = config or get_config()

    # Initialize handlers
    MonitorHandler._system_handler = SystemStatsHandler(config)
    MonitorHandler._tailscale_handler = TailscaleHandler()
    MonitorHandler._speedtest_manager = SpeedtestManager(config.speedtest)
    MonitorHandler._static_dir = config.static_dir

    # Change to static directory for SimpleHTTPRequestHandler
    os.chdir(config.static_dir)

    server = ThreadingTCPServer(
        (config.server.host, config.server.port),
        MonitorHandler,
    )

    return server


def main() -> int:
    """Main entry point."""
    config = get_config()
    server = create_server(config)

    logger.info(f"Raspberry Monitor v{__import__('monitor').__version__}")
    logger.info(f"Server started on port {config.server.port}")
    logger.info(f"Local: http://127.0.0.1:{config.server.port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped")
    finally:
        server.shutdown()

    return 0


if __name__ == "__main__":
    exit(main())

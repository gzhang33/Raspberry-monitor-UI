"""Speedtest functionality with background execution."""

import json
import os
import subprocess
import threading
import time
from dataclasses import dataclass
from typing import Any, Optional

from monitor.config import SpeedtestConfig


@dataclass
class SpeedtestResult:
    """Speedtest result data."""

    ping_ms: Optional[float] = None
    download_mbps: Optional[float] = None
    upload_mbps: Optional[float] = None
    timestamp: float = 0
    error: Optional[str] = None
    in_progress: bool = False


class SpeedtestManager:
    """Manages periodic speedtest execution."""

    def __init__(self, config: SpeedtestConfig):
        self._config = config
        self._result = SpeedtestResult()
        self._last_attempt_time: float = 0
        self._lock = threading.Lock()

    def get_status(self) -> dict[str, Any]:
        """Get current speedtest status and results."""
        with self._lock:
            return {
                "ping_ms": self._result.ping_ms,
                "download_mbps": self._result.download_mbps,
                "upload_mbps": self._result.upload_mbps,
                "last_updated_ts": int(self._result.timestamp) if self._result.timestamp else 0,
                "last_error": self._result.error,
                "in_progress": self._result.in_progress,
            }

    def maybe_trigger(self, current_time: float) -> None:
        """Trigger speedtest if interval has passed and not already running."""
        if not self._config.enabled:
            return

        with self._lock:
            if self._result.in_progress:
                return
            if (current_time - self._last_attempt_time) < self._config.interval_sec:
                return
            self._result.in_progress = True
            self._last_attempt_time = current_time

        thread = threading.Thread(
            target=self._run_speedtest,
            name="openclaw-speedtest",
            daemon=True,
        )
        thread.start()

    def _run_speedtest(self) -> None:
        """Execute speedtest in background thread."""
        error: Optional[str] = None
        new_data: Optional[dict[str, float]] = None

        if not os.path.exists(self._config.cli_path):
            error = f"{self._config.cli_path} not found"
        else:
            try:
                result = subprocess.run(
                    [
                        self._config.cli_path,
                        "--accept-license",
                        "--accept-gdpr",
                        "--format=json",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=self._config.timeout_sec,
                )
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    ping = data.get("ping", {})
                    dl = data.get("download", {})
                    ul = data.get("upload", {})
                    new_data = {
                        "ping_ms": round(ping.get("latency", 0), 1),
                        # bandwidth is bytes/sec -> convert to Mbps
                        "download_mbps": round(dl.get("bandwidth", 0) * 8 / 1_000_000, 2),
                        "upload_mbps": round(ul.get("bandwidth", 0) * 8 / 1_000_000, 2),
                    }
                else:
                    error = f"speedtest exited {result.returncode}: {result.stderr.strip()[:200]}"
            except subprocess.TimeoutExpired:
                error = "Speedtest timed out"
            except json.JSONDecodeError:
                error = "Invalid speedtest JSON response"
            except Exception as e:
                error = str(e)

        with self._lock:
            if new_data is not None:
                self._result.ping_ms = new_data["ping_ms"]
                self._result.download_mbps = new_data["download_mbps"]
                self._result.upload_mbps = new_data["upload_mbps"]
                self._result.timestamp = time.time()
                self._result.error = None
            else:
                self._result.error = error
            self._result.in_progress = False

        if error:
            print(f"Speedtest error: {error}")

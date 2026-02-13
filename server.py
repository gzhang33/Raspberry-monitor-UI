#!/usr/bin/env python3
"""System Monitor Server for OpenClaw"""

import http.server
import socketserver
import json
import os
import subprocess
import threading
import time
from typing import Dict, Any, List

PORT = int(os.environ.get("MONITOR_PORT", "10000"))
DIRECTORY = "/home/admin/monitor"
SPEEDTEST_INTERVAL_SEC = int(os.environ.get("SPEEDTEST_INTERVAL_SEC", "60"))
SPEEDTEST_TIMEOUT_SEC = int(os.environ.get("SPEEDTEST_TIMEOUT_SEC", "60"))
TAILSCALE_CACHE_TTL_SEC = int(os.environ.get("TAILSCALE_CACHE_TTL_SEC", "15"))

SYSTEM_STATS_CACHE = {}
SYSTEM_STATS_CACHE_TIME = 0
CACHE_TTL = 2
# Process list is heavy (ps scans /proc); refresh less often to avoid periodic CPU spikes.
PROCESS_LIST_TTL = 8
PROCESS_LIST_CACHE = []
PROCESS_LIST_CACHE_TIME = 0

# Cache for rate calculations
NET_STATS = {"rx_bytes": 0, "tx_bytes": 0}
NET_STATS_TIME = time.time()

DISK_STATS = {"read_bytes": 0, "write_bytes": 0}
DISK_STATS_TIME = time.time()

CPU_STATS = {"idle": 0, "total": 0}

SPEEDTEST_CACHE = {"ping_ms": None, "download_mbps": None, "upload_mbps": None}
SPEEDTEST_CACHE_TIME = 0
SPEEDTEST_LAST_ERROR = None
SPEEDTEST_IN_PROGRESS = False
SPEEDTEST_LAST_ATTEMPT_TIME = 0
SPEEDTEST_STATE_LOCK = threading.Lock()

TAILSCALE_CACHE = {"tailscale_connected": False, "tailscale_ip": "-"}
TAILSCALE_CACHE_TIME = 0
TAILSCALE_CACHE_LOCK = threading.Lock()


def _normalize_path(path: str) -> str:
    """Strip /monitor prefix so backend works when Tailscale forwards with path preserved."""
    if path.startswith("/monitor/"):
        return path[9:] or "/"
    if path == "/monitor":
        return "/"
    return path


class MonitorHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        raw_path = self.path.split("?")[0]
        path = _normalize_path(raw_path)
        if path == "/" or path == "":
            self.serve_html()
        elif path == "/api/system-stats":
            self._serve_system_stats()
        elif path == "/api/tailscale-ip":
            self._serve_tailscale_ip()
        elif path == "/api/health":
            self._send_json(200, {"ok": True})
        else:
            self._send_json(404, {"error": "Not found"})

    def _send_json(self, code: int, obj: Any):
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
            # Client disconnected while we were writing response.
            return

    def serve_html(self):
        html_path = os.path.join(DIRECTORY, "index.html")
        if os.path.exists(html_path):
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
                return

    def _serve_system_stats(self):
        stats = get_system_stats()
        self._send_json(200, stats)

    def _serve_tailscale_ip(self):
        ts_info = get_tailscale_info()
        self._send_json(200, ts_info)

    def log_message(self, format, *args):
        pass


def get_system_stats() -> Dict[str, Any]:
    global SYSTEM_STATS_CACHE, SYSTEM_STATS_CACHE_TIME
    global PROCESS_LIST_CACHE, PROCESS_LIST_CACHE_TIME
    now = time.time()

    if SYSTEM_STATS_CACHE and (now - SYSTEM_STATS_CACHE_TIME) < CACHE_TTL:
        return SYSTEM_STATS_CACHE

    try:
        overview = get_overview()
        cpu = get_cpu_stats()
        memory = get_memory_stats()
        disk = get_disk_stats()
        network = get_network_stats()
        sensors = get_sensors()
        # Refresh process list only when its TTL expired (reduces ps-induced CPU spikes).
        if PROCESS_LIST_CACHE and (now - PROCESS_LIST_CACHE_TIME) < PROCESS_LIST_TTL:
            processes = PROCESS_LIST_CACHE
        else:
            processes = get_top_processes()
            PROCESS_LIST_CACHE = processes
            PROCESS_LIST_CACHE_TIME = now
        tailscale = get_tailscale_info()

        stats = {
            "overview": overview,
            "cpu": cpu,
            "memory": memory,
            "disk": disk,
            "network": network,
            "sensors": sensors,
            "processes": processes[:10],
            "tailscale": tailscale
        }

        SYSTEM_STATS_CACHE = stats
        SYSTEM_STATS_CACHE_TIME = now
        return stats
    except Exception as e:
        print(f"Error: {e}")
        return SYSTEM_STATS_CACHE if SYSTEM_STATS_CACHE else {}


def get_overview() -> Dict[str, Any]:
    try:
        uptime = get_uptime()
        load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
        ip = get_local_ip()
        
        return {
            "os": "Linux",
            "uptime": format_uptime(uptime),
            "load_1": f"{load_avg[0]:.2f}",
            "load_5": f"{load_avg[1]:.2f}",
            "load_15": f"{load_avg[2]:.2f}",
            "ip": ip,
            "docker": None
        }
    except Exception as e:
        print(f"Error: {e}")
        return {}


def get_uptime() -> float:
    try:
        with open("/proc/uptime", "r") as f:
            return float(f.read().split()[0])
    except:
        return 0


def format_uptime(seconds: float) -> str:
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    mins = int((seconds % 3600) // 60)
    return f"{days}d {hours}h {mins}m"


def get_local_ip() -> str:
    try:
        result = subprocess.run(["hostname", "-I"], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            ips = result.stdout.strip().split()
            for ip in ips:
                if not ip.startswith("127.") and not ip.startswith("::1"):
                    return ip
    except:
        pass
    return "-"


def get_cpu_stats() -> Dict[str, Any]:
    global CPU_STATS
    try:
        # 1. Calculate CPU % using /proc/stat
        with open("/proc/stat", "r") as f:
            line = f.readline()
            if line.startswith("cpu"):
                # cpu  user nice system idle iowait irq softirq steal guest guest_nice
                parts = [int(x) for x in line.split()[1:]]
                idle = parts[3] + parts[4] # idle + iowait
                total = sum(parts)
                
                diff_idle = idle - CPU_STATS["idle"]
                diff_total = total - CPU_STATS["total"]
                
                cpu_percent = 0.0
                if diff_total > 0:
                    cpu_percent = 100.0 * (1.0 - diff_idle / diff_total)
                
                CPU_STATS = {"idle": idle, "total": total}
        
        # 2. Get CPU Frequency
        freq = 0
        try:
            with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq", "r") as f:
                freq = int(f.read().strip()) // 1000
        except:
            pass
        
        return {"percent": round(cpu_percent, 1), "freq": freq}
    except Exception as e:
        print(f"CPU Error: {e}")
        return {"percent": 0, "freq": 0}


def get_memory_stats() -> Dict[str, Any]:
    try:
        with open("/proc/meminfo", "r") as f:
            meminfo = {}
            for line in f:
                parts = line.split(":")
                key = parts[0].strip()
                value = int(parts[1].strip().split()[0])
                meminfo[key] = value
        
        total_kb = meminfo.get("MemTotal", 0)
        available_kb = meminfo.get("MemAvailable", meminfo.get("MemFree", 0))
        used_kb = total_kb - available_kb
        
        total_gb = total_kb / 1024 / 1024
        used_gb = used_kb / 1024 / 1024
        percent = (used_kb / total_kb * 100) if total_kb > 0 else 0
        
        swap_total = meminfo.get("SwapTotal", 0)
        swap_free = meminfo.get("SwapFree", 0)
        swap_used = swap_total - swap_free
        swap_percent = (swap_used / swap_total * 100) if swap_total > 0 else 0
        
        return {
            "percent": round(percent, 1),
            "used_gb": round(used_gb, 2),
            "total_gb": round(total_gb, 2),
            "swap_percent": round(swap_percent, 1),
            "swap_total_gb": round(swap_total / 1024 / 1024, 2),
            "swap_used_gb": round(swap_used / 1024 / 1024, 2)
        }
    except Exception as e:
        print(f"Error: {e}")
        return {"percent": 0, "used_gb": 0, "total_gb": 1, "swap_percent": 0}


def get_disk_stats() -> Dict[str, Any]:
    global DISK_STATS, DISK_STATS_TIME
    
    # 1. Storage Usage
    percent, used_gb, total_gb = 0, 0, 100
    try:
        result = subprocess.run(["df", "/"], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            if len(lines) >= 2:
                parts = lines[1].split()
                total = int(parts[1])
                used = int(parts[2])
                percent = float(parts[4].replace("%", ""))
                # df default output is 1K-blocks
                total_gb = total / 1024 / 1024
                used_gb = used / 1024 / 1024
    except Exception as e:
        print(f"Df Error: {e}")

    # 2. Disk I/O Rate
    read_mb_s, write_mb_s = 0.0, 0.0
    try:
        curr_read = 0
        curr_write = 0
        with open("/proc/diskstats", "r") as f:
            for line in f:
                parts = line.split()
                # Looking for mmcblk0 (SD card) or sda (SSD)
                # Filter for physical devices (usually numbers like 8 0, 179 0)
                if parts[2] in ["mmcblk0", "sda", "vda"]:
                    # Field 6: sectors read, Field 10: sectors written (512 bytes each)
                    curr_read += int(parts[5]) * 512
                    curr_write += int(parts[9]) * 512

        now = time.time()
        time_delta = now - DISK_STATS_TIME
        
        if time_delta > 0 and DISK_STATS["read_bytes"] > 0:
            read_delta = curr_read - DISK_STATS["read_bytes"]
            write_delta = curr_write - DISK_STATS["write_bytes"]
            read_mb_s = (read_delta / time_delta) / 1024 / 1024
            write_mb_s = (write_delta / time_delta) / 1024 / 1024

        DISK_STATS = {"read_bytes": curr_read, "write_bytes": curr_write}
        DISK_STATS_TIME = now
        
    except Exception as e:
        print(f"Disk I/O Error: {e}")

    return {
        "percent": round(percent, 1),
        "used_gb": round(used_gb, 2),
        "total_gb": round(total_gb, 2),
        "read_mb_s": round(read_mb_s, 2),
        "write_mb_s": round(write_mb_s, 2)
    }


def get_network_stats() -> Dict[str, Any]:
    global NET_STATS, NET_STATS_TIME
    
    try:
        rx_bytes = 0
        tx_bytes = 0
        
        try:
            with open("/proc/net/dev", "r") as f:
                for line in f:
                    if ":" in line:
                        parts = line.split(":")
                        iface = parts[0].strip()
                        if iface not in ["lo"]:
                            stats = parts[1].split()
                            if len(stats) >= 9:
                                rx_bytes += int(stats[0])
                                tx_bytes += int(stats[8])
        except:
            pass
        
        now = time.time()
        time_delta = now - NET_STATS_TIME
        
        rx_rate = 0
        tx_rate = 0
        
        if time_delta > 0 and NET_STATS["rx_bytes"] > 0:
            rx_delta = rx_bytes - NET_STATS["rx_bytes"]
            tx_delta = tx_bytes - NET_STATS["tx_bytes"]
            rx_rate = (rx_delta / time_delta) / 1024 / 1024
            tx_rate = (tx_delta / time_delta) / 1024 / 1024
        
        NET_STATS = {"rx_bytes": rx_bytes, "tx_bytes": tx_bytes}
        NET_STATS_TIME = now

        maybe_trigger_speedtest_async(now)
        with SPEEDTEST_STATE_LOCK:
            speedtest = SPEEDTEST_CACHE.copy()
            speedtest["in_progress"] = SPEEDTEST_IN_PROGRESS
            speedtest["last_updated_ts"] = int(SPEEDTEST_CACHE_TIME) if SPEEDTEST_CACHE_TIME else 0
            speedtest["last_error"] = SPEEDTEST_LAST_ERROR

        rx_total_gb = round(rx_bytes / 1024 / 1024 / 1024, 2)
        tx_total_gb = round(tx_bytes / 1024 / 1024 / 1024, 2)
        
        return {
            "rx_mb_s": round(rx_rate, 3),
            "tx_mb_s": round(tx_rate, 3),
            "rx_total_gb": rx_total_gb,
            "tx_total_gb": tx_total_gb,
            "speedtest": speedtest,
            "ping_ms": speedtest.get("ping_ms")
        }
    except Exception as e:
        print(f"Error: {e}")
        return {
            "rx_mb_s": 0,
            "tx_mb_s": 0,
            "rx_total_gb": 0,
            "tx_total_gb": 0,
            "speedtest": {
                "ping_ms": None,
                "download_mbps": None,
                "upload_mbps": None,
                "in_progress": False,
                "last_updated_ts": 0,
                "last_error": None,
            },
            "ping_ms": None,
        }


def maybe_trigger_speedtest_async(now: float) -> None:
    global SPEEDTEST_IN_PROGRESS, SPEEDTEST_LAST_ATTEMPT_TIME
    with SPEEDTEST_STATE_LOCK:
        if SPEEDTEST_IN_PROGRESS:
            return
        if (now - SPEEDTEST_LAST_ATTEMPT_TIME) < SPEEDTEST_INTERVAL_SEC:
            return
        SPEEDTEST_IN_PROGRESS = True
        SPEEDTEST_LAST_ATTEMPT_TIME = now

    thread = threading.Thread(target=_run_speedtest_once, name="monitor-speedtest", daemon=True)
    thread.start()


def _run_speedtest_once() -> None:
    global SPEEDTEST_CACHE, SPEEDTEST_CACHE_TIME, SPEEDTEST_LAST_ERROR, SPEEDTEST_IN_PROGRESS
    error = None
    new_speedtest_data = None
    speedtest_bin = "/usr/bin/speedtest"

    if not os.path.exists(speedtest_bin):
        error = f"{speedtest_bin} not found"
    else:
        try:
            result = subprocess.run(
                [speedtest_bin, "--accept-license", "--accept-gdpr", "--format=json"],
                capture_output=True, text=True, timeout=SPEEDTEST_TIMEOUT_SEC,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                ping = data.get("ping", {})
                dl = data.get("download", {})
                ul = data.get("upload", {})
                new_speedtest_data = {
                    "ping_ms": round(ping.get("latency", 0), 1),
                    # bandwidth is bytes/sec -> convert to Mbps
                    "download_mbps": round(dl.get("bandwidth", 0) * 8 / 1_000_000, 2),
                    "upload_mbps": round(ul.get("bandwidth", 0) * 8 / 1_000_000, 2),
                }
            else:
                error = f"speedtest exited {result.returncode}: {result.stderr.strip()[:200]}"
        except Exception as e:
            error = str(e)

    with SPEEDTEST_STATE_LOCK:
        if new_speedtest_data is not None:
            SPEEDTEST_CACHE.update(new_speedtest_data)
            SPEEDTEST_CACHE_TIME = time.time()
            SPEEDTEST_LAST_ERROR = None
        else:
            SPEEDTEST_LAST_ERROR = error
        SPEEDTEST_IN_PROGRESS = False

    if error:
        print(f"Speedtest error: {error}")


def get_sensors() -> Dict[str, Any]:
    sensors = {"temp": None, "voltage": None, "throttled": None}
    
    try:
        result = subprocess.run(["/usr/bin/vcgencmd", "measure_temp"], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            temp_str = result.stdout.strip().split("=")[1]
            sensors["temp"] = float(temp_str.replace("'C", "").replace("C", ""))
    except:
        pass
    
    try:
        result = subprocess.run(["/usr/bin/vcgencmd", "measure_volts", "core"], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            volt_str = result.stdout.strip().split("=")[1]
            sensors["voltage"] = float(volt_str.replace("V", ""))
    except:
        pass
    
    try:
        result = subprocess.run(["/usr/bin/vcgencmd", "get_throttled"], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            throttled_str = result.stdout.strip().split("=")[1].strip()
            sensors["throttled"] = parse_throttled(throttled_str)
    except:
        pass
    
    return sensors


def parse_throttled(status: str) -> Dict[str, Any]:
    try:
        raw = int(status, 16)
        return {
            "raw": raw,
            "current_undervolt": bool(raw & 0x1),
            "current_throttled": bool(raw & 0x4),
            "current_soft_temp": bool(raw & 0x8),
            "current_arm_freq_capped": bool(raw & 0x2)
        }
    except:
        return {"raw": 0}


def _cpu_core_count() -> int:
    """Number of CPU cores; used to normalize ps %cpu (per-core) to system-wide 0-100%."""
    try:
        with open("/proc/cpuinfo", "r") as f:
            return sum(1 for line in f if line.strip().startswith("processor"))
    except Exception:
        return 1


def get_top_processes() -> List[Dict[str, Any]]:
    """Top processes by CPU. ps reports %cpu as percentage of one core; we normalize to system-wide 0-100%."""
    processes = []
    cores = max(1, _cpu_core_count())

    try:
        result = subprocess.run(["ps", "aux", "--sort=-%cpu"], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            for line in lines[:20]:
                parts = line.split(None, 10)
                if len(parts) >= 11:
                    try:
                        # ps %CPU = percentage of one core; normalize so 100% = all cores
                        raw_cpu = float(parts[2])
                        cpu_pct = min(100.0, round(raw_cpu / cores, 1))
                        processes.append({
                            "pid": int(parts[1]),
                            "name": parts[10][:50],
                            "cpu": cpu_pct,
                            "mem": round(float(parts[3]), 1)
                        })
                    except (ValueError, IndexError):
                        continue
    except Exception as e:
        print(f"Error: {e}")

    return processes


def get_tailscale_info() -> Dict[str, Any]:
    global TAILSCALE_CACHE, TAILSCALE_CACHE_TIME
    now = time.time()
    with TAILSCALE_CACHE_LOCK:
        if TAILSCALE_CACHE_TIME and (now - TAILSCALE_CACHE_TIME) < TAILSCALE_CACHE_TTL_SEC:
            return TAILSCALE_CACHE.copy()

    try:
        result = subprocess.run(["tailscale", "status", "--json"], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            status = json.loads(result.stdout)
            tailscale_ips = status.get("TailscaleIPs", [])
            ts_info = {
                "tailscale_connected": True,
                "tailscale_ip": tailscale_ips[0] if tailscale_ips else "-"
            }
            with TAILSCALE_CACHE_LOCK:
                TAILSCALE_CACHE = ts_info
                TAILSCALE_CACHE_TIME = now
            return ts_info
    except Exception as e:
        print(f"Error: {e}")

    with TAILSCALE_CACHE_LOCK:
        if TAILSCALE_CACHE_TIME:
            return TAILSCALE_CACHE.copy()

    return {"tailscale_connected": False, "tailscale_ip": "-"}


class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    os.chdir(DIRECTORY)
    server = ThreadingTCPServer(('0.0.0.0', PORT), MonitorHandler)
    
    print(f"Monitor started on port {PORT}")
    print(f"Local: http://127.0.0.1:{PORT}")
    print(f"Tailscale: https://agent.tail16521a.ts.net/monitor")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")


if __name__ == "__main__":
    main()

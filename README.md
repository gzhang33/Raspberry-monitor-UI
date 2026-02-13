# OpenClaw System Monitor

实时系统监控服务，提供 CPU、内存、磁盘、网络、进程和温度等指标的 Web 可视化。

## 功能特性

- ✅ **CPU 监控**：使用率、频率、温度、节流状态
- ✅ **内存监控**：RAM 和 Swap 使用情况
- ✅ **磁盘监控**：根分区使用率、读写速度
- ✅ **网络监控**：上传/下载速率、总流量、Speedtest 测速
- ✅ **进程监控**：Top 10 CPU/内存占用进程
- ✅ **系统概览**：OS 信息、运行时间、负载平均、IP 地址、Docker 状态
- ✅ **Tailscale 状态**：连接状态和 Tailscale IP
- ✅ **趋势图表**：CPU/内存/网络历史趋势（点击卡片切换）
- ✅ **实时刷新**：5 秒自动轮询，手动刷新支持
- ✅ **响应式设计**：支持桌面和移动端

---

## 启动

### 手动启动

```bash
cd /home/admin/monitor
python3 server.py
```

#### 方式 1: 用户级 systemd（推荐，无需 root）

```bash
cd /home/admin/monitor
./start.sh
```

用户级服务会在登录时自动启动。

控制命令：
```bash
# 启动/停止/重启/状态
systemctl --user {start|stop|restart|status} monitor
```

#### 方式 2: 系统级 systemd（需要 root，开机自启）

```bash
# 复制服务文件到系统 systemd
sudo cp /home/admin/monitor/monitor.service /etc/systemd/system/

# 重新加载 systemd
sudo systemctl daemon-reload

# 启用并启动服务（开机自启）
sudo systemctl enable monitor.service
sudo systemctl start monitor.service

# 查看状态
sudo systemctl status monitor.service
```

---

## 访问

- 本地：`http://127.0.0.1:10000`
- Tailscale：`https://agent.tail16521a.ts.net/monitor`

默认端口：`10000`（可通过 `MONITOR_PORT` 环境变量覆盖）

---

## API 端点

### 系统统计
- `GET /api/system-stats` - 完整系统指标

响应示例：
```json
{
  "overview": {
    "os": "Linux 6.12.62+rpt-rpi-v8",
    "uptime": "15d 4h 32m",
    "load_1": "0.45",
    "load_5": "0.52",
    "load_15": "0.48",
    "ip": "192.168.1.100",
    "docker": {"running": 3, "stopped": 1}
  },
  "cpu": {
    "percent": 12.3,
    "freq": 1200
  },
  "memory": {
    "percent": 45.6,
    "used_gb": 1.85,
    "total_gb": 4.00,
    "swap_percent": 0.0,
    "swap_total_gb": 2.00,
    "swap_used_gb": 0.00
  },
  "disk": {
    "percent": 67.2,
    "used_gb": 27.5,
    "total_gb": 40.9
  },
  "network": {
    "rx_mb_s": 0.125,
    "tx_mb_s": 0.032,
    "rx_total_gb": 125.4,
    "tx_total_gb": 32.1,
    "speedtest": {
      "ping_ms": 8.5,
      "download_mbps": 125.3,
      "upload_mbps": 45.2
    },
    "ping_ms": 8.5
  },
  "sensors": {
    "temp": 42.5,
    "voltage": 1.2,
    "throttled": {
      "raw": 0,
      "current_undervolt": false,
      "current_throttled": false,
      "current_soft_temp": false,
      "current_arm_freq_capped": false
    }
  },
  "processes": [
    {"pid": 1234, "name": "python3", "cpu": 5.2, "mem": 2.1},
    ...
  ],
  "tailscale": {
    "tailscale_connected": true,
    "tailscale_ip": "100.77.79.121"
  }
}
```

### Tailscale 信息
- `GET /api/tailscale-ip` - Tailscale 连接信息

响应示例：
```json
{
  "tailscale_connected": true,
  "tailscale_ip": "100.77.79.121"
}
```

### 健康检查
- `GET /api/health` - 服务健康状态

---

## 配置

### 环境变量

- `MONITOR_PORT` - 服务端口（默认：9999）
- `SPEEDTEST_INTERVAL_SEC` - Speedtest 执行间隔（默认：60 秒）
- `SPEEDTEST_CLI_PATH` - speedtest-cli 可执行文件路径

### Speedtest 配置

系统监控支持自动网络测速（使用 speedtest-cli）。如果已安装，服务器会定期运行测速并缓存结果。

安装 speedtest-cli：
```bash
python3 -m venv /tmp/speedtest-venv
/tmp/speedtest-venv/bin/pip install speedtest-cli
export SPEEDTEST_CLI_PATH=/tmp/speedtest-venv/bin/speedtest-cli
```

---

## 文件结构

```
monitor/
├── server.py         # 监控服务器
├── index.html        # 前端界面
└── README.md         # 本文档
```

---

## 依赖

监控服务器仅使用 Python 标准库，无需额外安装依赖。

### 系统命令依赖

- `top` - CPU 使用率
- `ps` - 进程列表
- `df` - 磁盘使用
- `vcgencmd` - Raspberry Pi 传感器（温度、电压、节流）
- `docker` - Docker 容器状态（可选）
- `tailscale` - Tailscale 状态（可选）
- `hostname` - 本地 IP
- `speedtest-cli` - 网络测速（可选）

---

## 性能优化

- **数据缓存**：系统统计数据缓存 2 秒，减少重复读取开销
- **网络速率计算**：使用 `/proc/net/dev` 读取字节计数器，计算增量速率
- **Speedtest 间隔**：默认 60 秒执行一次，避免频繁测速
- **前端轮询**：5 秒间隔，页面隐藏时自动暂停

---

## 注意事项

1. **Raspberry Pi 专用**：部分传感器（`vcgencmd`）仅适用于 Raspberry Pi
2. **网络测速**：需要安装 speedtest-cli，否则跳过测速功能
3. **Tailscale 集成**：需正确配置 Tailscale 客户端和权限
4. **端口配置**：确保防火墙允许 9999 端口访问

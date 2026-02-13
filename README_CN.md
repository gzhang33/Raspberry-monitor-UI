# Raspberry Monitor

[![PyPI version](https://badge.fury.io/py/raspberry-monitor.svg)](https://pypi.org/project/raspberry-monitor/)
[![Python](https://img.shields.io/pypi/pyversions/raspberry-monitor.svg)](https://pypi.org/project/raspberry-monitor/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

轻量级实时系统监控服务，专为 Raspberry Pi/Linux 系统设计。使用 Python 内置 `http.server`，**零外部依赖**。

[English Documentation](README.md)

## 功能特性

- **CPU 监控**：使用率、频率、温度、节流状态
- **内存监控**：RAM 和 Swap 使用情况
- **磁盘监控**：存储使用率、读写速度
- **网络监控**：上传/下载速率、总流量、Speedtest 测速
- **进程监控**：Top 10 CPU/内存占用进程
- **系统概览**：OS 信息、运行时间、负载平均、IP 地址、Docker 状态
- **Tailscale 状态**：连接状态和 Tailscale IP
- **趋势图表**：Canvas 历史趋势（点击卡片切换）
- **实时刷新**：5 秒自动轮询，页面隐藏时暂停
- **响应式设计**：GitHub 风格暗色主题，支持移动端

## 安装

### 从 PyPI 安装（推荐）

```bash
pip install raspberry-monitor
```

### 从源码安装

```bash
git clone https://github.com/raspberry-monitor/monitor.git
cd monitor
pip install -e .
```

## 快速开始

### 命令行启动

```bash
# 使用默认设置启动（端口 10000）
raspberry-monitor

# 或作为模块运行
python -m monitor
```

### 配置

环境变量：

| 变量 | 默认值 | 描述 |
|------|--------|------|
| `MONITOR_PORT` | 10000 | 服务端口 |
| `SPEEDTEST_INTERVAL_SEC` | 60 | Speedtest 间隔 |
| `SPEEDTEST_TIMEOUT_SEC` | 60 | Speedtest 超时 |
| `TAILSCALE_CACHE_TTL_SEC` | 15 | Tailscale 缓存 TTL |

## Systemd 服务配置

### 方式 1：用户级服务（推荐）

用户级服务在登录时自动启动，无需 root 权限。

```bash
# 运行安装脚本
./deployment/install.sh

# 手动设置（如需要）
mkdir -p ~/.config/systemd/user
cp deployment/monitor.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now monitor
```

**控制命令：**
```bash
systemctl --user start monitor      # 启动
systemctl --user stop monitor       # 停止
systemctl --user restart monitor    # 重启
systemctl --user status monitor     # 状态
journalctl --user -u monitor -f     # 查看日志
```

### 方式 2：系统级服务（开机自启）

系统级服务在开机时自动启动，无需用户登录。

```bash
# 复制服务文件到系统目录
sudo cp deployment/monitor.service /etc/systemd/system/

# 重新加载 systemd
sudo systemctl daemon-reload

# 启用并启动
sudo systemctl enable --now monitor

# 查看状态
sudo systemctl status monitor
```

**控制命令：**
```bash
sudo systemctl start monitor        # 启动
sudo systemctl stop monitor         # 停止
sudo systemctl restart monitor      # 重启
sudo systemctl status monitor       # 状态
sudo journalctl -u monitor -f       # 查看日志
```

### 自定义端口配置

编辑服务文件以更改端口：

```bash
# 用户级服务
nano ~/.config/systemd/user/monitor.service

# 系统级服务
sudo nano /etc/systemd/system/monitor.service
```

添加或修改 `Environment` 行：
```ini
[Service]
Environment=MONITOR_PORT=8080
```

然后重新加载并重启：
```bash
# 用户级
systemctl --user daemon-reload
systemctl --user restart monitor

# 系统级
sudo systemctl daemon-reload
sudo systemctl restart monitor
```

## API 端点

| 端点 | 描述 |
|------|------|
| `GET /` | 主仪表盘 |
| `GET /api/system-stats` | 完整系统指标 |
| `GET /api/tailscale-ip` | Tailscale 连接信息 |
| `GET /api/health` | 健康检查 |

### 响应示例

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

## 系统要求

### 必需
- Python 3.9+
- Linux（在 Raspberry Pi OS 上测试）

### 可选
- `vcgencmd` - Raspberry Pi 传感器（温度、电压、节流）
- `tailscale` - Tailscale 状态
- `speedtest-cli` - 网络测速
- `docker` - Docker 容器状态

## 项目结构

```
raspberry-monitor/
├── pyproject.toml              # 现代 Python 打包
├── README.md                   # 英文文档
├── README_CN.md               # 中文文档（本文件）
├── LICENSE                     # MIT 许可证
├── CHANGELOG.md               # 版本历史
├── CONTRIBUTING.md            # 贡献指南
│
├── src/monitor/               # 主包
│   ├── __init__.py            # 包入口
│   ├── __main__.py            # CLI 入口
│   ├── config.py              # 配置管理
│   ├── server.py              # HTTP 服务器
│   ├── cache.py               # TTL 缓存
│   ├── speedtest.py           # Speedtest 管理器
│   ├── collectors/            # 指标收集器
│   │   ├── cpu.py
│   │   ├── memory.py
│   │   ├── disk.py
│   │   ├── network.py
│   │   └── ...
│   ├── handlers/              # HTTP 处理器
│   └── static/                # 前端文件
│
├── tests/                     # 测试套件
├── deployment/                # 部署配置
│   ├── monitor.service        # Systemd 服务
│   └── install.sh             # 安装脚本
│
└── .github/                   # GitHub 配置
```

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码检查
ruff check src tests

# 类型检查
mypy src
```

## 性能优化

- **缓存**：系统统计缓存 2 秒，进程列表缓存 8 秒
- **网络速率**：使用 `/proc/net/dev` 计数器计算增量速率
- **Speedtest**：每 60 秒运行一次，避免网络开销
- **前端**：5 秒轮询，标签页隐藏时自动暂停

## 注意事项

1. **Raspberry Pi 专用**：部分传感器（`vcgencmd`）仅适用于 Raspberry Pi
2. **无认证**：目前为开放访问；公开暴露时建议添加认证
3. **零依赖**：仅使用 Python 标准库

## 贡献

查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解贡献指南。

## 许可证

MIT 许可证 - 详见 [LICENSE](LICENSE)。

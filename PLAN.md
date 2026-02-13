# Raspberry Monitor 重构计划

## 1. 当前项目分析

### 现有结构
```
monitor/
├── server.py           # 单文件后端 (~600行)
├── index.html          # 单文件前端
├── start.sh            # 启动脚本
├── monitor.service     # systemd服务
├── README.md           # 文档
├── CLAUDE.md           # Claude Code 指南
└── speedtest-venv/     # 虚拟环境 (应忽略)
```

### 优点
- 零外部依赖，仅使用Python标准库
- 单文件部署简单
- 功能完整：CPU、内存、磁盘、网络、进程、温度监控

### 需要改进
1. **结构扁平**：所有代码在单一文件中
2. **缺少现代打包配置**：无 pyproject.toml
3. **无测试框架**：缺少单元测试
4. **配置分散**：硬编码和环境变量混合
5. **日志简陋**：使用 print 而非 logging
6. **开源文档不全**：缺少 LICENSE、CONTRIBUTING 等

---

## 2. 目标项目结构

采用 Python 社区推荐的 **src/ 布局**：

```
raspberry-monitor/
├── pyproject.toml              # 现代 Python 打包配置
├── README.md                   # 英文文档
├── README_CN.md               # 中文文档
├── LICENSE                     # MIT License
├── CHANGELOG.md                # 版本变更记录
├── CONTRIBUTING.md             # 贡献指南
├── CODE_OF_CONDUCT.md          # 行为准则
├── .gitignore                  # Git 忽略规则
│
├── src/
│   └── monitor/               # 主包
│       ├── __init__.py         # 包入口，版本信息
│       ├── __main__.py         # python -m 入口
│       ├── config.py           # 配置管理
│       ├── server.py           # HTTP 服务器
│       ├── handlers/           # 请求处理器
│       │   ├── __init__.py
│       │   ├── system.py       # 系统统计 API
│       │   └── health.py       # 健康检查 API
│       ├── collectors/         # 数据收集器
│       │   ├── __init__.py
│       │   ├── cpu.py          # CPU 统计
│       │   ├── memory.py       # 内存统计
│       │   ├── disk.py         # 磁盘统计
│       │   ├── network.py      # 网络统计
│       │   ├── process.py      # 进程列表
│       │   ├── sensors.py      # 传感器 (温度/电压)
│       │   └── tailscale.py    # Tailscale 状态
│       ├── cache.py            # 缓存管理
│       ├── speedtest.py        # Speedtest 功能
│       └── static/             # 静态文件
│           └── index.html
│
├── tests/                      # 测试目录
│   ├── __init__.py
│   ├── conftest.py             # pytest fixtures
│   ├── test_config.py
│   ├── test_collectors/
│   │   ├── test_cpu.py
│   │   ├── test_memory.py
│   │   └── ...
│   └── test_handlers/
│       └── test_system.py
│
├── deployment/                 # 部署配置
│   ├── monitor.service         # systemd 服务
│   └── install.sh              # 安装脚本
│
└── .github/                    # GitHub 配置
    ├── workflows/
    │   ├── tests.yml           # CI 测试
    │   └── release.yml         # 自动发布
    ├── ISSUE_TEMPLATE/
    │   ├── bug_report.md
    │   └── feature_request.md
    └── PULL_REQUEST_TEMPLATE.md
```

---

## 3. 核心模块设计

### 3.1 配置管理 (config.py)

```python
from dataclasses import dataclass, field
from typing import Optional
import os

@dataclass
class Config:
    """Application configuration with environment variable support."""

    # Server settings
    port: int = field(default_factory=lambda: int(os.getenv("MONITOR_PORT", "10000")))
    host: str = "0.0.0.0"

    # Cache settings
    system_stats_ttl: float = 2.0
    process_list_ttl: float = 8.0
    tailscale_cache_ttl: float = 15.0

    # Speedtest settings
    speedtest_interval: float = field(default_factory=lambda: float(os.getenv("SPEEDTEST_INTERVAL_SEC", "60")))
    speedtest_timeout: float = field(default_factory=lambda: float(os.getenv("SPEEDTEST_TIMEOUT_SEC", "60")))
    speedtest_cli_path: str = "/usr/bin/speedtest"

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls()
```

### 3.2 数据收集器模式

每个收集器遵循统一接口：

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseCollector(ABC):
    """Base class for all metric collectors."""

    @abstractmethod
    def collect(self) -> Dict[str, Any]:
        """Collect and return metrics."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Collector name for logging."""
        pass
```

### 3.3 缓存管理器

```python
from dataclasses import dataclass
from typing import Dict, Any, Optional, Callable
import time
import threading

@dataclass
class CacheEntry:
    data: Dict[str, Any]
    timestamp: float

class CacheManager:
    """Thread-safe TTL cache for system metrics."""

    def __init__(self, default_ttl: float = 2.0):
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.Lock()
        self._default_ttl = default_ttl

    def get_or_compute(self, key: str, compute: Callable[[], Dict], ttl: Optional[float] = None) -> Dict:
        """Get cached value or compute and cache new value."""
        with self._lock:
            now = time.time()
            entry = self._cache.get(key)

            if entry and (now - entry.timestamp) < (ttl or self._default_ttl):
                return entry.data

            data = compute()
            self._cache[key] = CacheEntry(data, now)
            return data
```

---

## 4. pyproject.toml 配置

```toml
[build-system]
requires = ["setuptools >= 77.0.3", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "openclaw-monitor"
version = "1.0.0"
description = "Lightweight real-time system monitor for Raspberry Pi/Linux"
readme = "README.md"
license = "MIT"
license-files = ["LICENSE"]
requires-python = ">=3.9"
authors = [
    { name = "OpenClaw Team", email = "team@openclaw.dev" }
]
keywords = ["monitoring", "raspberry-pi", "system", "metrics", "dashboard"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Web Environment",
    "Intended Audience :: Developers",
    "Intended Audience :: System Administrators",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: System :: Monitoring",
]
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest >= 7.0",
    "pytest-cov >= 4.0",
    "ruff >= 0.1.0",
    "mypy >= 1.0",
]

[project.scripts]
openclaw-monitor = "openclaw_monitor.__main__:main"

[project.urls]
Homepage = "https://github.com/openclaw/monitor"
Documentation = "https://github.com/openclaw/monitor#readme"
Repository = "https://github.com/openclaw/monitor"
Issues = "https://github.com/openclaw/monitor/issues"

[tool.setuptools.packages.find]
where = ["src"]

[tool.ruff]
line-length = 100
target-version = "py39"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"

[tool.mypy]
python_version = "3.9"
strict = true
```

---

## 5. 实施步骤

### 阶段 1: 项目结构重组
- [ ] 创建 `src/openclaw_monitor/` 目录结构
- [ ] 移动 `index.html` 到 `src/openclaw_monitor/static/`
- [ ] 创建 `__init__.py` 和 `__main__.py`
- [ ] 创建 `pyproject.toml`

### 阶段 2: 代码模块化
- [ ] 提取配置到 `config.py`
- [ ] 创建 `collectors/` 模块，拆分各统计收集器
- [ ] 创建 `handlers/` 模块，拆分API处理器
- [ ] 提取缓存逻辑到 `cache.py`
- [ ] 提取 Speedtest 到 `speedtest.py`
- [ ] 重构服务器到 `server.py`

### 阶段 3: 测试框架
- [ ] 配置 pytest
- [ ] 添加单元测试
- [ ] 添加集成测试
- [ ] 配置测试覆盖率

### 阶段 4: 文档完善
- [ ] 创建 MIT LICENSE
- [ ] 编写 CONTRIBUTING.md
- [ ] 编写 CHANGELOG.md
- [ ] 添加 CODE_OF_CONDUCT.md
- [ ] 更新 README.md (英文版)

### 阶段 5: CI/CD
- [ ] 配置 GitHub Actions
- [ ] 添加代码检查 (ruff, mypy)
- [ ] 配置自动测试
- [ ] 配置 PyPI 自动发布

---

## 6. 参考资源

### Python 打包最佳实践
- [Packaging Python Projects](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
- [Python Project Structure: Why the 'src' Layout](https://medium.com/@adityaghadge99/python-project-structure-why-the-src-layout-beats-flat-folders-and-how-to-use-my-free-template-808844d16f35)
- [Structuring Your Project](https://docs.python-guide.org/writing/structure/)

### 监控项目参考
- [RPi-Monitor](https://pandorafms.com/blog/monitor-raspberry-pi-with-rpi-monitor/)
- [Raspberry Pi System Monitor Guide](https://www.sunfounder.com/blogs/news/raspberry-pi-system-monitor-guide-how-to-track-cpu-ram-temperature-and-services-with-monit)

### Web 框架对比
- [FastAPI vs Flask 2025](https://strapi.io/blog/fastapi-vs-flask-python-framework-comparison)
- [Flask vs FastAPI: Real-World Use Cases](https://softwarelogic.co/en/blog/flask-vs-fastapi-real-world-use-cases-and-best-practices/)

---

## 7. 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 保持零依赖 | 高 | 继续使用 stdlib only，不添加 psutil 等 |
| 功能回归 | 中 | 添加完整测试覆盖，保持 API 兼容 |
| 部署复杂度增加 | 中 | 提供 wheel 包，简化 pip install |
| 性能影响 | 低 | 模块化不影响运行时性能 |

---

## 8. 版本规划

- **v1.0.0** - 当前稳定版本 (重构前)
- **v2.0.0** - 模块化重构版本
  - 新的项目结构
  - pyproject.toml 支持
  - pip 可安装
  - 测试覆盖
- **v2.1.0** - CI/CD 和文档完善
- **v2.2.0** - 可选功能：认证、多语言支持

#!/bin/bash
# Raspberry Monitor Installation Script
# This script installs the package and sets up systemd service

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SERVICE_NAME="raspberry-monitor"

echo "🚀 Installing Raspberry Monitor..."

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Install the package
cd "$PROJECT_ROOT"
pip install --user .

echo ""
echo "📦 Package installed successfully"

# Setup systemd service
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
mkdir -p "$SYSTEMD_USER_DIR"

# Create user-level service file with expanded paths
cat > "$SYSTEMD_USER_DIR/${SERVICE_NAME}.service" << EOF
[Unit]
Description=Raspberry Monitor
After=network.target

[Service]
Type=simple
WorkingDirectory=$HOME
Environment=MONITOR_PORT=\${MONITOR_PORT:-10000}
Environment=SPEEDTEST_INTERVAL_SEC=\${SPEEDTEST_INTERVAL_SEC:-300}
Environment=SPEEDTEST_TIMEOUT_SEC=\${SPEEDTEST_TIMEOUT_SEC:-60}
Environment=PYTHONUNBUFFERED=1
ExecStart=$HOME/.local/bin/${SERVICE_NAME}
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
EOF

# Reload and enable
systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME.service"

echo ""
echo "✅ Service installed and enabled"
echo ""
echo "📍 Commands:"
echo "  Start:   systemctl --user start $SERVICE_NAME"
echo "  Stop:    systemctl --user stop $SERVICE_NAME"
echo "  Status:  systemctl --user status $SERVICE_NAME"
echo "  Restart: systemctl --user restart $SERVICE_NAME"
echo "  Logs:    journalctl --user -u $SERVICE_NAME -f"
echo ""
echo "🌐 Access the monitor at: http://localhost:\${MONITOR_PORT:-10000}"
echo ""
echo "⚠️  Note: User-level services auto-start on user login."
echo "   For boot-time startup (system-level), use:"
echo "   sudo cp $SCRIPT_DIR/monitor.service /etc/systemd/system/"
echo "   sudo systemctl enable --now $SERVICE_NAME"

#!/bin/bash
# OpenClaw System Monitor Startup Script
# This script sets up systemd service for auto-start on boot

set -e

SERVICE_NAME="monitor"
SERVICE_PORT="${MONITOR_PORT:-10000}"
SERVICE_FILE="$(dirname "$0")/monitor.service"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

echo "🚀 Setting up System Monitor auto-start..."

# Create user systemd directory
mkdir -p "$SYSTEMD_USER_DIR"

# Copy service file (using relative path for ExecStart)
cp "$SERVICE_FILE" "$SYSTEMD_USER_DIR/${SERVICE_NAME}.service"

# Reload systemd (user level)
systemctl --user daemon-reload

# Enable service (auto-start on login)
systemctl --user enable "$SERVICE_NAME.service"

echo "✅ Service installed and enabled"
echo ""
echo "📍 Commands:"
echo "  Start:   systemctl --user start $SERVICE_NAME"
echo "  Stop:    systemctl --user stop $SERVICE_NAME"
echo "  Status:  systemctl --user status $SERVICE_NAME"
echo "  Restart: systemctl --user restart $SERVICE_NAME"
echo ""
echo "⚠️  Note: User-level services auto-start on user login (login session)"
echo "   For boot-time startup, see README.md for root-level systemd setup"

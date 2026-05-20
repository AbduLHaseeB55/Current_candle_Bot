#!/bin/bash
# ========================================
# LINUX/UBUNTU DEPLOYMENT SCRIPT
# Sets up bot as systemd service
# ========================================

set -e

echo "========================================"
echo "TRADING BOT - LINUX DEPLOYMENT"
echo "========================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "[ERROR] Please run as root (use sudo)"
    exit 1
fi

# Get actual username
ACTUAL_USER=${SUDO_USER:-$USER}
echo "[INFO] Deploying for user: $ACTUAL_USER"

# Get bot directory
BOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "[INFO] Bot directory: $BOT_DIR"

# Check venv exists
if [ ! -d "$BOT_DIR/venv" ]; then
    echo "[ERROR] Virtual environment not found!"
    echo "Run: python3 -m venv venv"
    exit 1
fi

# Check .env exists
if [ ! -f "$BOT_DIR/.env" ]; then
    echo "[ERROR] .env file missing!"
    echo "Copy .env.template and configure it"
    exit 1
fi

# Create systemd service file
SERVICE_FILE="/etc/systemd/system/trading-bot.service"
echo "[1/5] Creating systemd service..."

cat > $SERVICE_FILE <<EOF
[Unit]
Description=Current Candle Trading Bot
After=network.target

[Service]
Type=simple
User=$ACTUAL_USER
WorkingDirectory=$BOT_DIR
Environment="PATH=$BOT_DIR/venv/bin"
ExecStart=$BOT_DIR/venv/bin/python run_bot.py
Restart=always
RestartSec=10
StandardOutput=append:$BOT_DIR/logs/bot.log
StandardError=append:$BOT_DIR/logs/bot_error.log

[Install]
WantedBy=multi-user.target
EOF

echo "[2/5] Reloading systemd..."
systemctl daemon-reload

echo "[3/5] Enabling service..."
systemctl enable trading-bot

echo "[4/5] Starting service..."
systemctl start trading-bot

echo "[5/5] Checking status..."
sleep 2
systemctl status trading-bot --no-pager

echo ""
echo "========================================"
echo "DEPLOYMENT COMPLETE!"
echo "========================================"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status trading-bot   # Check status"
echo "  sudo systemctl stop trading-bot     # Stop bot"
echo "  sudo systemctl start trading-bot    # Start bot"
echo "  sudo systemctl restart trading-bot  # Restart bot"
echo "  sudo journalctl -u trading-bot -f   # View logs"
echo "  tail -f $BOT_DIR/logs/inference.log # View bot logs"
echo ""

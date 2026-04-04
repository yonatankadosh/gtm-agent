#!/bin/bash
# Run THIS script ON THE GCP VM (after SSH), not on your Mac.
# Restarts the Telegram bot and reinstalls Python deps from ~/gtm-agent/requirements.txt
#
# Usage (on VM):
#   chmod +x ~/gtm-agent/tools/vm-restart-bot.sh   # once
#   bash ~/gtm-agent/tools/vm-restart-bot.sh

set -e
ROOT="${HOME}/gtm-agent"
cd "$ROOT"

echo "Installing deps from ${ROOT}/requirements.txt ..."
pip3 install -q -r requirements.txt

if systemctl is-active --quiet gtm-bot 2>/dev/null; then
  echo "Restarting gtm-bot service..."
  sudo systemctl restart gtm-bot
  sudo systemctl status gtm-bot --no-pager || true
else
  echo "No systemd unit 'gtm-bot'. Run the bot manually:"
  echo "  python3 ${ROOT}/tools/telegram-bot.py"
fi

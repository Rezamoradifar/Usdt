#!/usr/bin/env bash
set -euo pipefail
if [ "$(id -u)" -ne 0 ]; then echo 'Run: sudo bash install.sh'; exit 1; fi
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
command -v systemctl >/dev/null || { echo 'systemd required'; exit 1; }
command -v python3 >/dev/null || { apt-get update; apt-get install -y python3; }
id usdti-monitor >/dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin usdti-monitor
install -d -m 755 /opt/usdti-monitor
install -m 644 monitor.py /opt/usdti-monitor/monitor.py
install -d -o usdti-monitor -g usdti-monitor -m 750 /var/lib/usdti-monitor
if [ ! -f /etc/usdti-monitor.env ]; then
  install -m 600 /dev/null /etc/usdti-monitor.env
  cat > /etc/usdti-monitor.env <<'ENV'
TRONGRID_API_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
DB_PATH=/var/lib/usdti-monitor/events.sqlite3
ENV
fi
cat > /etc/systemd/system/usdti-monitor.service <<'UNIT'
[Unit]
Description=Read-only USDTI transfer monitor
Wants=network-online.target
After=network-online.target
[Service]
User=usdti-monitor
Group=usdti-monitor
EnvironmentFile=/etc/usdti-monitor.env
ExecStart=/usr/bin/python3 /opt/usdti-monitor/monitor.py
Restart=on-failure
RestartSec=10
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/usdti-monitor
UMask=0077
[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now usdti-monitor
systemctl restart usdti-monitor
echo 'Installed. Logs: journalctl -u usdti-monitor -f'
echo 'Optional configuration: sudo nano /etc/usdti-monitor.env'

#!/usr/bin/env bash
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo 'Run sudo bash install-dashboard.sh'; exit 1; }
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
[ -f dist/client/index.html ] || { echo 'Build missing: run npm ci && npm run build first'; exit 1; }
command -v python3 >/dev/null || { apt-get update; apt-get install -y python3; }
id usdti-dashboard >/dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin usdti-dashboard
install -d -m 755 /opt/usdti-dashboard/dist
install -m 644 api.py /opt/usdti-dashboard/api.py
cp -R dist/client /opt/usdti-dashboard/dist/
chmod -R a+rX /opt/usdti-dashboard/dist
if [ ! -f /etc/usdti-dashboard.env ]; then
  install -m 600 /dev/null /etc/usdti-dashboard.env
  echo 'TRONGRID_API_KEY=' > /etc/usdti-dashboard.env
fi
cat > /etc/systemd/system/usdti-dashboard.service <<'UNIT'
[Unit]
Description=USDTI independent read-only dashboard
After=network-online.target
Wants=network-online.target
[Service]
User=usdti-dashboard
Group=usdti-dashboard
EnvironmentFile=/etc/usdti-dashboard.env
ExecStart=/usr/bin/python3 /opt/usdti-dashboard/api.py --host 0.0.0.0 --port 8080
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable usdti-dashboard
systemctl restart usdti-dashboard
echo 'Dashboard started on port 8080. Add your domain and HTTPS reverse proxy for public deployment.'

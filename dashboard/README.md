# USDTI independent dashboard

Responsive React dashboard inspired by the supplied layout, with independent branding and real read-only TRON data. No TRONSCAN affiliation, verification badge, invented price, or fabricated activity.

## Ubuntu installation

From the repository root:

```bash
cd dashboard
sudo bash install-dashboard.sh
```

Prebuilt client assets are included: Node.js is not required on the server. Opens HTTP port 8080 using a restricted systemd service. Does not change firewall, DNS, existing nginx, or TLS configuration. For internet production, put it behind your existing HTTPS reverse proxy. The standard-library HTTP host is intended for a small dashboard; apply reverse-proxy limits for public traffic.

Configure your TronGrid API key on the server only:

```bash
sudo nano /etc/usdti-dashboard.env
sudo systemctl restart usdti-dashboard
sudo systemctl status usdti-dashboard --no-pager
```

Set `TRONGRID_API_KEY=...`. Do not put API keys in frontend code or GitHub. The existing monitor and dashboard use separate settings. There is no wallet connection and no signing.

## Data coverage

- Fixed contract: `TRpMNouAARgEA5KjtRjbb6f3n1FvmLoL4x`.
- Project label USDTI / USD Token is user-supplied, not independently verified.
- Latest 200 confirmed Transfer events from TronGrid; sampled counts are not lifetime totals.
- A 24-hour histogram uses only this sample. If more than 200 events occurred, it is incomplete.
- `decimals()` and `totalSupply()` are read from solidified state using constant calls every five minutes. Values stay unavailable if the calls fail.
- Price, circulating supply, total holders, market capitalization, and trading volume are not claimed.
- Refresh every 30 seconds. Provider errors produce an unavailable or stale state; stale data is explicitly labeled.
- CSV exports use raw integer units. Addresses returned as hex are converted to TRON Base58Check.
- Fixed upstream endpoints and cache isolate server credentials from browser clients. No user-controlled proxy URL.

## Development

Node 20.19+ or 22.12+ and Python 3.10+:

```bash
npm ci
npm run dev -- --host 0.0.0.0 --port 4173
```

```bash
python3 -m unittest -v test_api.py
npm run build
```

Built assets are in `dist/client`. The Sites starter runtime remains included, but its static worker does not run `api.py`; use the Ubuntu installation for the integrated API. A Sites deployment requires a separate API integration.

Live check in this session: provider returned one confirmed event, decimals 6, and raw totalSupply 10000000000000000. This is a point-in-time check, not a promise of ongoing provider availability.

Source docs: https://developers.tron.network/reference/get-events-by-contract-address and https://developers.tron.network/reference/triggerconstantcontract-1

# USDTI Transfer Monitor

Read-only confirmed TRC-20 Transfer event monitor for Ubuntu/systemd. No trading, wallet signing, volume generation, or artificial holders.

Contract: `TRpMNouAARgEA5KjtRjbb6f3n1FvmLoL4x` (user supplied; metadata not independently verified).

## Install

```bash
git clone https://github.com/Rezamoradifar/Usdt.git
cd Usdt
sudo bash install.sh
```

Configure optional TronGrid API key and Telegram credentials locally in `/etc/usdti-monitor.env`, then restart `usdti-monitor`. Never commit credentials.

```bash
sudo nano /etc/usdti-monitor.env
sudo systemctl restart usdti-monitor
sudo journalctl -u usdti-monitor -f
```

Python standard library only. Runs as a restricted service account. Stores events in SQLite. Starts five minutes before first launch, not full historical sync. Raw token units only. Telegram delivery is at-least-once; a crash can duplicate a notification. Late indexing beyond the five-minute overlap can miss events. No total-holder or trading-volume calculation.

## Tests

```bash
python3 -m unittest -v test_monitor.py
```

Three mocked tests cover pagination/deduplication and error checkpoint handling. Live API and server deployment have not been verified. See README-FA.txt for Persian instructions.

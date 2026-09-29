#!/usr/bin/env python3
"""Read-only confirmed TRC20 Transfer monitor. No signing or trading."""
import json, os, sqlite3, time, urllib.request, urllib.parse, urllib.error, logging
CONTRACT = 'TRpMNouAARgEA5KjtRjbb6f3n1FvmLoL4x'
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def request_json(url, headers=None, body=None):
    req = urllib.request.Request(url, data=body, headers=headers or {})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)

def init_db(path):
    db = sqlite3.connect(path)
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('CREATE TABLE IF NOT EXISTS state (k TEXT PRIMARY KEY, v TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS events (tx TEXT, idx INTEGER, ts INTEGER, payload TEXT, notified INTEGER DEFAULT 0, PRIMARY KEY(tx,idx))')
    with db:
        db.execute('INSERT OR IGNORE INTO state VALUES (?,?)', ('cursor', str(int(time.time()*1000)-300000)))
    return db

def scan(db, fetch=request_json):
    start = int(db.execute("SELECT v FROM state WHERE k='cursor'").fetchone()[0])
    end = int(time.time()*1000)-60000
    if end < start:
        return
    params = dict(event_name='Transfer', only_confirmed='true', limit=200,
                  order_by='block_timestamp,asc', min_timestamp=max(0,start-300000), max_timestamp=end)
    headers = {'accept':'application/json'}
    if os.getenv('TRONGRID_API_KEY'):
        headers['TRON-PRO-API-KEY'] = os.environ['TRONGRID_API_KEY']
    seen = set()
    while True:
        url = 'https://api.trongrid.io/v1/contracts/'+CONTRACT+'/events?'+urllib.parse.urlencode(params)
        page = fetch(url, headers)
        if page.get('success') is not True or not isinstance(page.get('data'), list):
            raise ValueError('Invalid API response')
        with db:
            for event in page['data']:
                if event.get('_unconfirmed') is True:
                    raise ValueError('Unconfirmed event in confirmed response')
                tx, idx, ts = event['transaction_id'], int(event['event_index']), int(event['block_timestamp'])
                row = db.execute('INSERT OR IGNORE INTO events(tx,idx,ts,payload) VALUES (?,?,?,?)',
                                 (tx,idx,ts,json.dumps(event)))
                if row.rowcount:
                    logging.info('Transfer recorded tx=%s event=%s',tx,idx)
        fingerprint = page.get('meta',{}).get('fingerprint')
        if not fingerprint:
            break
        if fingerprint in seen:
            raise ValueError('Repeated pagination cursor')
        seen.add(fingerprint)
        params['fingerprint'] = fingerprint
    with db:
        db.execute("UPDATE state SET v=? WHERE k='cursor'", (str(end),))
    logging.info('Scan complete through timestamp=%s',end)

def notify(db):
    token, chat = os.getenv('TELEGRAM_BOT_TOKEN'), os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat:
        return
    for tx,idx,payload in db.execute('SELECT tx,idx,payload FROM events WHERE notified=0 ORDER BY ts LIMIT 20').fetchall():
        event = json.loads(payload)
        r = event.get('result',{})
        message = ('Confirmed token Transfer\nContract: '+CONTRACT+'\nTx: '+tx+
                   '\nFrom: '+str(r.get('from',r.get('_from','unknown')))+
                   '\nTo: '+str(r.get('to',r.get('_to','unknown')))+
                   '\nRaw units: '+str(r.get('value',r.get('_value','unknown'))))
        body = urllib.parse.urlencode({'chat_id':chat,'text':message}).encode()
        response = request_json('https://api.telegram.org/bot'+token+'/sendMessage', body=body)
        if not response.get('ok'):
            raise ValueError('Telegram rejected notification')
        with db:
            db.execute('UPDATE events SET notified=1 WHERE tx=? AND idx=?',(tx,idx))
        time.sleep(1)

def main():
    db = init_db(os.getenv('DB_PATH','/var/lib/usdti-monitor/events.sqlite3'))
    delay = 30
    while True:
        try:
            scan(db)
            notify(db)
            delay = 30
        except urllib.error.HTTPError as e:
            logging.error('HTTP status %s; retrying without advancing incomplete scan',e.code)
            delay = min(delay*2,300)
        except Exception as e:
            # Do not log exception URLs; they can contain Telegram tokens.
            logging.error('Operation failed (%s); retrying',type(e).__name__)
            delay = min(delay*2,300)
        time.sleep(delay)

if __name__ == '__main__':
    main()

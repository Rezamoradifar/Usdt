"""Fixed-contract read-only API and static dashboard host. No credentials in responses."""
import os,json,time,threading,urllib.request,urllib.parse,hashlib,argparse
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
CONTRACT='TRpMNouAARgEA5KjtRjbb6f3n1FvmLoL4x'
state={'contract':CONTRACT,'events':None,'decimals':None,'totalSupply':None,'updatedAt':None,'status':'loading','metadataAt':None}
lock=threading.Lock()

def rpc(path,body=None):
    headers={'Accept':'application/json'}
    if os.getenv('TRONGRID_API_KEY'): headers['TRON-PRO-API-KEY']=os.environ['TRONGRID_API_KEY']
    if body is not None: headers['Content-Type']='application/json'
    request=urllib.request.Request('https://api.trongrid.io'+path,headers=headers,data=json.dumps(body).encode() if body is not None else None)
    with urllib.request.urlopen(request,timeout=15) as response: return json.load(response)

def uint_call(selector):
    data=rpc('/walletsolidity/triggerconstantcontract',{'owner_address':CONTRACT,'contract_address':CONTRACT,'function_selector':selector,'visible':True})
    if data.get('result',{}).get('result') is not True: raise ValueError('constant call failed')
    raw=data['constant_result'][0]
    if len(raw)!=64: raise ValueError('invalid uint256')
    return int(raw,16)

def address(raw):
    if not isinstance(raw,str): return 'Unknown'
    if raw.startswith('T') and len(raw)==34: return raw
    h=raw.removeprefix('0x')
    if len(h)==40: h='41'+h
    if len(h)!=42 or not h.startswith('41'): return raw
    try: b=bytes.fromhex(h)
    except ValueError: return raw
    data=b+hashlib.sha256(hashlib.sha256(b).digest()).digest()[:4]
    n=int.from_bytes(data,'big'); result=''; alphabet='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    while n: n,r=divmod(n,58); result=alphabet[r]+result
    return result

def normalize(e):
    r=e.get('result',{})
    return {'tx':str(e['transaction_id']),'index':int(e['event_index']),'timestamp':int(e['block_timestamp']),'block':int(e['block_number']), 'from':address(r.get('from',r.get('_from'))),'to':address(r.get('to',r.get('_to'))),'value':str(r.get('value',r.get('_value','')))}

last_meta=0
def refresh_once():
    global last_meta
    try:
        data=rpc('/v1/contracts/'+CONTRACT+'/events?'+urllib.parse.urlencode({'event_name':'Transfer','only_confirmed':'true','order_by':'block_timestamp,desc','limit':200}))
        if data.get('success') is not True or not isinstance(data.get('data'),list): raise ValueError('events failed')
        if any(e.get('_unconfirmed') is True for e in data['data']): raise ValueError('unconfirmed response')
        events=[normalize(e) for e in data['data']]
        with lock: state.update(events=events,updatedAt=int(time.time()*1000),status='live')
    except Exception:
        with lock: state['status']='stale' if state['updatedAt'] else 'unavailable'
    if time.time()-last_meta>300:
        last_meta=time.time()
        try:
            decimals=uint_call('decimals()'); supply=uint_call('totalSupply()')
            if not 0<=decimals<=255: raise ValueError('decimals')
            with lock: state.update(decimals=decimals,totalSupply=str(supply),metadataAt=int(time.time()*1000))
        except Exception:
            with lock: state.update(decimals=None,totalSupply=None,metadataAt=None)

def refresh():
    while True:
        refresh_once()
        time.sleep(30)

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(Path(__file__).parent/'dist/client'),**kwargs)
    def do_GET(self):
        if self.path.split('?')[0]=='/api/token':
            with lock: payload=json.dumps(state).encode()
            self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(payload))); self.end_headers(); self.wfile.write(payload)
        elif self.path.split('?')[0] in ['/','/index.html'] or self.path.startswith('/assets/'):
            super().do_GET()
        else: self.send_error(404)
    def end_headers(self):
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',"default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
        super().end_headers()
    def log_message(self,*args): pass

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--port',type=int,default=8787); p.add_argument('--host',default='127.0.0.1'); p.add_argument('--snapshot',action='store_true'); a=p.parse_args()
    if a.snapshot:
        refresh_once(); print(json.dumps(state)); raise SystemExit(0)
    threading.Thread(target=refresh,daemon=True).start()
    ThreadingHTTPServer((a.host,a.port),Handler).serve_forever()

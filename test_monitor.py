import unittest
import monitor

class MonitorTests(unittest.TestCase):
    def event(self, idx):
        return {'transaction_id':'a'*64,'event_index':idx,'block_timestamp':1,'result':{'value':'123'}}
    def test_pagination_and_duplicates(self):
        db=monitor.init_db(':memory:')
        calls=[]
        def fetch(url,headers):
            calls.append(url)
            if 'fingerprint=' not in url:
                return {'success':True,'data':[self.event(0)],'meta':{'fingerprint':'next'}}
            return {'success':True,'data':[self.event(1)],'meta':{}}
        monitor.scan(db,fetch)
        monitor.scan(db,fetch)
        self.assertEqual(db.execute('SELECT COUNT(*) FROM events').fetchone()[0],2)
        self.assertIn('only_confirmed=true',calls[0])
        self.assertIn('fingerprint=next',calls[1])
    def test_failed_page_keeps_cursor(self):
        db=monitor.init_db(':memory:')
        old=db.execute('SELECT v FROM state').fetchone()[0]
        def fetch(url,headers):
            if 'fingerprint=' in url:
                raise OSError('offline')
            return {'success':True,'data':[self.event(0)],'meta':{'fingerprint':'next'}}
        with self.assertRaises(OSError): monitor.scan(db,fetch)
        self.assertEqual(db.execute('SELECT v FROM state').fetchone()[0],old)
    def test_unsuccessful_response(self):
        db=monitor.init_db(':memory:')
        with self.assertRaises(ValueError):
            monitor.scan(db,lambda *args:{'success':False,'data':[]})

if __name__=='__main__': unittest.main()

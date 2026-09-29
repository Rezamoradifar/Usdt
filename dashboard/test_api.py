import unittest
from unittest.mock import patch
import api
class ApiTests(unittest.TestCase):
 def test_zero_address(self):
  self.assertEqual(api.address('0x'+'00'*20),'T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb')
 def test_uint_exact(self):
  n=10**30
  with patch.object(api,'rpc',return_value={'result':{'result':True},'constant_result':[format(n,'064x')]}):
   self.assertEqual(api.uint_call('totalSupply()'),n)
 def test_reject_failed_call(self):
  with patch.object(api,'rpc',return_value={'result':{'result':False},'constant_result':['0'*64]}):
   with self.assertRaises(ValueError): api.uint_call('decimals()')
 def test_event_no_precision_loss(self):
  e={'transaction_id':'a'*64,'event_index':0,'block_timestamp':10,'block_number':20,'result':{'value':str(10**30),'from':api.CONTRACT,'to':api.CONTRACT}}
  self.assertEqual(api.normalize(e)['value'],str(10**30))
if __name__=='__main__':unittest.main()

from gdax.order_book import OrderBook
import sys
import time
import datetime as dt

from gdax.public_client import PublicClient
import gdax
import json
import decimal
from Queue import Queue


if __name__ == '__main__':
	
	
	class Spread(OrderBook):

		def __init__(self, product_id = ''):
			super(Spread, self).__init__(product_id=product_id)

			self._bid = None
			self._ask = None
			self._bidDepth = None
			self._askDepth = None
			
		def on_message(self, message):
			super(Spread, self).on_message(message)
			
			bid = self.get_bid()
			bidDepth = sum([b['size'] for b in self.get_bids(bid)])
			ask = self.get_ask()
			askDepth = sum([a['size'] for a in self.get_asks(ask)])

			if self._bid == bid and self._ask == ask and self._bidDepth == bidDepth and self._askDepth == askDepth:
                		#no changes to spread so do nothing
                		pass
            		else:
                		# update cache
                		self._bid = bid
                		self._ask = ask
                		self._bidDepth = bidDepth
                		self._askDepth = askDepth
                		print('{} {} bid: {:.3f} @ {:.2f}\task: {:.3f} @ {:.2f}'.format(
                    			dt.datetime.now(), self.product_id, bidDepth, bid, askDepth, ask))
				
				q.put({"product":self.product_id, "bid":(self._bid, self._bidDepth), "ask":(self._ask, self._askDepth)})
			 
	q = Queue(maxsize=0)
	num_threads = 3	


	ethusd = Spread('ETH-USD')
	ethbtc = Spread('ETH-BTC')
	btcusd = Spread('BTC-USD')
	
	#wait 5 seconds when starting threads due to websocket rate limit
	ethusd.start()
	time.sleep(5)
	
	ethbtc.start()
	time.sleep(5)
	
	btcusd.start()
	time.sleep(5)
	
	#load json with api connection details
	with open('./config/live.json', 'r') as f:
		config = json.load(f)
	
	#connect to the authenticated client
	auth_client = gdax.AuthenticatedClient(config["apiKey"], config['apiSecret'], config['apiPassphrase'], api_url="https://api.gdax.com")
	
	#store tuple (price,size)
	bids = {"BTC-USD": None, "ETH-BTC": None, "ETH-USD": None} 
	asks = {"BTC-USD": None, "ETH-BTC": None, "ETH-USD": None}
	while True:
		try:
			#if bids['BTC-USD'] is not None and bids['ETH-BTC'] is not None and bids['ETH-USD'] is not None:
			#	pnl = bids['BTC-USD'][0] * bids['ETH-BTC'][0] - bids['ETH-USD'][0]
			#pnl = btcusd._bid * ethbtc._bid - ethusd._ask
			last_update = q.get()
			bids[last_update['product']] = last_update['bid']
			asks[last_update['product']] = last_update['ask']
			if bids['BTC-USD'] is not None and bids['ETH-BTC'] is not None and asks['ETH-USD'] is not None:
                                pnl = bids['BTC-USD'][0] * bids['ETH-BTC'][0] - asks['ETH-USD'][0]
                        #pnl = btcusd._bid * ethbtc._bid - ethusd._ask
			if pnl is not None:
				print "PNL: ",pnl

		
			
			#entry conditions
			if pnl is not None and pnl > 0:
				
				order1_id = auth_client.buy(price=str(ethusd._ask), size='.01', product_id = 'ETH-USD')
				print order1_id
				#might be able to do this with the websocket for faster response
				eth_balance = 0
				while eth_balance == 0:
					eth_balance = auth_client.get_position()["accounts"]["ETH"]["balance"]
					print eth_balance
				order2_id = auth_client.sell(price=str(ethbtc._bid), size=eth_balance, product_id='ETH-BTC')
				btc_balance = 0
				while btc_balance == 0:
					btc_balance = auth_client.get_position()["accounts"]["BTC"]["balance"]
					print btc_balance
				order3_id = auth_client.sell(price=str(btcusd._bid), size = btc_balance, product_id='BTC-USD')
				#sleep while testing to avoid opening a ton of trades
				time.sleep(60)
				
		
		#except (KeyboardInterrupt, SystemExit):
		#	ethusd.close()
		#	ethbtc.close()
		#	btcusd.close()
		
		except Exception as e:
			print e 	
		'''

		if ethusd.error or ethbtc.error or btcusd.error:
			sys.exit(1)
		else:
			sys.exit(0)
		'''
	ethusd.close()
	ethbtc.close()
	btcusd.close()

	#to avoid fees
	#def maker(bids, asks):	

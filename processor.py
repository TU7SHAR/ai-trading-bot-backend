import asyncio
import pytz
from datetime import datetime, time
from database import upsert_market_data
from kotak_client import get_client
from config import Config

def is_market_open():
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    if now.weekday() > 4: return False
    return time(9, 15) <= now.time() <= time(15, 30)

class MarketProcessor:
    def __init__(self):
        self.queue = asyncio.PriorityQueue()
        self.client = get_client()
        self.is_running = True

    async def add_request(self, symbol, priority=2):
        await self.queue.put((priority, symbol))

   async def process_loop(self):
        print("🚀 Market Processor Engine Started...")
        
        while self.is_running:
            if not is_market_open():
                print("💤 Market is closed. Sleeping...")
                await asyncio.sleep(300) 
                continue

            priority, symbol = await self.queue.get()
            
            try:
                # 1. Determine Segment (VIX is an index)
                segment = 'nse_indices' if symbol == Config.VIX_SYMBOL else 'nse_cm'
                
                # 2. Fetch from Kotak Neo
                scrip = self.client.search_scrip(exchange=Config.DEFAULT_EXCHANGE, symbol=symbol)
                token = scrip[0]['instrument_token']
                
                quote = self.client.quotes(
                    instrument_tokens=[{'instrument_token': token, 'exchange_segment': segment}],
                    quote_type='ltp'
                )
                
                price = float(quote['message'][0]['last_traded_price'])
                
                # 3. Update Neon Database
                await self.update_db_price(symbol, price)
                
                # If VIX is high (>20), you might want to print a warning
                status = "⚠️ VOLATILE" if symbol == Config.VIX_SYMBOL and price > 20 else "✅ STABLE"
                print(f"[{status}] {symbol}: {price}")

            except Exception as e:
                print(f"⚠️ Error processing {symbol}: {e}")

            # Re-queue VIX so it stays in the loop
            if symbol == Config.VIX_SYMBOL:
                await self.add_request(symbol, priority=2)

            wait_time = 0.2 if priority == 1 else 2.0 
            await asyncio.sleep(wait_time)
            self.queue.task_done()
            
market_processor = MarketProcessor()
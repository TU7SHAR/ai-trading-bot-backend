import asyncio
import pytz
from datetime import datetime, time
from database import SessionLocal, PriceHistory
from kotak_client import get_client
from config import Config
from sqlalchemy.dialects.postgresql import insert

def is_market_open():
    """Checks if the Indian Stock Market is currently trading."""
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    
    # Saturday (5) and Sunday (6) are closed
    if now.weekday() > 4:
        return False
        
    start_time = time(9, 15)
    end_time = time(15, 30)
    
    return start_time <= now.time() <= end_time

class MarketProcessor:
    def __init__(self):
        self.queue = asyncio.PriorityQueue()
        self.client = get_client()
        self.is_running = True

    async def add_request(self, symbol, priority=2):
        """
        Priority 1 = Live User/AI Request (High)
        Priority 2 = Idle Background Tracking (Low)
        """
        await self.queue.put((priority, symbol))

    async def update_db_price(self, symbol, price):
        """Uses PostgreSQL Upsert to save space on Neon Free Tier."""
        db = SessionLocal()
        try:
            # This avoids creating 1000s of rows; it just updates the existing symbol
            stmt = insert(PriceHistory).values(
                symbol=symbol,
                price=price,
                timestamp=datetime.utcnow()
            )
            # If symbol exists, update price and time
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=['symbol'],
                set_=dict(price=price, timestamp=datetime.utcnow())
            )
            db.execute(upsert_stmt)
            db.commit()
        except Exception as e:
            print(f"DB Error: {e}")
        finally:
            db.close()

    async def process_loop(self):
        print("🚀 Market Processor Engine Started...")
        
        while self.is_running:
            # 1. Check if we should be working
            if not is_market_open():
                # If market is closed, clear queue or just sleep long
                # We check every 5 minutes during off-hours to save Neon Compute
                print("💤 Market is closed. Sleeping for 5 minutes...")
                await asyncio.sleep(300) 
                continue

            # 2. Get the next symbol (Priority 1 goes first)
            priority, symbol = await self.queue.get()
            
            try:
                # 3. Fetch from Kotak Neo
                # In production, cache tokens in a dict to avoid calling search_scrip every time
                scrip = self.client.search_scrip(exchange=Config.DEFAULT_EXCHANGE, symbol=symbol)
                token = scrip[0]['instrument_token']
                
                quote = self.client.quotes(
                    instrument_tokens=[{'instrument_token': token, 'exchange_segment': 'nse_cm'}],
                    quote_type='ltp'
                )
                
                price = float(quote['message'][0]['last_traded_price'])
                
                # 4. Update Neon Database
                await self.update_db_price(symbol, price)
                
                status = "🔥 LIVE" if priority == 1 else "⏳ IDLE"
                print(f"[{status}] {symbol}: ₹{price}")

            except Exception as e:
                print(f"⚠️ Error processing {symbol}: {e}")

            # 5. Rate Limiting (Protects your API key)
            # Live requests go fast; Idle requests wait 2 seconds to stay under limits
            wait_time = 0.2 if priority == 1 else 2.0 
            await asyncio.sleep(wait_time)
            
            self.queue.task_done()

# Global instance
market_processor = MarketProcessor()
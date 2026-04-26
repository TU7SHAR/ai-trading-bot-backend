from fastapi import FastAPI
from contextlib import asynccontextmanager
from processor import market_processor
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start background task
    task = asyncio.create_task(market_processor.process_loop())
  await market_processor.add_request(Config.VIX_SYMBOL, priority=2)    await market_processor.add_request("TATSILV", priority=2)
    await market_processor.add_request("SILVERBEES", priority=2)
    yield
    # Shutdown: Stop loop
    market_processor.is_running = False
    await task

app = FastAPI(lifespan=lifespan)

@app.get("/track/{symbol}")
async def track_stock_live(symbol: str):
    await market_processor.add_request(symbol.upper(), priority=1)
    return {"status": "Priority tracking started", "symbol": symbol}

@app.get("/brain/analyze/{symbol}")
async def analyze_stock(symbol: str):
    # This triggers an immediate sentiment check
    from brain import fingpt
    # In a real scenario, you'd fetch news here. 
    # For now, we analyze the 'vibe' or latest headline
    sentiment = fingpt.get_sentiment(f"Latest market movement for {symbol}")
    
    decision = "BUY" if sentiment > 0.3 else "SELL" if sentiment < -0.3 else "HOLD"
    return {
        "symbol": symbol,
        "sentiment_score": sentiment,
        "recommendation": decision
    }
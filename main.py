from fastapi import FastAPI, BackgroundTasks
from processor import market_processor
import asyncio

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    # Start the background processor loop
    asyncio.create_task(market_processor.process_loop())
    
    # Fill queue with initial "Idle" stocks (e.g., Silver)
    await market_processor.add_request("TATSILV", priority=2)
    await market_processor.add_request("SILVERBEES", priority=2)

@app.get("/track/{symbol}")
async def track_stock_live(symbol: str):
    # User requested this -> Priority 1
    await market_processor.add_request(symbol.upper(), priority=1)
    return {"status": "Priority request added", "symbol": symbol}

@app.get("/brain/analyze/{symbol}")
async def analyze_stock(symbol: str):
    await market_processor.add_request(symbol.upper(), priority=1)    
    await asyncio.sleep(1)    
    from brain import get_ai_decision
    decision = get_ai_decision(symbol.upper())
    
    return {"symbol": symbol, "ai_analysis": decision}
from sqlalchemy import create_engine, Column, String, Float, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import insert
import datetime
import os
from dotenv import load_dotenv

load_dotenv()
Base = declarative_base()

class MarketData(Base):
    __tablename__ = "market_intelligence"
    symbol = Column(String, primary_key=True)
    price = Column(Float)
    rsi = Column(Float, default=50.0)
    sentiment = Column(Float, default=0.0) # -1.0 to 1.0
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

# Ensure SSL mode is passed to SQLAlchemy for Neon connection
engine = create_engine(os.getenv("DATABASE_URL"), connect_args={"sslmode": "require"})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def upsert_market_intelligence(symbol, price, rsi=None, sentiment=None):
    db = SessionLocal()
    try:
        data = {
            "symbol": symbol,
            "price": price,
            "timestamp": datetime.datetime.utcnow()
        }
        if rsi is not None: data["rsi"] = rsi
        if sentiment is not None: data["sentiment"] = sentiment

        stmt = insert(MarketData).values(**data)
        
        # Only update the fields we generated, don't overwrite with nulls
        update_cols = {k: v for k, v in data.items() if k != "symbol"}

        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=['symbol'],
            set_=update_cols
        )
        db.execute(upsert_stmt)
        db.commit()
    finally:
        db.close()
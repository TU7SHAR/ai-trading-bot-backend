from sqlalchemy import create_engine, Column, String, Float, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
import datetime
import os
from dotenv import load_dotenv

load_dotenv()
Base = declarative_base()

class PriceHistory(Base):
    __tablename__ = "market_data"
    symbol = Column(String, primary_key=True)
    price = Column(Float)
    sentiment = Column(Float, default=0.0) # -1 to 1
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

engine = create_engine(os.getenv("DATABASE_URL"))
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def upsert_market_data(symbol, price, sentiment=None):
    db = SessionLocal()
    try:
        stmt = insert(PriceHistory).values(
            symbol=symbol, price=price, sentiment=sentiment, timestamp=datetime.datetime.utcnow()
        )
        # If symbol exists, update everything except the symbol name
        update_dict = {"price": price, "timestamp": datetime.datetime.utcnow()}
        if sentiment is not None:
            update_dict["sentiment"] = sentiment
            
        upsert_stmt = stmt.on_conflict_do_update(index_elements=['symbol'], set_=update_dict)
        db.execute(upsert_stmt)
        db.commit()
    finally:
        db.close()
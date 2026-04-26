import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Settings
    CONSUMER_KEY = os.getenv("KOTAK_CONSUMER_KEY")
    CONSUMER_SECRET = os.getenv("KOTAK_CONSUMER_SECRET")
    UCC = os.getenv("KOTAK_UCC")
    MOBILE = os.getenv("KOTAK_MOBILE")
    MPIN = os.getenv("KOTAK_MPIN")
    
    # DB Settings
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # Trading Constants
    DEFAULT_EXCHANGE = "NSE"
    SILVER_SYMBOL = "TATSILV" 
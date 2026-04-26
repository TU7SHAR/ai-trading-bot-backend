from neo_api_client import NeoAPI
from config import Config

def get_client():
    client = NeoAPI(
        consumer_key=Config.CONSUMER_KEY,
        environment='prod'
    )
    return client

def login_session(client, totp):
    try:
        client.login(
            mobile_number=Config.MOBILE,
            ucc=Config.UCC,
            totp=totp
        )
        client.session_2fa(Config.MPIN)
        return True
    except Exception as e:
        print(f"Login failed: {e}")
        return False
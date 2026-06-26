import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    LOCAL_IP = os.getenv("LOCAL_IP", "127.0.0.1")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///callbacks.db")
    CLEANUP_HOURS = int(os.getenv("CLEANUP_HOURS", 24))
    CLEANUP_INTERVAL = int(os.getenv("CLEANUP_INTERVAL", 3600))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
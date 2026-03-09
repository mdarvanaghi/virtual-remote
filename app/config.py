import os
from dotenv import load_dotenv

load_dotenv()

PIN: str = os.getenv("PIN", "0000")
SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")

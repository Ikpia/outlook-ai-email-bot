import os
from dotenv import load_dotenv

# ✅ Load Environment Variables
load_dotenv(dotenv_path="backend/config/.env")

# ✅ MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI")

# ✅ Microsoft Graph API Credentials
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["https://graph.microsoft.com/.default"]
OUTLOOK_API_URL = "https://graph.microsoft.com/v1.0/me/messages"

# ✅ Redis Configuration for Celery
REDIS_URL = os.getenv("REDIS_URL")


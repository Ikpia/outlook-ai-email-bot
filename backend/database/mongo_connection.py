from pymongo import MongoClient, ASCENDING
from backend.api.config import MONGO_URI

# ✅ Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client["email_bot"]

# ✅ Define Collections
templates_collection = db["email_templates"]
emails_collection = db["emails"]
emails_collection.create_index([("id", ASCENDING)], unique=True, sparse=True)
scheduled_responses_collection = db["scheduled_responses"]
failed_responses_collection = db["failed_responses"]
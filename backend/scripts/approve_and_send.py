from backend.database.mongo_connection import emails_collection
from backend.api.tasks import schedule_email_response
from bson.objectid import ObjectId

def approve_email(email_id):
    emails_collection.update_one({"_id": ObjectId(email_id)}, {"$set": {"status": "Approved"}})
    print(f"✅ Email {email_id} approved.")

def send_email(email_id):
    email = emails_collection.find_one({"_id": ObjectId(email_id), "status": "Approved"})
    if email:
        schedule_email_response(email["body"], email["subject"], email["recipient"])
        print(f"📤 Email sent to {email['recipient']}")

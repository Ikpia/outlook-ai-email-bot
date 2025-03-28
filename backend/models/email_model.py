from backend.database.mongo_connection import db

# ✅ Define Email Schema
emails_collection = db["email_responses"]

def save_email(recipient, subject, body, status="Pending"):
    email_data = {
        "recipient": recipient,
        "subject": subject,
        "body": body,
        "status": status
    }
    emails_collection.insert_one(email_data)

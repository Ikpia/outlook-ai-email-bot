from backend.database.mongo_connection import db

# ✅ Define Template Schema
templates_collection = db["email_templates"]

def save_template(category, subject, body):
    template_data = {"category": category, "subject": subject, "body": body}
    templates_collection.insert_one(template_data)

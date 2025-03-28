import requests
import json
from msal import ConfidentialClientApplication
from pymongo import MongoClient
from backend.services.generate_response import generate_email_response

import os

# Microsoft Graph API Credentials
OUTLOOK_API_URL = os.getenv("GRAPH_API_URL")
SEND_MAIL_URL = os.getenv("SEND_MAIL_URL")
CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
MICROSOFT_TENANT_ID = os.getenv("MICROSOFT_TENANT_ID")
MICROSOFT_REDIRECT_URI = os.getenv("MICROSOFT_REDIRECT_URI", "http://localhost:5000/callback")
#MICROSOFT_AUTH_URL = f"https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}/oauth2/v2.0/authorize"
#MICROSOFT_TOKEN_URL = f"https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}/oauth2/v2.0/token"
MICROSOFT_TOKEN_URL = os.getenv("MICROSOFT_TOKEN_URL")
AUTHORITY = os.getenv("MICROSOFT_AUTH_URL")
SCOPES = scope = ["email", "openid", "profile", "https://graph.microsoft.com/Mail.Read", "https://graph.microsoft.com/Mail.ReadWrite", "https://graph.microsoft.com/Mail.Send"]

# ✅ Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["email_bot"]
responses_collection = db["email_responses"]

# ✅ Get Microsoft Outlook API Access Token
def get_access_token():
    app = ConfidentialClientApplication(CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET)
    result = app.acquire_token_for_client(scopes=SCOPES)

    if "access_token" in result:
        return result["access_token"]
    else:
        raise Exception("Authentication failed:", result.get("error_description"))

# ✅ Fetch Unread Emails from Outlook
def get_unread_emails():
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{OUTLOOK_API_URL}?$filter=isRead eq false", headers=headers)
    emails = response.json().get("value", [])

    return emails

# ✅ Send AI-Generated Response via Outlook
def send_email_response(recipient_email, subject, body):
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    email_data = {
        "message": {
            "subject": subject,
            "body": {"contentType": "Text", "content": body},
            "toRecipients": [{"emailAddress": {"address": recipient_email}}]
        },
        "saveToSentItems": "true"
    }

    response = requests.post("https://graph.microsoft.com/v1.0/me/sendMail", headers=headers, json=email_data)
    
    return response.status_code == 202  # 202 means accepted for delivery

# ✅ Process Emails: Fetch, Generate AI Response, and Send Reply
def process_emails():
    unread_emails = get_unread_emails()
    
    for email in unread_emails:
        sender = email["from"]["emailAddress"]["address"]
        subject = email["subject"]
        email_body = email["body"]["content"]
        
        print(f"\n📩 New Email from {sender}: {subject}")

        # Generate AI response
        ai_response = generate_email_response(email_body)
        print(f"🤖 AI Response: {ai_response}")

        # Store response in MongoDB
        email_log = {
            "recipient": sender,
            "category": "Auto-Generated Response",
            "email_text": email_body,
            "ai_response": ai_response,
            "status": "Pending"
        }
        responses_collection.insert_one(email_log)

        # Send AI-generated response via Outlook
        send_success = send_email_response(sender, f"Re: {subject}", ai_response)
        if send_success:
            print(f"✅ AI response sent to {sender}")
        else:
            print(f"❌ Failed to send response to {sender}")

# ✅ Run Email Processing
if __name__ == "__main__":
    process_emails()

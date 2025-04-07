from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import string
from pymongo import MongoClient
from celery import shared_task, chain
import logging
from bs4 import BeautifulSoup
from celery.schedules import crontab
import os
from bson import json_util
from flask import Response
from bson.objectid import ObjectId
from dotenv import load_dotenv
import requests
from requests_oauthlib import OAuth2Session
from datetime import datetime, timezone, timedelta
from celery import Celery
from backend.database.mongo_connection import emails_collection, failed_responses_collection, scheduled_responses_collection
from backend.services.generate_response import generate_email_response
from backend.services.category import categorize_email
from backend.scripts.approve_and_send import  approve_email

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Celery Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery = Celery(app.name, broker=REDIS_URL, backend=REDIS_URL)


# Microsoft Graph API Credentials
GRAPH_API_URL = os.getenv("GRAPH_API_URL")
SEND_MAIL_URL = os.getenv("SEND_MAIL_URL")
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
MICROSOFT_TENANT_ID = os.getenv("MICROSOFT_TENANT_ID")
MICROSOFT_REDIRECT_URI = os.getenv("MICROSOFT_REDIRECT_URI", "http://localhost:5000/callback")
#MICROSOFT_AUTH_URL = f"https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}/oauth2/v2.0/authorize"
#MICROSOFT_TOKEN_URL = f"https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}/oauth2/v2.0/token"
MICROSOFT_TOKEN_URL = os.getenv("MICROSOFT_TOKEN_URL")
MICROSOFT_AUTH_URL = os.getenv("MICROSOFT_AUTH_URL")

import os
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

#TOKEN_URL = f"https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}/oauth2/v2.0/token"

# OAuth2 Session
scope = [
  "openid",
  "profile",
  "email",
  "https://graph.microsoft.com/User.Read",
  "https://graph.microsoft.com/Mail.Read",
  "https://graph.microsoft.com/Mail.ReadWrite",
  "https://graph.microsoft.com/Mail.Send"
  ]
oauth = OAuth2Session(MICROSOFT_CLIENT_ID, redirect_uri=MICROSOFT_REDIRECT_URI, scope=scope)

def extract_text_from_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator="\n", strip=True)


def handle_failed_email(email, token):
    """Log failed emails and notify a team member."""
    failed_responses_collection.insert_one({
        "email_id": email.get("id"),
        "recipient": email.get("toRecipients", [{}])[0].get("emailAddress", {}).get("address", "Unknown"),
        "category": email.get("category"),
        "scheduled_time": email.get("scheduled_time", "Unknown"),
        "status": "Failed",
        "error_message": "Failed to send email",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    notify_team_member(email.get("toRecipients", [{}])[0].get("emailAddress", {}).get("address", "Unknown"), email.get("category"), token)

def notify_team_member(recipient, category, token):
    """Notify a team member about the failure."""
    admin_email = "adekiitn4faith@outlook.com"
    subject = "Email Send Failure Alert"
    body = f"An email to {recipient} (Category: {category}) failed to send. Please investigate."
    send_email(admin_email, subject, body, token)



@celery.task
def send_failure_report():
    """Generate a daily failure report and send it to the team."""
    failed_emails = list(failed_responses_collection.find({"created_at": {"$gte": (datetime.now(datetime.timezone.utc) - timedelta(days=1)).isoformat()}}))

    if not failed_emails:
        return "No failures to report."

    report_body = "\n".join([f"{email['recipient']} - {email['category']} - {email['error_message']}" for email in failed_emails])

    send_email("support@example.com", "Daily Failure Report", report_body)

# Run at midnight every day
celery.conf.beat_schedule["send-daily-failure-report"] = {
    "task": "send_failure_report",
    "schedule": crontab(minute=0, hour=0),
}

def clean_text(html_content):
    text = extract_text_from_html(html_content)
    # Remove non-printable characters
    text = "".join(char for char in text if char in string.printable)
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


@app.route("/schedule-response", methods=["POST"])
def schedule_response():
    """Schedule an email response at a specified time."""
    data = request.json
    category = data.get("category")
    hour = data.get("hour")
    minute = data.get("minute")
    folderName = data.get("folderName")

    if not all([category, hour, minute, folderName]):
        return jsonify({"error": "Missing required fields"}), 400

    # Store the scheduled response in MongoDB
    scheduled_responses_collection.insert_one({
         "category": category,
        "scheduled_hour": hour,
        "scheduled_minute": minute,
        "folder_name": folderName
    })
    token = oauth.token.get("access_token")
    if not token:
        return {"error": "Missing or expired access token"}
    folder_id = get_folder_id(folderName, token)
    if not folder_id:
        return {"error": "Folder not found."}
    return jsonify({"message": "Scheduled responses processed"}), 201


@app.route("/respond", methods=["POST"])
def respond():
    data = request.json
    category = data.get("category")
    token = oauth.token.get("access_token")
    if not token:
        return {"error": "Missing or expired access token"}
    response = send_scheduled_responses(token, category)
    return jsonify({"message": response}), 201


def send_scheduled_responses(token, category):
    """Send responses at their scheduled time."""
    scheduled_categories = scheduled_responses_collection.find({"category":category})
    scheduled_categories_list = list(scheduled_categories)
    print(f"Scheduled categories: {scheduled_categories_list}")
    processed_count = 0

    for category in scheduled_categories_list:
        print(f"Processing category: {category['category']}")
        approved_emails = emails_collection.find({"category": category["category"], "status": "Categorized"})
        approved_emails_list = list(approved_emails)
        print(f"Found {len(approved_emails_list)} approved emails for category: {category['category']}")

        for email in approved_emails_list:
            body_content = email.get("body", {}).get("content", "")
            if not body_content:
                print(f"Skipping email {email.get('id')} due to empty content.")
                continue
            #body_content = clean_text(body_content)
            print(body_content)
            response_text = generate_email_response(body_content)
            print(response_text)
            #success = send_email(recipient_email, subject, response_text, token)
            #print(success)
            if response_text:
                status = "Responded" if response_text else "Failed"
                emails_collection.update_one({"id": email["id"]}, {"$set": {"status": status, "ai_response": response_text}})
                #save_email_to_folder(folder_id, recipient_email, subject, response_text, token)  # Store response
            else:
                handle_failed_email(email, token)  # Call failure handler
            processed_count += 1

    return {"message": f"Processed {processed_count} scheduled responses"}


def send_email(recipient, subject, body, token ):
    #token = oauth.token["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    email_data = {
        "message": {
            "subject": subject,
            "body": {"contentType": "Text", "content": body},
            "toRecipients": [{"emailAddress": {"address": recipient}}],
        },
        "saveToSentItems": True
    }
    response = requests.post(SEND_MAIL_URL, headers=headers, json=email_data)
    if response.status_code != 202:
        print(f"❌ Email sending failed: {response.text}")
        return False
    return True

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Outlook AI Email Bot is running!"})

@app.route("/auth", methods=["GET"])
def auth():
    auth_url, state = oauth.authorization_url(MICROSOFT_AUTH_URL)
    return jsonify({"auth_url": auth_url})

@app.route("/callback", methods=["GET"])
def callback():
    token = oauth.fetch_token(MICROSOFT_TOKEN_URL, client_secret=MICROSOFT_CLIENT_SECRET, authorization_response=request.url)
    return jsonify(token)


@app.route("/create_mail_folder", methods=["POST"])
def create_mail_folder():
    token = oauth.token.get("access_token")
    if not token:
        return jsonify({"error": "Missing or expired access token"}), 400
    
    folder_name = request.json.get("folderName")
    if not folder_name:
        return jsonify({"error": "Folder name is required"}), 400
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {
        "displayName": folder_name,
    }
    
    response = requests.post("https://graph.microsoft.com/v1.0/me/mailFolders", headers=headers, json=data)
    if response.status_code == 201:
        return jsonify(response.json()), 201
    
    return jsonify({"error": "Failed to create mail folder", "details": response.json()}), response.status_code

@app.route("/mail_folders", methods=["GET"])
def get_mail_folders():
    token = oauth.token.get("access_token")
    if not token:
        return jsonify({"error": "Missing or expired access token"}), 400
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.get("https://graph.microsoft.com/v1.0/me/mailFolders", headers=headers)

    if response.status_code == 200:
        mail_folders = response.json()
        return jsonify(mail_folders)
    
    return jsonify({"error": "Failed to fetch mail folders", "details": response.json()}), response.status_code


@app.route("/get-emails", methods=["GET"])
def getemails():
    emails_cursor = emails_collection.find({})
    emails_list = list(emails_cursor)

    if not emails_list:
        return Response(json_util.dumps({"error": "No emails in Database"}), mimetype='application/json', status=404)

    return Response(json_util.dumps(emails_list), mimetype='application/json')


@app.route("/fetch-outlook-emails", methods=["GET"])
def fetch_outlook_emails():
    token = oauth.token.get("access_token")
    if not token:
        return {"error": "Missing or expired access token"}
    
    """Manually trigger email fetching & categorization."""
    result = fetch_and_categorize_emails(token)
    return Response(json_util.dumps(result), mimetype="application/json")

#@celery.task(name="backend.api.app.fetch_and_categorize_emails")
def fetch_and_categorize_emails(token):
    """Fetch Outlook emails and categorize them periodically."""
    if not token:
        return {"error": "Missing or expired access token"}

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.get(GRAPH_API_URL, headers=headers)

    if response.status_code == 200:
        emails = response.json().get("value", [])

        categorized_emails = []
        for email in emails:
            email_id = email.get("id")
            body_content = clean_text(email.get("body", {}).get("content", ""))
            email["body"]["content"] = body_content
            print(body_content)
            # Check if the email already exists in MongoDB
            if not emails_collection.find_one({"id": email_id}):
                category = categorize_email(email["subject"])  # Use LLM to categorize
                email["category"] = category  # Assign category
                email["status"] = "Categorized"
                email["ai_response"] = "Pending"
                
                # Save to MongoDB
                emails_collection.insert_one(email)
            categorized_emails.append(email)
        
        return {"message": "Emails categorized successfully", "emails": categorized_emails}

    return {"error": "Failed to fetch emails", "details": response.json()}


def get_folder_id(folder_name, token):
    url = "https://graph.microsoft.com/v1.0/me/mailFolders"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        folders = response.json().get("value", [])
        for folder in folders:
            if folder["displayName"].lower() == folder_name.lower():
                return folder["id"]
    
    print(f"⚠️ Folder '{folder_name}' not found.")
    return None


def save_email_to_folder(folder_id, recipient_email, subject, response_text, token):
    url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{folder_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    email_data = {
        "subject": subject,
        "body": {"contentType": "Text", "content": response_text},
        "toRecipients": [{"emailAddress": {"address": recipient_email}}]
    }

    response = requests.post(url, headers=headers, json=email_data)
    
    if response.status_code == 201:
        print(f"✅ Email saved to folder {folder_id} successfully.")
        return True
    else:
        print(f"❌ Failed to save email: {response.text}")
        return False


'''
def move_email_to_folder(email_id, folder_name):
    """Move an email to a different Outlook folder."""
    move_url = f"https://graph.microsoft.com/v1.0/me/messages/{email_id}/move"
    token = oauth.token.get("access_token")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Find folder ID
    folders_url = "https://graph.microsoft.com/v1.0/me/mailFolders"
    folder_response = requests.get(folders_url, headers=headers)
    if folder_response.status_code == 200:
        folders = folder_response.json().get("value", [])
        folder_id = next((f["id"] for f in folders if f["displayName"] == folder_name), None)

        if not folder_id:
            return f"Folder '{folder_name}' not found."
        
        move_data = {"destinationId": folder_id}
        response = requests.post(move_url, json=move_data, headers=headers)
        
        if response.status_code == 201:
            emails_collection.update_one({"id": email_id}, {"$set": {"status": "Moved"}})
            return f"Email {email_id} moved to {folder_name}."
        else:
            return f"Error moving email: {response.text}"
    else:
        return f"Error fetching folders: {folder_response.text}"


@app.route("/move-responded-emails", methods=["POST"])
def move_responded_emails():
    """Move all responded emails to a specific folder."""
    folder_name = request.json.get("folder_name")

    if not all([folder_name]):
        return jsonify({"error": "Missing required field"}), 400
    token = oauth.token.get("access_token")
    # Fetch responded emails from MongoDB
    responded_emails = emails_collection.find({"status": "Responded"})

    moved_emails = []
    for email in responded_emails:
        email_id = email["id"]
        result = move_email_to_folder(email_id, folder_name)
        moved_emails.append({"email_id": email_id, "result": result})

    return jsonify({"moved_emails": moved_emails})
'''

@app.route('/delete-email/<string:email_id>', methods=['DELETE'])
def delete_email(email_id):

    # Attempt to delete the document
    result = emails_collection.delete_one({"id": email_id})

    if result.deleted_count == 0:
        return jsonify({"error": "Email not found"}), 404

    return jsonify({"message": "Email deleted successfully"}), 200

# Approve Email API
@app.route("/approve_email/<email_id>", methods=["POST"])
def api_approve_email(email_id):
    approve_email(email_id)
    return jsonify({"message": "Email Approved!"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)

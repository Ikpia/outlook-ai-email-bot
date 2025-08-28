import requests
import re
#import pandas as pd
import os
import re

import os
import json
import re
import time
import requests
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from dotenv import load_dotenv

# --------------------
# LOAD ENVIRONMENT
# --------------------
load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@company.com")

# --------------------
# FASTAPI APP
# --------------------
#app = FastAPI()

# --------------------
# MONGO CONNECTION
# --------------------
if not MONGO_URI:
    try_uris = ["mongodb://localhost:27017", "mongodb://127.0.0.1:27017"]
else:
    try_uris = [MONGO_URI]

mongo_client = None
for uri in try_uris:
    try:
        mongo_client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        mongo_client.admin.command("ping")  # test connection
        print(f"✅ Connected to MongoDB at {uri}")
        break
    except Exception as e:
        print(f"⚠️ Could not connect to {uri} -> {e}")

if not mongo_client:
    raise Exception("❌ Failed to connect to MongoDB on all URIs")

db_clients = mongo_client["companyData"]

# --------------------
# LOAD JSON TEMPLATES
# --------------------
with open("datasets_combined.json", "r", encoding="utf-8") as f:
    template_datasets = json.load(f)


def get_template_catalog():
    """Load all templates from JSON into a usable catalog, split into individual templates."""
    catalog = []
    for dataset in template_datasets:
        paragraphs = dataset.get("content", {}).get("paragraphs", [])

        for i, para in enumerate(paragraphs, start=1):
            if not para.strip():
                continue

            placeholders = re.findall(r'[\{\[]([^\}\]]+)[\}\]]', para)
            catalog.append({
                "id": f"{dataset.get('_id', '')}_{i}",
                "name": f"{dataset.get('source_file', 'Unnamed')} - Template {i}",
                "placeholders": list(set(placeholders)),
                "full_content": para.strip()
            })
    return catalog

# --------------------
# TOGETHER API
# --------------------
def query_together_api(messages: list, retries=3, backoff=5):
    url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": 500
    }

    for attempt in range(retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 429:
                wait_time = backoff * (attempt + 1)
                print(f"⚠️ Rate limit hit. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt == retries - 1:
                raise Exception(f"Failed after {retries} attempts: {str(e)}")
            time.sleep(backoff)

    raise Exception("Failed after retries due to rate limits")

# --------------------
# MONGO SCHEMA
# --------------------
def get_enhanced_schema():
    schema = {}
    for coll_name in db_clients.list_collection_names():
        sample = db_clients[coll_name].find_one()
        if sample:
            sample.pop("_id", None)
            schema[coll_name] = list(sample.keys())
    return schema

# --------------------
# QUERY GENERATION (LLM)
# --------------------
def get_llm_query_enhanced(user_prompt: str, schema: dict):
    system_msg = {
        "role": "system",
        "content": f"""You are an expert MongoDB query generator.

RULES:
1. Return ONLY valid JSON with 'collection' and 'query'.
2. Use regex with case-insensitive for names: {{"$regex": "pattern", "$options": "i"}}.
3. Use exact match for IDs, VINs, emails.
4. Do not explain anything. Just return JSON.

Available collections:
{json.dumps(schema, indent=2)}
"""
    }
    user_msg = {
        "role": "user",
        "content": f"""Generate MongoDB query for: "{user_prompt}"

Return only JSON format:
{{"collection": "collection_name", "query": {{...}}}}"""
    }

    try:
        llm_response = query_together_api([system_msg, user_msg])
        content = llm_response["choices"][0]["message"]["content"].strip()
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        return json.loads(content)
    except Exception as e:
        print(f"[QUERY ERROR] {str(e)}")
        return None

# --------------------
# TEMPLATE SELECTION (LLM-powered with fix)
# --------------------
def select_template_llm(user_prompt: str, client_record: dict, templates: list):
    system_msg = {
        "role": "system",
        "content": """You are an assistant that selects the BEST matching email template.

RULES:
- Return ONLY valid JSON: {"id": "template_id"}.
- Consider BOTH the user request AND the client record fields when deciding.
- Always choose the most contextually relevant template (e.g., if VIN/vehicle fields exist, prefer vehicle-related templates)."""
    }

    template_summary = "\n".join(
        [f"{t['id']}: {t['name']} => {t['full_content'][:100]}..." for t in templates]
    )

    # 🔧 FIX: safely serialize client_record including datetime/ObjectId
    client_dump = json.dumps(client_record, indent=2, default=str)

    user_msg = {
        "role": "user",
        "content": f"""User request: "{user_prompt}"

Client record: {client_dump}

Available templates:
{template_summary}

Pick the ONE most relevant template. 
Return only JSON:
{{"id": "<best_template_id>"}}"""
    }

    try:
        llm_response = query_together_api([system_msg, user_msg])
        content = llm_response["choices"][0]["message"]["content"].strip()
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        selected = json.loads(content)
        best_id = selected.get("id")
        return next((t for t in templates if t["id"] == best_id), None)
    except Exception as e:
        print(f"[LLM TEMPLATE ERROR] {str(e)}")
        return None

# --------------------
# TEMPLATE FILLER
# --------------------
def fill_template_placeholders(template_content: str, client_record: dict):
    filled_content = template_content
    for key, value in client_record.items():
        if value is None:
            continue
        value = str(value)
        filled_content = re.sub(rf"\{{{key}\}}", value, filled_content)
        filled_content = re.sub(rf"\[{key}\]", value, filled_content)
    return filled_content.strip()

# --------------------
# MODELS
# --------------------
class EmailRequest(BaseModel):
    text: str

class EmailResponse(BaseModel):
    to: str = None
    subject: str = None
    body: str = None
    error: str = None

# --------------------
# MAIN ENDPOINT
# --------------------
#@app.post("/compose", response_model=EmailResponse)
def compose_email(email: EmailRequest):
    user_prompt = email.text.strip()
    if not user_prompt:
        raise HTTPException(status_code=400, detail="Empty prompt provided")

    schema = get_enhanced_schema()
    llm_query = get_llm_query_enhanced(user_prompt, schema)
    if not llm_query:
        return EmailResponse(error="Could not generate query")

    coll = llm_query["collection"]
    query = llm_query["query"]
    client_record = db_clients[coll].find_one(query)
    if not client_record:
        return EmailResponse(error="No matching client found")

    client_record.pop("_id", None)
    templates = get_template_catalog()
    selected_template = select_template_llm(user_prompt, client_record, templates)
    if not selected_template:
        return EmailResponse(error="No suitable template found")

    filled_content = fill_template_placeholders(selected_template["full_content"], client_record)
    client_email = client_record.get("Email") or client_record.get("email") or "noemail@example.com"
    client_name = client_record.get("Name") or client_record.get("name") or "Valued Client"

    return EmailResponse(
        to=client_email,
        subject=f"Message for {client_name}",
        body=filled_content
    )



# External API for generating responses
#generate_response_url = "https://adekiitan11-email-model.hf.space/generate"
#generate_response_url = "https://adekiitan11-llama2-email-api.hf.space/generate"

def clean_placeholders(text: str) -> str:
    # Remove specific placeholders
    cleaned = re.sub(r"\[Name\]", "", text)
    cleaned = re.sub(r"\[Your Name\]", "", cleaned)
    cleaned = re.sub(r"\[User\]", "", cleaned)
    cleaned = re.sub(r"\[User Name\]", "", cleaned)
    # Optionally clean up extra whitespace left behind
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned

# ✅ Function to Generate Email Responses
#def generate_email_response(email_content):
#    if len(email_content) > 150:
#        return {"response": "Hello, thank you for reaching out to us, we have received your request and we will get back to you as soon as possible. Best regards."}
#    user_query = {"text": f"{email_content}"}
#    response = compose_email(user_query)
#    json_response = response.json()  # Ensure it's a dictionary
#    answer = clean_placeholders(json_response.get("response", "").strip())
#    return {"response": f"{answer}"}


def generate_email_response(email_content):
    if len(email_content) > 150:
        return {
            "response": "Hello, thank you for reaching out to us, we have received your request and we will get back to you as soon as possible. Best regards."
        }

    try:
        response = compose_email(EmailRequest(text=email_content))

        if response.error:
            return {"response": f"⚠️ {response.error}"}

        answer = clean_placeholders(response.body or "")
        return {"response": answer}
    except Exception as e:
        return {"response": f"⚠️ Failed to generate response: {str(e)}"}


# ✅ Example usage
#print(generate_email_response("Hello, I need information regarding Doctor  Psychiatry  Global Health Hospital  Board Certified  OnCall"))
'''
Hello, I need information regarding Nurse  Psychiatry  Sunrise Clinic  Certified Medical Practitioner  FullTime
Can you confirm the date for my appointment? I want to make sure I have the correct one. Thanks! Best, Sophia Davis
I have a query about my claim details CL52567  VIN569625K
'''

# ✅ Example Test
'''
if __name__ == "__main__":
    user_email = "Hello, I need information regarding Nurse  Psychiatry  Sunrise Clinic  Certified Medical Practitioner  FullTime"
    ai_response = generate_email_response(user_email)
    print(f"📩 **User Query:** {user_email}")
    print(f"🤖 **AI Response:** {ai_response}")
'''



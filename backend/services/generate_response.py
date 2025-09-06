import os
import json
import re
import time
import requests
from typing import Dict, Any
#from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from groq import Groq
from dotenv import load_dotenv

# --------------------
# LOAD ENVIRONMENT
# --------------------
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# --------------------
# MONGO CONNECTION
# --------------------
if not MONGO_URI:
    try_uris = ["mongodb://localhost:27017", "mongodb://127.0.0.1:27017"]
else:
    try_uris = [MONGO_URI, "mongodb://localhost:27017"]

mongo_client = None
for uri in try_uris:
    try:
        print(f"[DEBUG] Trying MongoDB URI: {uri}")
        mongo_client = MongoClient(uri, serverSelectionTimeoutMS=10000)
        mongo_client.admin.command("ping")
        print(f"✅ Connected to MongoDB at {uri}")
        break
    except Exception as e:
        print(f"⚠️ Could not connect to {uri}: {e}")

if not mongo_client:
    raise Exception("❌ Failed to connect to MongoDB on all URIs")

db_clients = mongo_client.get_database("companyData")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@company.com")

# --------------------
# FASTAPI APP
# --------------------
#app = FastAPI()

# --------------------
# LOAD JSON TEMPLATES
# --------------------
with open("datasets_combined.json", "r", encoding="utf-8") as f:
    template_datasets = json.load(f)

def get_template_catalog():
    catalog = []
    counter = 1
    for dataset in template_datasets:
        paragraphs = dataset.get("content", {}).get("paragraphs", [])
        for para in paragraphs:
            if not para.strip():
                continue

            # only keep templates that have placeholders
            placeholders = re.findall(r'[\{\[]([^\}\]]+)[\}\]]', para)
            if not placeholders:
                continue

            catalog.append({
                "id": f"{counter}",
                "source_id": dataset.get("_id", ""),
                "name": f"{dataset.get('source_file', 'Unnamed')} - Template {counter}",
                "placeholders": list(set(placeholders)),
                "full_content": para.strip()
            })
            counter += 1
    print(f"[DEBUG] Loaded {len(catalog)} templates with placeholders from JSON")
    return catalog


# --------------------
# TOGETHER / GROQ API
# --------------------
def query_together_api(messages: list, retries=3, backoff=5):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": 500
    }

    for attempt in range(retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 429:
                print("[DEBUG] Rate limit hit, retrying...")
                time.sleep(backoff * (attempt + 1))
                continue
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[DEBUG] API request error: {str(e)}")
            if attempt == retries - 1:
                raise Exception(f"Failed after {retries} attempts: {str(e)}")
            time.sleep(backoff)
    raise Exception("Failed after retries due to rate limits")

# --------------------
# MONGO SCHEMA
# --------------------
def get_enhanced_schema():
    schema = {}
    collections = db_clients.list_collection_names()

    for coll_name in collections:
        sample = db_clients[coll_name].find_one()
        if sample:
            sample.pop("_id", None)
            schema[coll_name] = list(sample.keys())

    # 🔥 Fallback: enrich schema from templates JSON
    for dataset in template_datasets:
        meta = dataset.get("metadata", {})
        coll = meta.get("collection")
        fields = meta.get("fields", [])
        if coll:
            if coll not in schema:
                schema[coll] = fields
            else:
                schema[coll] = list(set(schema[coll] + fields))

    print(f"[DEBUG] Schema generated: {json.dumps(schema, indent=2, default=str)}")

    return schema

# --------------------
# QUERY GENERATION
# --------------------
def get_llm_query_enhanced(user_prompt: str, schema: dict):
    system_msg = {
        "role": "system",
        "content": f"""You are an expert MongoDB query generator.

RULES:
1. Return ONLY valid JSON with 'collection' and 'query'.
2. Use regex with case-insensitive for names.
3. Use exact match for IDs, VINs, emails.
4. Do not explain anything. Just return JSON.

Available collections:
{json.dumps(schema, indent=2, default=str)}
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
        if not content:
            raise ValueError("LLM returned empty response")

        # cleanup fences
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'\s*```$', '', content)

        print(f"[DEBUG] Raw LLM query response:\n{content}\n")
        return json.loads(content)

    except Exception as e:
        print(f"[QUERY ERROR] {str(e)}")

        # 🔥 fallback rules if LLM fails
        lower_prompt = user_prompt.lower()
        if "vin" in lower_prompt or "vehicle" in lower_prompt:
            return {"collection": "listings", "query": {"VIN": {"$regex": ".*", "$options": "i"}}}
        if "test" in lower_prompt or "result" in lower_prompt:
            return {"collection": "medical_tests", "query": {"Patient Name": {"$regex": ".*", "$options": "i"}}}
        if "appointment" in lower_prompt:
            return {"collection": "salon_appointments", "query": {"Client Name": {"$regex": ".*", "$options": "i"}}}
        if "case" in lower_prompt:
            return {"collection": "cases", "query": {"Client Name": {"$regex": ".*", "$options": "i"}}}

        return None

# --------------------
# QUERY NORMALIZATION
# --------------------
def normalize_query(q: dict) -> dict:
    """
    Convert string values in the query into case-insensitive regex matches.
    This ensures MongoDB queries are not tripped up by capitalization differences.
    """
    normalized = {}
    for key, value in q.items():
        if isinstance(value, str):
            # Make it regex, match full string, case-insensitive
            normalized[key] = {"$regex": f"^{value}$", "$options": "i"}
        elif isinstance(value, dict) and "$regex" in value:
            # Already regex from LLM, keep as is
            normalized[key] = value
        else:
            # Numbers, dates, etc.
            normalized[key] = value
    return normalized

# --------------------
# TEMPLATE SELECTION
# --------------------
def select_template_llm(user_prompt: str, client_record: dict, templates: list):
    system_msg = {
        "role": "system",
        "content": """You are an assistant that selects the BEST matching email template.

RULES:
- Return ONLY valid JSON: {"id": "template_id"}.
- Consider BOTH the user request AND the client record fields when deciding.
- Always choose the most contextually relevant template.
"""
    }

    template_summary = "\n".join(
        [f"{t['id']}: {t['name']} => {t['full_content'][:80]}..." for t in templates]
    )

    user_msg = {
        "role": "user",
        "content": f"""User request: "{user_prompt}"

Client record: {json.dumps(client_record, default=str)}

Available templates:
{template_summary}

Pick the ONE most relevant template.
Return only JSON:
{{"id": "<best_template_id>"}}"""
    }

    try:
        llm_response = query_together_api([system_msg, user_msg])
        content = llm_response["choices"][0]["message"]["content"].strip()
        if not content:
            raise ValueError("LLM returned empty response")
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        print(f"[DEBUG] Raw LLM template choice response:\n{content}\n")
        selected = json.loads(content)
        best_id = selected.get("id")
        matched_template = next((t for t in templates if t["id"] == best_id), None)
        if not matched_template and templates:
            matched_template = templates[0]
        return matched_template
    except Exception as e:
        print(f"[LLM TEMPLATE ERROR] {str(e)}")
        return templates[0] if templates else None

# --------------------
# TEMPLATE FILLER
# --------------------
def fill_template_placeholders(template_content: str, client_record: dict):
    filled_content = template_content
    for key, value in client_record.items():
        if value is None:
            continue
        value = str(value)
        filled_content = re.sub(rf"\{{{key}\}}", value, filled_content, flags=re.IGNORECASE)
        filled_content = re.sub(rf"\[{key}\]", value, filled_content, flags=re.IGNORECASE)

    # replace any unreplaced placeholders with "N/A"
    filled_content = re.sub(r'[\{\[]([^\}\]]+)[\}\]]', r'N/A', filled_content)

    return filled_content.strip()


# --------------------
# MODELS
# --------------------
'''
class EmailRequest(BaseModel):
    text: str

from typing import Optional

class EmailResponse(BaseModel):
    to: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    error: Optional[str] = None
'''

class EmailRequest(BaseModel):
    text: str

from typing import Optional

class EmailResponse(BaseModel):
    to: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    error: Optional[str] = None

def generate_email_response(req: EmailRequest):
    print(f"[DEBUG] Prompt: {req.text}")

    schema = get_enhanced_schema()
    llm_query = get_llm_query_enhanced(req.text, schema)
    if not llm_query:
        return EmailResponse(error="Could not generate query")

    collection = llm_query.get("collection")
    query = llm_query.get("query", {})
    # Normalize query before sending to MongoDB
    normalized_query = normalize_query(query)

    print(f"[DEBUG] Final normalized query: {json.dumps(normalized_query, indent=2)}")

    client_record = db_clients[collection].find_one(normalized_query)


    if not client_record:
        return EmailResponse(error="No matching client found")

    client_record.pop("_id", None)
    print(f"[DEBUG] Client record found: {json.dumps(client_record, indent=2, default=str)}")


    templates = get_template_catalog()
    matched_template = select_template_llm(req.text, client_record, templates)
    if not matched_template:
        return EmailResponse(error="No suitable template found")

    print(f"[DEBUG] Selected template: {matched_template['id']} => {matched_template['name']}")

    # ✅ Always fill the template with MongoDB data
    filled_body = fill_template_placeholders(matched_template["full_content"], client_record)

    # ✅ Debug final output
    print(f"[DEBUG] Final filled email body:\n{filled_body}\n")
    

    return EmailResponse(
        to=client_record.get("Email", ADMIN_EMAIL),
        subject=f"Response regarding {client_record.get('Make', client_record.get('ID', 'your request'))} {client_record.get('Model', '')}".strip(),
        body=filled_body,
        error=None
    )
'''
prompt = {
  "text": "My ID is ID-1026 can you give me more information on my test? Many thanks."
}
'''

#"Can you please give me the information for the vehicle with a VIN: HQ0S3U42R8K7FOYPP Many thanks, Bob"
#print(generate_email_response(EmailRequest(**prompt)))

# --------------------
# RUN APP
# --------------------
#if __name__ == "__main__":
#    import uvicorn
#    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
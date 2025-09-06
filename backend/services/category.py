import requests
import os
import re
import time  # needed for backoff retry
from groq import Groq
from dotenv import load_dotenv

# --------------------
# LOAD ENVIRONMENT
# --------------------
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
retries = 3
backoff = 5  # seconds


if not GROQ_API_KEY:
    raise EnvironmentError("GROQ_API_KEY environment variable is not set.")

CATEGORY_KEYWORDS = {
    "Billing Issues": ["invoice", "payment", "refund", "billing", "charge", "overcharge", "subscription", "fee"],
    "Technical Support": ["error", "bug", "issue", "crash", "not working", "troubleshoot", "server down"],
    "Account Management": ["password reset", "login issue", "update profile", "account locked", "change email"],
    "Claims & Disputes": ["claim", "dispute", "case number", "ticket", "resolution", "complaint"],
    "General Inquiry": ["help", "support", "question", "details", "assistance"],
    "Medical Inquiry": ["nurse", "psychiatry", "doctor", "hospital", "clinic", "medical"],
}

def keyword_based_categorization(email_subject):
    email_subject = email_subject.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(re.search(rf"\b{keyword}\b", email_subject) for keyword in keywords):
            return category
    return "Unknown"

def normalize_category(category_value):
    if isinstance(category_value, dict):
        cat_str = category_value.get("category", "")
    else:
        cat_str = str(category_value)
    
    cat_str = cat_str.strip()
    for valid_category in CATEGORY_KEYWORDS.keys():
        if valid_category.lower() in cat_str.lower():
            return valid_category
    return cat_str if cat_str else "Unknown"

def categorize_email(email_subject):
    category = keyword_based_categorization(email_subject)
    if category != "Unknown":
        return {'category': category}

    messages = f"""Classify the following email subject into one of the categories:
Billing Issues, Technical Support, Account Management, General Inquiry.
Email Subject: "{email_subject}"
Category:"""

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
                wait_time = backoff * (attempt + 1)
                print(f"⚠️ Rate limit hit. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            response.raise_for_status()
            response_data = response.json()
            return {'category': normalize_category(response_data)}
        except requests.exceptions.RequestException as e:
            if attempt == retries - 1:
                raise Exception(f"Failed after {retries} attempts: {str(e)}")
            time.sleep(backoff)

    raise Exception("Failed after retries due to rate limits or network issues")
def categorize_email(email_subject):
    category = keyword_based_categorization(email_subject)
    if category != "Unknown":
        return {'category': category}

    prompt = f"""Classify the following email subject into one of the categories:
Billing Issues, Technical Support, Account Management, General Inquiry.
Email Subject: "{email_subject}"
Category:"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {"role": "user", "content": prompt}
        ],
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
            response_data = response.json()
            category_text = response_data["choices"][0]["message"]["content"]
            return {'category': normalize_category(category_text)}
        except requests.exceptions.RequestException as e:
            if attempt == retries - 1:
                raise Exception(f"Failed after {retries} attempts: {str(e)}")
            time.sleep(backoff)

    raise Exception("Failed after retries due to rate limits or network issues")

# Example usage:
#if __name__ == "__main__":
    #print(categorize_email("Important: Your Azure account was disabled—pay now to resume service"))

import requests
from transformers import AutoTokenizer
import json
import re

space_url = "https://adekiitan11-email-model.hf.space/categorize"

# Define category keywords
CATEGORY_KEYWORDS = {
    "Billing Issues": ["invoice", "payment", "refund", "billing", "charge", "overcharge", "subscription", "fee"],
    "Technical Support": ["error", "bug", "issue", "crash", "not working", "troubleshoot", "server down"],
    "Account Management": ["password reset", "login issue", "update profile", "account locked", "change email"],
    "Claims & Disputes": ["claim", "dispute", "case number", "ticket", "resolution", "complaint"],
    "General Inquiry": ["information", "help", "support", "question", "details", "assistance"],
}

def keyword_based_categorization(email_subject):
    """Categorizes email based on keywords in the subject."""
    email_subject = email_subject.lower()
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(re.search(rf"\b{keyword}\b", email_subject) for keyword in keywords):
            return category  # Return category if a match is found

    return "Unknown"  # Return Unknown if no match is found

def categorize_email(email_subject):
    """Hybrid categorization using both keyword matching and LLaMA 2."""
    
    # Step 1: Try keyword-based categorization first
    category = keyword_based_categorization(email_subject)
    print(category)
    # Step 2: If no keyword match, ask LLaMA 2
    if category == "Unknown":
        user_query = {"subject": f"{email_subject}"}
        response = requests.post(space_url, json=user_query)
        return response.json()
    return category
    
# print(categorize_email("Hello, I need information regarding Nurse  Psychiatry  Sunrise Clinic  Certified Medical Practitioner  FullTime"))
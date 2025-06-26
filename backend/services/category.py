import requests
#from transformers import AutoTokenizer
import json
import re

space_url = "https://adekiitan11-email-model.hf.space/categorize"

# Define category keywords
CATEGORY_KEYWORDS = {
    "Billing Issues": ["invoice", "payment", "refund", "billing", "charge", "overcharge", "subscription", "fee"],
    "Technical Support": ["error", "bug", "issue", "crash", "not working", "troubleshoot", "server down"],
    "Account Management": ["password reset", "login issue", "update profile", "account locked", "change email"],
    "Claims & Disputes": ["claim", "dispute", "case number", "ticket", "resolution", "complaint"],
    "General Inquiry": ["help", "support", "question", "details", "assistance"],
    "Medical Inquiry": ["nurse", "psychiatry", "doctor", "hospital", "clinic", "medical"],
}

def keyword_based_categorization(email_subject):
    """Categorizes email based on keywords in the subject."""
    email_subject = email_subject.lower()
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(re.search(rf"\b{keyword}\b", email_subject) for keyword in keywords):
            return category  # Return category if a match is found

    return "Unknown"  # Return Unknown if no match is found

def normalize_category(category_value):
    """
    Normalizes the category value.
    If category_value is a dict with a "category" key, or if it's a string,
    this function checks whether it contains one of the valid category names (ignoring case and extra characters)
    and returns that valid category name.
    """
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
    """Hybrid categorization using both keyword matching and LLaMA 2."""
    
    # Step 1: Try keyword-based categorization first
    category = keyword_based_categorization(email_subject)
    print(category)
    # Step 2: If no keyword match, ask LLaMA 2
    if category == "Unknown":
        user_query = {"subject": f"{email_subject}"}
        response = requests.post(space_url, json=user_query)
        return { 'category': normalize_category(response.json()) }
    return { 'category': category }
    
#print(categorize_email("Important: Your Azure account was disabled—pay now to resume service"))
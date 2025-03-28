import json
import re
from backend.database.mongo_connection import templates_collection

# ✅ Load JSON Data
JSON_PATH = "backend/database/datasets/template_emails.json"

with open(JSON_PATH, "r", encoding="utf-8") as f:
    templates = json.load(f)

# ✅ Function to Clean & Normalize Text
def clean_text(text):
    if not isinstance(text, str):
        return ""  # Ensure text is a string
    text = text.strip()
    text = re.sub(r"\s+", " ", text)  # Remove extra spaces
    text = re.sub(r"[^\w\s.,!?]", "", text)  # Remove special characters
    return text

# ✅ Apply Cleaning
for template in templates:
    template["Category"] = clean_text(template["Category"])
    template["Subject"] = clean_text(template["Subject"])
    template["Body"] = clean_text(template["Body"])

# ✅ Store in MongoDB
templates_collection.insert_many(templates)
print("✅ Template emails stored in MongoDB after preprocessing!")
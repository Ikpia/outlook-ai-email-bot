import requests
import re
#import pandas as pd
import os
import re


# External API for generating responses
#generate_response_url = "https://adekiitan11-email-model.hf.space/generate"
generate_response_url = "https://adekiitan11-llama2-email-api.hf.space/generate"

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
def generate_email_response(email_content):
    if len(email_content) > 150:
        return {"response": "Hello, thank you for reaching out to us, we have received your request and we will get back to you as soon as possible. Best regards."}
    user_query = {"text": f"{email_content}"}
    response = requests.post(generate_response_url, json=user_query)
    json_response = response.json()  # Ensure it's a dictionary
    answer = clean_placeholders(json_response.get("response", "").strip())
    return {"response": f"{answer}"}


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
'''
import torch
from transformers import GPT2Tokenizer, GPT2LMHeadModel
from backend.models.template_model import get_templates

# ✅ Load Fine-Tuned GPT-2 Model
MODEL_PATH = "backend/models/fine_tuned_gpt2"
tokenizer = GPT2Tokenizer.from_pretrained(MODEL_PATH)
model = GPT2LMHeadModel.from_pretrained(MODEL_PATH)

# ✅ Categorize Email Based on LLM Output
def categorize_email(user_query):
    """
    Uses GPT-2 to determine the email category.
    """
    prompt = f"Classify this email: {user_query}\nCategory:"
    inputs = tokenizer(prompt, return_tensors="pt")

    output = model.generate(
        inputs.input_ids,
        max_length=30,
        num_return_sequences=1,
        pad_token_id=tokenizer.eos_token_id,
        temperature=0.7,
        top_k=50,
        top_p=0.95
    )

    category = tokenizer.decode(output[0], skip_special_tokens=True)
    return category.split("Category:")[-1].strip()

# ✅ Generate AI Response with Categorization
def generate_ai_response(user_query):
    """
    Generates an AI response and assigns an email category.
    """
    category = categorize_email(user_query)  # Get category
    templates = get_templates()

    # Check if a matching template exists
    for template in templates:
        if category.lower() in template["category"].lower():
            return category, template["body"]  # Use predefined template response

    # If no template is found, use GPT-2 to generate a response
    prompt = f"User: {user_query}\nAssistant:"
    inputs = tokenizer(prompt, return_tensors="pt")

    output = model.generate(
        inputs.input_ids,
        max_length=200,
        num_return_sequences=1,
        pad_token_id=tokenizer.eos_token_id,
        temperature=0.7,
        top_k=50,
        top_p=0.95
    )

    response = tokenizer.decode(output[0], skip_special_tokens=True)
    return category, response.split("Assistant:")[-1].strip()
'''

import torch
from transformers import GPT2Tokenizer, GPT2LMHeadModel

# Load Fine-Tuned GPT-2 Model (make sure the path is correct)
MODEL_PATH = "backend/models/fine_tuned_gpt2"
tokenizer = GPT2Tokenizer.from_pretrained(MODEL_PATH)
model = GPT2LMHeadModel.from_pretrained(MODEL_PATH)

def generate_ai_response(user_query):
    """
    Takes a user query (email) and generates an AI response using the fine-tuned GPT-2 model.
    """
    prompt = f"User: {user_query}\nAssistant:"
    inputs = tokenizer(prompt, return_tensors="pt")
    output = model.generate(
        inputs.input_ids,
        max_length=200,
        num_return_sequences=1,
        pad_token_id=tokenizer.eos_token_id,
        temperature=0.7,
        top_k=40,
        top_p=0.9
    )
    # Debug: print the complete decoded output
    full_output = tokenizer.decode(output[0], skip_special_tokens=True)
    print("DEBUG: Full output from model:", full_output)
    # Extract the response after "Assistant:" if present; otherwise, return full output
    if "Assistant:" in full_output:
        return full_output.split("Assistant:")[-1].strip()
    else:
        return full_output.strip()

# Example Test
if __name__ == "__main__":
    test_query = "Hi, When is my next vin? Please let me know. Thanks, Alex"
    ai_response = generate_ai_response(test_query)
    print(f"📩 User Query: {test_query}")
    print(f"🤖 AI Response: {ai_response}")
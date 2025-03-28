import torch
from transformers import GPT2Tokenizer, GPT2LMHeadModel

# ✅ Load the Fine-Tuned Model
MODEL_PATH = "backend/models/fine_tuned_gpt2"
tokenizer = GPT2Tokenizer.from_pretrained(MODEL_PATH)
model = GPT2LMHeadModel.from_pretrained(MODEL_PATH)

# ✅ Function to Generate Email Responses
def generate_email_response(user_query):
    """
    Takes a user query (email) and generates an AI response using the fine-tuned GPT-2 model.
    """
    prompt = f"User: {user_query}\nAssistant:"
    inputs = tokenizer(prompt, return_tensors="pt")

    output = model.generate(
        inputs.input_ids,
        attention_mask=inputs.attention_mask,  # ✅ Fix: Add attention mask
        max_new_tokens=500,  # ✅ Fix: Prevents incomplete responses
        num_return_sequences=1,
        pad_token_id=tokenizer.eos_token_id,
        temperature=0.7,
        top_k=50,
        top_p=0.95,
        do_sample=True  # ✅ Fix: Ensures diverse responses
    )

    response = tokenizer.decode(output[0], skip_special_tokens=True)
    return response.split("Assistant:")[-1].strip()

# ✅ Example Test
if __name__ == "__main__":
    user_email = "Can you confirm my appointment time?"
    ai_response = generate_email_response(user_email)
    print(f"📩 **User Query:** {user_email}")
    print(f"🤖 **AI Response:** {ai_response}")

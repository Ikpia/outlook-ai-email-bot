import requests
import re
import pandas as pd
import os

# External API for generating responses
generate_response_url = "https://adekiitan11-email-model.hf.space/generate"

# ✅ Function to Generate Email Responses
def generate_email_response(email_content):
    # Get the absolute path to the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the absolute path to the CSV file
    dataset_path = os.path.join(script_dir, 'reformatted_dataset.csv')

    # Load and parse the dataset
    df = pd.read_csv(dataset_path)
    qa_dict = {}

    for index, row in df.iterrows():
        match = re.search(r"<s>\[INST\](.*?)\[/INST\](.*?)</s>", row[0], re.DOTALL)
        if match:
            question = " ".join(match.group(1).strip().lower().split())  # Normalize spaces
            response = match.group(2).strip()
            qa_dict[question] = response

    user_query = {"text": f"{email_content}"}
    # Normalize user query
    normalized_query = " ".join(email_content.strip().lower().split())

    # If query is not in dataset, return a default response
    if normalized_query not in qa_dict:
        return {"response": "Your request has been received, it will be processed and we will get in touch with you soon."}

    # Send request to the external API
    response = requests.post(generate_response_url, json=user_query)
    json_response = response.json()  # Ensure it's a dictionary
    generated_response = json_response.get("response", "").strip()

    # ✅ Remove the question from the response intelligently
    # - Using regex to remove variations of the question
    pattern = re.escape(normalized_query)
    cleaned_response = re.sub(pattern, "", generated_response, flags=re.IGNORECASE).strip()

    # ✅ Remove unnecessary tags like [/Certification] or extra punctuation
    cleaned_response = re.sub(r"\[.*?\]", "", cleaned_response)  # Remove bracketed content
    cleaned_response = re.sub(r"\s+", " ", cleaned_response)  # Normalize spaces
    cleaned_response = re.sub(r"^\W+|\W+$", "", cleaned_response)  # Remove leading/trailing symbols

    # ✅ Extract the first complete sentence to ensure brevity
    sentences = re.split(r"(?<=[.!?])\s+", cleaned_response)  # Split by punctuation
    final_response = sentences[0] if sentences else cleaned_response  # Keep only the first sentence

    # Normalize spaces to ensure proper matching
    normalized_question = " ".join(email_content.split())
    normalized_answer = " ".join(final_response.split())

    # Check if answer starts with question
    if normalized_answer.startswith(normalized_question):
        remaining_answer = normalized_answer[len(normalized_question):].strip()
        return remaining_answer
    else:
        remaining_answer = normalized_answer  # No change if question is not in answer

    return remaining_answer


# ✅ Example usage
#print(generate_email_response("Hello, I need information regarding Doctor  Psychiatry  Global Health Hospital  Board Certified  OnCall"))

'''
# ✅ Example Test
if __name__ == "__main__":
    user_email = "Can you confirm my appointment time?"
    ai_response = generate_email_response(user_email)
    print(f"📩 **User Query:** {user_email}")
    print(f"🤖 **AI Response:** {ai_response}")
'''

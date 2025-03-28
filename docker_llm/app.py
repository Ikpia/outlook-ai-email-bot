from flask import Flask, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

app = Flask(__name__)

# Load your fine-tuned LLaMA 2 model from Hugging Face
MODEL_NAME = "Adekiitan11/categorai-llama2-chat-finetune"  # Replace with your actual model repo
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)

@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json()
        input_text = data.get("text", "")

        if not input_text:
            return jsonify({"error": "No input text provided"}), 400

        inputs = tokenizer(input_text, return_tensors="pt")
        outputs = model.generate(**inputs, max_length=100)  # Adjust `max_length` as needed
        response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

        return jsonify({"response": response_text})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
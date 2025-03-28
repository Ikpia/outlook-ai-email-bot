import json
import torch
from transformers import GPT2Tokenizer, GPT2ForSequenceClassification, Trainer, TrainingArguments
from datasets import Dataset

# ✅ Load Dataset
dataset_path = "backend/database/datasets/template_emails.json"

with open(dataset_path, "r", encoding="utf-8") as f:
    email_templates = json.load(f)

# ✅ Prepare Data for Training
emails, labels = [], []
category_to_label = {}  # Mapping categories to numerical labels
label_to_category = {}  # Reverse mapping

for entry in email_templates:
    category = entry["Category"]
    body = entry["Body"]
    
    # Ensure unique label IDs for each category
    if category not in category_to_label:
        label_id = len(category_to_label)
        category_to_label[category] = label_id
        label_to_category[label_id] = category
    
    emails.append(body)  # Email Body
    labels.append(category_to_label[category])  # Category as Label ID

# ✅ Convert Data to Hugging Face Dataset Format
dataset = Dataset.from_dict({"text": emails, "label": labels})

# ✅ Split into Training & Validation Sets
dataset = dataset.train_test_split(test_size=0.2)

# ✅ Load Tokenizer for GPT-2 & Set Padding Token
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
tokenizer.pad_token = tokenizer.eos_token  # ✅ Use EOS token as padding

# ✅ Tokenization Function
def tokenize_function(examples):
    return tokenizer(
        examples["text"],
        truncation=True,
        padding="max_length",  # ✅ Ensure consistent padding
        max_length=512
    )

# ✅ Tokenize Dataset
tokenized_dataset = dataset.map(tokenize_function, batched=True)

# ✅ Update Dataset to Include Label Mappings
tokenized_dataset = tokenized_dataset.rename_column("label", "labels")

# ✅ Load GPT-2 for Classification & Set Padding Token
num_labels = len(category_to_label)
model = GPT2ForSequenceClassification.from_pretrained("gpt2", num_labels=num_labels)

# ✅ Set model padding token
model.config.pad_token_id = tokenizer.pad_token_id

# ✅ Define Training Arguments
training_args = TrainingArguments(
    output_dir="backend/models/gpt2_email_classifier",
    evaluation_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=2,  # ✅ Avoid large batch sizes
    per_device_eval_batch_size=2,
    num_train_epochs=3,
    weight_decay=0.01,
    save_total_limit=2,
    logging_dir="backend/logs",
    logging_steps=10
)

# ✅ Initialize Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset["train"],
    eval_dataset=tokenized_dataset["test"],
    tokenizer=tokenizer
)

# ✅ Train the Model
trainer.train()

# ✅ Save the Model & Tokenizer
model.save_pretrained("backend/models/fine_tuned_gpt2_classifier")
tokenizer.save_pretrained("backend/models/fine_tuned_gpt2_classifier")

# ✅ Save Label Mappings for Later Use
with open("backend/models/category_mappings.json", "w") as f:
    json.dump({"category_to_label": category_to_label, "label_to_category": label_to_category}, f)

print("🎉 GPT-2 Email Categorization Model Trained Successfully!")

import json
import torch
from transformers import GPT2Tokenizer, GPT2LMHeadModel, Trainer, TrainingArguments, DataCollatorForLanguageModeling
from datasets import Dataset

# ✅ Load the Training Dataset (JSON Format)
dataset_path = "backend/database/datasets/balanced_dialog_finetune_dataset.json"

with open(dataset_path, "r", encoding="utf-8") as f:
    dialog_data = json.load(f)

# ✅ Convert dataset to structured text format
texts = []
for entry in dialog_data:
    user_text = entry["dialog"][0]["text"]  # User query
    assistant_text = entry["dialog"][1]["text"]  # AI response
    formatted_text = f"User: {user_text}\nAssistant: {assistant_text}"
    texts.append(formatted_text)

# ✅ Load GPT-2 Tokenizer
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
tokenizer.pad_token = tokenizer.eos_token  # Set padding token

# ✅ Tokenize the Dataset
def tokenize_function(examples):
    return tokenizer(examples["text"], truncation=True, padding="max_length", max_length=256)

dataset = Dataset.from_dict({"text": texts})
tokenized_dataset = dataset.map(tokenize_function, batched=True)

# ✅ Split into Training & Validation Sets
split_ratio = 0.8  # 80% Training, 20% Validation
train_size = int(split_ratio * len(tokenized_dataset))
train_dataset = tokenized_dataset.select(range(train_size))
val_dataset = tokenized_dataset.select(range(train_size, len(tokenized_dataset)))

# ✅ Load Pretrained GPT-2 Model
model = GPT2LMHeadModel.from_pretrained("gpt2")

# ✅ Define Training Arguments
training_args = TrainingArguments(
    output_dir="backend/models/gpt2_email_model",
    eval_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=2,
    per_device_eval_batch_size=2,
    num_train_epochs=3,
    weight_decay=0.01,
    save_total_limit=2,
    logging_dir="backend/logs",
    logging_steps=10
)

# ✅ Define Data Collator
data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

# ✅ Initialize Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    tokenizer=tokenizer,
    data_collator=data_collator
)

# ✅ Start Fine-Tuning
trainer.train()

# ✅ Save the Fine-Tuned Model
model.save_pretrained("backend/models/fine_tuned_gpt2")
tokenizer.save_pretrained("backend/models/fine_tuned_gpt2")

print("🎉 GPT-2 Fine-Tuning Complete! Model saved in 'backend/models/fine_tuned_gpt2'.")

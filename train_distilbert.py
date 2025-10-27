from transformers import DistilBertTokenizer, DistilBertForSequenceClassification, Trainer, TrainingArguments
import json
import torch
from torch.utils.data import Dataset

# Custom Dataset
class CorrectionDataset(Dataset):
    def __init__(self, corrections, tokenizer, max_length=128):
        self.input_texts = list(corrections.keys())
        self.target_texts = list(corrections.values())
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.input_texts)

    def __getitem__(self, idx):
        input_text = self.input_texts[idx]
        target_text = self.target_texts[idx]
        encoding = self.tokenizer(
            input_text,
            target_text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "labels": torch.tensor(1)  # Binary classification (corrected vs uncorrected)
        }

# Load corrections
with open("corrections.json", "r", encoding="utf-8") as f:
    corrections = json.load(f)

# Initialize tokenizer and model
tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")
model = DistilBertForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=2)

# Prepare dataset
dataset = CorrectionDataset(corrections, tokenizer)

# Training arguments
training_args = TrainingArguments(
    output_dir="./distilbert_refiner",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    warmup_steps=50,
    weight_decay=0.01,
    logging_dir="./logs",
    logging_steps=10,
)

# Initialize Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
)

# Train the model
trainer.train()

# Save the trained model
model.save_pretrained("./distilbert_refiner")
tokenizer.save_pretrained("./distilbert_refiner")
print("Training complete! Model saved in ./distilbert_refiner")
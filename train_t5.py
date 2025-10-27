from transformers import T5Tokenizer, T5ForConditionalGeneration, Trainer, TrainingArguments
from datasets import Dataset
import json
import torch

# Load training data
with open("training_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)["data"]

# Prepare data
dataset = Dataset.from_dict({
    "input_text": [item["input_text"] for item in data],
    "target_text": [item["target_text"] for item in data]
})

# Initialize tokenizer and model
tokenizer = T5Tokenizer.from_pretrained("t5-small")
model = T5ForConditionalGeneration.from_pretrained("t5-small")

# Tokenize dataset
def preprocess_function(examples):
    inputs = [f"correct: {text}" for text in examples["input_text"]]
    model_inputs = tokenizer(inputs, max_length=128, truncation=True, padding="max_length")
    with tokenizer.as_target_tokenizer():
        labels = tokenizer(examples["target_text"], max_length=128, truncation=True, padding="max_length")
    model_inputs["labels"] = labels["input_ids"]
    return model_inputs

tokenized_dataset = dataset.map(preprocess_function, batched=True)

# Training arguments
training_args = TrainingArguments(
    output_dir="./t5_refiner",
    num_train_epochs=5,
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
    train_dataset=tokenized_dataset,
)

# Train the model
trainer.train()

# Save the trained model
model.save_pretrained("./t5_refiner")
tokenizer.save_pretrained("./t5_refiner")
print("Training complete! Model saved in ./t5_refiner")
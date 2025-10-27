from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

tokenizer = T5Tokenizer.from_pretrained("./t5_refiner")
model = T5ForConditionalGeneration.from_pretrained("./t5_refiner")
texts = [
    "correct: der druckabfall in der hydraulik von maschine 721-455",
    "correct: am 23. märz 2024 wurde festgestellt, dass die klingen stumpf waren"
]
for i, text in enumerate(texts):
    try:
        inputs = tokenizer(text, return_tensors="pt", max_length=256, truncation=True, padding="max_length")
        logger.info(f"Processing text {i+1} with input shape: {inputs['input_ids'].shape}")
        outputs = model.generate(**inputs, max_length=256, num_beams=10, early_stopping=True)
        logger.info(f"Generated output shape: {outputs.shape}")
        output_ids = outputs[0].tolist()
        logger.info(f"Raw output tokens: {output_ids}")
        refined_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        logger.info(f"Decoded text: {refined_text}")
        print(f"Text {i+1}: {refined_text}")
    except Exception as e:
        logger.error(f"Error processing text {i+1}: {str(e)}")
        print(f"Error processing text {i+1}: {str(e)}")
    finally:
        del model
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        model = T5ForConditionalGeneration.from_pretrained("./t5_refiner")
        logger.info(f"Model reloaded for text {i+1}")
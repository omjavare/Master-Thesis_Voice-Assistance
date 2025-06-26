import spacy
import re
import json
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

class EntityExtractor:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except Exception as e:
            logger.error(f"Error loading spaCy model: {e}. Run 'python -m spacy download en_core_web_sm'")
            raise
        self.patterns = {
            "machine_id": r"\bM\d{1,6}\b",  # Matches M followed by 1-6 digits
            "order_number": r"\b\d{3,6}\b",  # Matches 3-6 digit numbers
            "employee_id": r"\bEMP\d{3,4}\b"
        }
        self.intent_keywords = {
            "report": ["report", "issue", "problem", "down", "broken", "error", "machine"],  # Added "machine"
            "query": ["check", "status", "query", "find"],
            "assign": ["assign", "allocate", "give"],
            "identify": ["machine id", "order id", "employee id"],
            "request": ["read", "details", "show"]
        }
        self.output_file = "entities_intents.json"
        self.log = []

    def preprocess(self, text):
        text = text.lower().strip()
        doc = self.nlp(text)
        return " ".join(token.text for token in doc if not token.is_punct)

    def extract_entities(self, text):
        entities = {"machine_id": None, "order_number": None, "employee_id": None}
        text_lower = text.lower()
        for entity_type, pattern in self.patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                entities[entity_type] = matches[0]
            # Additional check for context
            if entity_type == "order_number" and "order" in text_lower:
                num_matches = re.findall(r"\b\d+\b", text)
                if num_matches:
                    entities["order_number"] = num_matches[0]
        return entities

    def classify_intent(self, text):
        text_lower = text.lower()
        for intent, keywords in self.intent_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return intent
        return "unknown"

    def log_entities_intents(self, entities, intent, transcription):
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "transcription": transcription,
            "entities": entities,
            "intent": intent
        }
        self.log.append(log_entry)
        try:
            with open(self.output_file, "w") as f:
                json.dump(self.log, f, indent=4)
            logger.info(f"Logged: Entities={entities}, Intent={intent}")
        except Exception as e:
            logger.error(f"Failed to log: {e}")
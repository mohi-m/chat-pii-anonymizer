import re
import spacy
from faker import Faker
from typing import Dict, List, Any
from sklearn.metrics import precision_score, recall_score, f1_score

from .base import BaseAnonymizer, AnonymizationResult


class RegexAnonymizer(BaseAnonymizer):
    """Regex and NLP based anonymizer implementation"""

    def __init__(self):
        # Load NLP model and Faker
        self.nlp = spacy.load("en_core_web_lg")
        self.faker = Faker()

        # Precompile regex patterns
        self.regex_patterns = {
            "EMAIL": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
            "PHONE": re.compile(
                r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}(?:x\d+)?\b"
            ),
            "IP": re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
            "CREDIT_CARD": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
            "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
            "US_PASSPORT": re.compile(r"\b\d{9}\b"),
            "GPS_COORDINATES": re.compile(
                r"\b-?\d{1,2}\.\d{5,},\s*-?\d{1,3}\.\d{5,}\b"
            ),
            "MEDICAL_LICENSE": re.compile(r"\b[A-Z]{1,2}\d{5,10}\b"),
            "US_BANK_NUMBER": re.compile(r"\b\d{8,17}\b"),
        }

        # US Driver License patterns
        self.us_driver_license_patterns = [
            re.compile(r"\b[A-Z]{1}\d{7}\b"),  # e.g., NY, NJ
            re.compile(r"\b\d{7,9}\b"),  # e.g., CA, TX
            re.compile(r"\b[A-Z]{2}\d{6,8}\b"),  # e.g., FL, IL
        ]

    def anonymize_text(self, text: str) -> AnonymizationResult:
        matches = []  # Each match is a dict: {'start', 'end', 'label'}

        # Collect structured PII using regex
        for label, pattern in self.regex_patterns.items():
            for match in pattern.finditer(text):
                matches.append(
                    {"start": match.start(), "end": match.end(), "label": label}
                )

        # Collect US driver licenses
        for pattern in self.us_driver_license_patterns:
            for match in pattern.finditer(text):
                matches.append(
                    {
                        "start": match.start(),
                        "end": match.end(),
                        "label": "US_DRIVER_LICENSE",
                    }
                )

        # Use NLP for entity recognition
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "GPE", "LOC"]:
                matches.append(
                    {"start": ent.start_char, "end": ent.end_char, "label": ent.label_}
                )

        # Sort matches by starting index
        matches.sort(key=lambda m: (m["start"], -m["end"]))

        # Filter out overlapping spans
        filtered = []
        current_end = 0
        for m in matches:
            if m["start"] >= current_end:
                filtered.append(m)
                current_end = m["end"]

        # Reconstruct the anonymized text
        anonymized_text = ""
        last_index = 0
        for m in filtered:
            anonymized_text += text[last_index : m["start"]]
            anonymized_text += f"[{m['label']}]"
            last_index = m["end"]
        anonymized_text += text[last_index:]

        return AnonymizationResult(text=anonymized_text, entities=filtered)

    def evaluate_anonymization(
        self, raw_text: str, labeled_text: str
    ) -> Dict[str, float]:
        anonymized = self.anonymize_text(raw_text)
        expected_entities = re.findall(r"\[(.*?)\]", labeled_text)
        anonymized_entities = re.findall(r"\[(.*?)\]", anonymized.text)

        y_true, y_pred = [], []
        for entity in expected_entities:
            y_true.append(1)
            y_pred.append(1 if entity in anonymized_entities else 0)
        for entity in anonymized_entities:
            if entity not in expected_entities:
                y_true.append(0)
                y_pred.append(1)

        return {
            "Precision": precision_score(y_true, y_pred, zero_division=0),
            "Recall": recall_score(y_true, y_pred, zero_division=0),
            "F1-score": f1_score(y_true, y_pred, zero_division=0),
            "anonymized": anonymized.text,
        }

    def generate_test_data(self, num_samples: int = 5) -> List[tuple]:
        test_cases = []
        for _ in range(num_samples):
            name = self.faker.name()
            email = self.faker.email()
            phone = self.faker.phone_number()
            clean_phone = phone.split(" x")[0]
            ip = self.faker.ipv4()
            credit_card = self.faker.credit_card_number()
            ssn = self.faker.ssn()
            bank_number = self.faker.random_int(min=10000000, max=99999999999999999)
            passport = self.faker.random_int(min=100000000, max=999999999)
            latitude, longitude = self.faker.latitude(), self.faker.longitude()
            medical_license = f"{self.faker.random_uppercase_letter()}{self.faker.random_int(10000, 999999)}"

            raw_text = (
                f"Hello, I'm {name}. Contact me at {email} or call {clean_phone}. "
                f"My IP is {ip}, and my credit card is {credit_card}. "
                f"SSN: {ssn}, Bank: {bank_number}, Passport: {passport}, "
                f"GPS: {latitude}, {longitude}, Medical License: {medical_license}."
            )
            expected_labeled = (
                f"Hello, I'm [PERSON]. Contact me at [EMAIL] or call [PHONE]. "
                f"My IP is [IP], and my credit card is [CREDIT_CARD]. "
                f"SSN: [SSN], Bank: [US_BANK_NUMBER], Passport: [US_PASSPORT], "
                f"GPS: [GPS_COORDINATES], Medical License: [MEDICAL_LICENSE]."
            )
            test_cases.append((raw_text, expected_labeled))
        return test_cases

    def evaluate_test_cases(self, test_cases: List[tuple]) -> Dict[str, float]:
        y_true, y_pred = [], []
        for raw, expected in test_cases:
            anonymized = self.anonymize_text(raw)
            expected_entities = re.findall(r"\[(.*?)\]", expected)
            anonymized_entities = re.findall(r"\[(.*?)\]", anonymized.text)

            for entity in expected_entities:
                y_true.append(1)
                y_pred.append(1 if entity in anonymized_entities else 0)
            for entity in anonymized_entities:
                if entity not in expected_entities:
                    y_true.append(0)
                    y_pred.append(1)

        return {
            "Precision": precision_score(y_true, y_pred, zero_division=0),
            "Recall": recall_score(y_true, y_pred, zero_division=0),
            "F1-score": f1_score(y_true, y_pred, zero_division=0),
        }

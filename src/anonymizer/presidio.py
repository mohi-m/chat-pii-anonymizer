from faker import Faker
from typing import Dict, List, Any
from sklearn.metrics import precision_score, recall_score, f1_score
import re

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_anonymizer import AnonymizerEngine

from .base import BaseAnonymizer, AnonymizationResult


class USBankNumberRecognizer(PatternRecognizer):
    def __init__(self):
        patterns = [Pattern("US_BANK_NUMBER", r"\b(?:\d{8}|\d{10,17})\b", 0.5)]
        super().__init__(
            supported_entity="US_BANK_NUMBER",
            patterns=patterns,
            context=[],
            name="USBankNumberRecognizer",
        )


class USPassportRecognizer(PatternRecognizer):
    def __init__(self):
        patterns = [Pattern("US_PASSPORT", r"\b\d{9}\b", 0.5)]
        super().__init__(
            supported_entity="US_PASSPORT",
            patterns=patterns,
            context=[],
            name="USPassportRecognizer",
        )


class MedicalLicenseRecognizer(PatternRecognizer):
    def __init__(self):
        patterns = [Pattern("MEDICAL_LICENSE", r"\b[A-Z]{1,2}\d{5,10}\b", 0.5)]
        super().__init__(
            supported_entity="MEDICAL_LICENSE",
            patterns=patterns,
            context=[],
            name="MedicalLicenseRecognizer",
        )


class PresidioAnonymizer(BaseAnonymizer):
    """Presidio-based anonymizer implementation"""

    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self.faker = Faker()

        # Add custom recognizers
        self.analyzer.registry.add_recognizer(USBankNumberRecognizer())
        self.analyzer.registry.add_recognizer(USPassportRecognizer())
        self.analyzer.registry.add_recognizer(MedicalLicenseRecognizer())

    def anonymize_text(self, text: str) -> AnonymizationResult:
        results = self.analyzer.analyze(text=text, language="en")
        anonymized_result = self.anonymizer.anonymize(
            text=text, analyzer_results=results
        )

        # Convert Presidio results to our format
        entities = []
        for ent in results:
            entities.append(
                {"start": ent.start, "end": ent.end, "label": ent.entity_type}
            )

        return AnonymizationResult(text=anonymized_result.text, entities=entities)

    def evaluate_anonymization(
        self, raw_text: str, labeled_text: str
    ) -> Dict[str, float]:
        anonymized = self.anonymize_text(raw_text)
        expected_entities = re.findall(r"<(.*?)>", labeled_text)
        anonymized_entities = re.findall(r"<(.*?)>", anonymized.text)

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
            location = self.faker.city()
            ip = self.faker.ipv4()
            credit_card = self.faker.credit_card_number()
            bank_number = self.faker.random_int(min=10000000, max=99999999999999999)
            passport = self.faker.random_int(min=100000000, max=999999999)
            medical_license = f"{self.faker.random_uppercase_letter()}{self.faker.random_int(10000, 999999)}"
            ssn = self.faker.ssn()

            raw_text = (
                f"Hello, I'm {name}. Contact me at {email} or call {clean_phone}. "
                f"I'm from {location}. My IP is {ip}, my credit card is {credit_card}, "
                f"my bank account is {bank_number}, my passport is {passport}, "
                f"my medical license is {medical_license}, and my SSN is {ssn}."
            )
            expected_labeled = (
                f"Hello, I'm <PERSON>. Contact me at <EMAIL_ADDRESS> or call <PHONE_NUMBER>. "
                f"I'm from <LOCATION>. My IP is <IP_ADDRESS>, my credit card is <CREDIT_CARD>, "
                f"my bank account is <US_BANK_NUMBER>, my passport is <US_PASSPORT>, "
                f"my medical license is <MEDICAL_LICENSE>, and my SSN is <US_SSN>."
            )
            test_cases.append((raw_text, expected_labeled))
        return test_cases

    def evaluate_test_cases(self, test_cases: List[tuple]) -> Dict[str, float]:
        y_true, y_pred = [], []
        for raw, expected in test_cases:
            anonymized = self.anonymize_text(raw)
            expected_entities = re.findall(r"<(.*?)>", expected)
            anonymized_entities = re.findall(r"<(.*?)>", anonymized.text)

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

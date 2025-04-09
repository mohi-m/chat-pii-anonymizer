import re
import tkinter as tk
from tkinter import scrolledtext
from faker import Faker
from sklearn.metrics import precision_score, recall_score, f1_score

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_anonymizer import AnonymizerEngine

# --- Custom Recognizers for Additional PII Types ---

class USBankNumberRecognizer(PatternRecognizer):
    def __init__(self):
        patterns = [Pattern("US_BANK_NUMBER", r"\b(?:\d{8}|\d{10,17})\b", 0.5)]
        super().__init__(supported_entity="US_BANK_NUMBER", patterns=patterns, context=[], name="USBankNumberRecognizer")

# class USDriverLicenseRecognizer(PatternRecognizer):
#     def __init__(self):
#         patterns = [
#             Pattern("US_DRIVER_LICENSE", r"\b[A-Z]{1}\d{7}\b", 0.5),
#             Pattern("US_DRIVER_LICENSE", r"\b\d{7,9}\b", 0.5),
#             Pattern("US_DRIVER_LICENSE", r"\b[A-Z]{2}\d{6,8}\b", 0.5)
#         ]
#         super().__init__(supported_entity="US_DRIVER_LICENSE", patterns=patterns, context=[], name="USDriverLicenseRecognizer")

class USPassportRecognizer(PatternRecognizer):
    def __init__(self):
        patterns = [Pattern("US_PASSPORT", r"\b\d{9}\b", 0.5)]
        super().__init__(supported_entity="US_PASSPORT", patterns=patterns, context=[], name="USPassportRecognizer")

class MedicalLicenseRecognizer(PatternRecognizer):
    def __init__(self):
        patterns = [Pattern("MEDICAL_LICENSE", r"\b[A-Z]{1,2}\d{5,10}\b", 0.5)]
        super().__init__(supported_entity="MEDICAL_LICENSE", patterns=patterns, context=[], name="MedicalLicenseRecognizer")


# --- Initialize Presidio Analyzer and Anonymizer ---

analyzer = AnalyzerEngine()
# Add our custom recognizers to the analyzer registry
analyzer.registry.add_recognizer(USBankNumberRecognizer())
# analyzer.registry.add_recognizer(USDriverLicenseRecognizer())
analyzer.registry.add_recognizer(USPassportRecognizer())
analyzer.registry.add_recognizer(MedicalLicenseRecognizer())

anonymizer = AnonymizerEngine()


def presidio_anonymize(text):
    """
    Uses Presidio's AnalyzerEngine and AnonymizerEngine (with default anonymization)
    to detect and mask PII in the text.
    """
    results = analyzer.analyze(text=text, language="en")
    anonymized_result = anonymizer.anonymize(text=text, analyzer_results=results)
    return anonymized_result.text


# --- Evaluation Functions ---

def evaluate_anonymization(raw_text, labeled_text):
    """
    Anonymizes the raw text using Presidio and compares the output with the expected labeled text.
    This function extracts tokens enclosed in angle brackets (e.g., <PERSON>) from both strings
    and computes precision, recall, and F1-score.
    """
    anonymized = presidio_anonymize(raw_text)
    
    expected_entities = re.findall(r"<(.*?)>", labeled_text)
    anonymized_entities = re.findall(r"<(.*?)>", anonymized)
    
    y_true, y_pred = [], []
    for entity in expected_entities:
        y_true.append(1)
        y_pred.append(1 if entity in anonymized_entities else 0)
    for entity in anonymized_entities:
        if entity not in expected_entities:
            y_true.append(0)
            y_pred.append(1)
    
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall    = recall_score(y_true, y_pred, zero_division=0)
    f1        = f1_score(y_true, y_pred, zero_division=0)
    
    return {"Precision": precision, "Recall": recall, "F1-score": f1, "anonymized": anonymized}


def generate_test_data(num_samples=5):
    """
    Generates synthetic test cases containing all the specified PII types using Faker.
    The expected labeled text uses angle-bracket tokens.
    """
    fake = Faker()
    test_cases = []
    for _ in range(num_samples):
        name            = fake.name()
        email           = fake.email()
        phone           = fake.phone_number()
        # For location, we'll use a city name
        location        = fake.city()
        ip              = fake.ipv4()
        credit_card     = fake.credit_card_number()
        # Ensure bank account numbers are not exactly 9 digits:
        us_bank         = fake.random_int(min=10000000, max=99999999) if fake.random_int(0,1)==0 else fake.random_int(min=1000000000, max=99999999999999999)
        us_driver_license = f"{fake.random_uppercase_letter()}{fake.random_int(1000000, 9999999)}"
        us_passport     = fake.random_int(min=100000000, max=999999999)  # exactly 9 digits
        medical_license = f"{fake.random_uppercase_letter()}{fake.random_int(10000, 999999)}"
        ssn             = fake.ssn()
        
        raw_text = (
            f"Hello, I'm {name}. Contact me at {email} or call {phone}. "
            f"I'm from {location}. My IP is {ip}, my credit card is {credit_card}, "
            f"my bank account is {us_bank}, my driver's license is {us_driver_license}, "
            f"my passport is {us_passport}, my medical license is {medical_license}, "
            f"and my SSN is {ssn}."
        )
        expected_labeled = (
            f"Hello, I'm <PERSON>. Contact me at <EMAIL_ADDRESS> or call <PHONE_NUMBER>. "
            f"I'm from <LOCATION>. My IP is <IP_ADDRESS>, my credit card is <CREDIT_CARD>, "
            f"my bank account is <US_BANK_NUMBER>, my driver's license is <US_DRIVER_LICENSE>, "
            f"my passport is <US_PASSPORT>, my medical license is <MEDICAL_LICENSE>, "
            f"and my SSN is <US_SSN>."
        )
        test_cases.append((raw_text, expected_labeled))
    return test_cases


def evaluate_test_cases(test_cases):
    """
    Evaluates a list of synthetic test cases and aggregates precision, recall, and F1-score.
    """
    y_true, y_pred = [], []
    for raw, expected in test_cases:
        result = evaluate_anonymization(raw, expected)
        expected_entities = re.findall(r"<(.*?)>", expected)
        anonymized_entities = re.findall(r"<(.*?)>", result["anonymized"])
        for entity in expected_entities:
            y_true.append(1)
            y_pred.append(1 if entity in anonymized_entities else 0)
        for entity in anonymized_entities:
            if entity not in expected_entities:
                y_true.append(0)
                y_pred.append(1)
    
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall    = recall_score(y_true, y_pred, zero_division=0)
    f1        = f1_score(y_true, y_pred, zero_division=0)
    return {"Precision": precision, "Recall": recall, "F1-score": f1}

def evaluate_test_cases_new(test_cases):
    """
    Evaluates a list of synthetic test cases and aggregates precision, recall, and F1-score.
    """
    y_true, y_pred = [], []
    for raw, expected in test_cases:
        result = evaluate_anonymization(raw, expected)
        expected_entities = re.findall(r"\[(.*?)\]", expected)
        anonymized_entities = re.findall(r"<(.*?)>", result["anonymized"])
        for entity in expected_entities:
            y_true.append(1)
            y_pred.append(1 if entity in anonymized_entities else 0)
        for entity in anonymized_entities:
            if entity not in expected_entities:
                y_true.append(0)
                y_pred.append(1)
    
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall    = recall_score(y_true, y_pred, zero_division=0)
    f1        = f1_score(y_true, y_pred, zero_division=0)
    return {"Precision": precision, "Recall": recall, "F1-score": f1}

def evaluate_external_test_cases(file_path):
    """
    Reads external test cases from a file and evaluates them.
    The file should contain raw text and expected labeled text in a specific format.
    Only processes the first 10 rows of the file, ignoring the header.
    """
    test_cases = []
    with open(file_path, 'r') as f:
        import csv
        reader = csv.reader(f)
        next(reader)  # Skip the header row
        for i, row in enumerate(reader):
            if i >= 10:  # Limit to the first 10 rows
                break
            raw_text, expected_labeled = row[1], row[0]
            # Use regex to replace multiple patterns efficiently
            replacements = {
                r"FULLNAME_\d+|FIRSTNAME_\d+|LASTNAME_\d+": "PERSON",
                r"EMAIL_\d+": "EMAIL_ADDRESS",
                r"PHONE_NUMBER": "PHONE_NUMBER",
                r"CITY_\d+|STATE_\d+|COUNTY_\d+|STREET_\d+|STREETADDRESS_\d+|SECONDARYADDRESS_\d+|ZIPCODE_\d+": "LOCATION",
                r"IPV4_\d+|IPV6_\d+|IP_\d+": "IP_ADDRESS",
                r"CREDITCARDNUMBER_\d+": "CREDIT_CARD",
                r"US_BANK_NUMBER": "US_BANK_NUMBER",
                r"US_DRIVER_LICENSE": "US_DRIVER_LICENSE",
                r"US_PASSPORT": "US_PASSPORT",
                r"MEDICAL_LICENSE": "MEDICAL_LICENSE",
                r"US_SSN": "US_SSN"
            }
            for pattern, replacement in replacements.items():
                expected_labeled = re.sub(pattern, replacement, expected_labeled)
            
            test_cases.append((raw_text.strip(), expected_labeled.strip()))
    return test_cases


# --- GUI Implementation using Tkinter ---

def run_gui():
    root = tk.Tk()
    root.title("Chat PII Anonymizer & Evaluator (Presidio with Custom Recognizers)")

    # Custom Evaluation Section
    frame_evaluation = tk.LabelFrame(root, text="Evaluate Anonymization (Custom Input)", padx=10, pady=10)
    frame_evaluation.pack(padx=10, pady=5, fill="both", expand=True)
    tk.Label(frame_evaluation, text="Raw text:").pack(anchor="w")
    raw_text_box = scrolledtext.ScrolledText(frame_evaluation, height=5, width=160)
    raw_text_box.pack(padx=5, pady=5)
    tk.Label(frame_evaluation, text="Labeled text (with expected <LABEL> tokens):").pack(anchor="w")
    labeled_text_box = scrolledtext.ScrolledText(frame_evaluation, height=5, width=160)
    labeled_text_box.pack(padx=5, pady=5)
    result_box_eval = scrolledtext.ScrolledText(frame_evaluation, height=5, width=160)
    result_box_eval.pack(padx=5, pady=5)

    def evaluate_input():
        raw = raw_text_box.get("1.0", tk.END).strip()
        labeled = labeled_text_box.get("1.0", tk.END).strip()
        if not raw or not labeled:
            result_box_eval.delete("1.0", tk.END)
            result_box_eval.insert(tk.END, "Please enter both raw and labeled text.")
            return
        metrics = evaluate_anonymization(raw, labeled)
        result_box_eval.delete("1.0", tk.END)
        result_box_eval.insert(tk.END, f"Anonymized Text:\n{metrics['anonymized']}\n")
        result_box_eval.insert(tk.END, f"Precision: {metrics['Precision']:.2f}\n")
        result_box_eval.insert(tk.END, f"Recall: {metrics['Recall']:.2f}\n")
        result_box_eval.insert(tk.END, f"F1-score: {metrics['F1-score']:.2f}\n")
    
    tk.Button(frame_evaluation, text="Calculate Accuracy", command=evaluate_input).pack(pady=5)

    # Synthetic Test Cases Section
    frame_test_data = tk.LabelFrame(root, text="Synthetic Test Cases Evaluation", padx=10, pady=10)
    frame_test_data.pack(padx=10, pady=5, fill="both", expand=True)
    result_box_test = scrolledtext.ScrolledText(frame_test_data, height=16, width=160)
    result_box_test.pack(padx=5, pady=5)

    def run_test_cases():
        # test_cases = evaluate_external_test_cases("test-data/PII43k.csv")
        # overall_metrics = evaluate_test_cases_new(test_cases)
        test_cases = generate_test_data(10)
        overall_metrics = evaluate_test_cases(test_cases)

        result_box_test.delete("1.0", tk.END)
        result_box_test.insert(tk.END, "Synthetic Test Cases Evaluation:\n")
        for i, (raw, expected) in enumerate(test_cases, start=1):
            anonymized = presidio_anonymize(raw)
            result_box_test.insert(tk.END, f"\nTest Case {i}:\n")
            result_box_test.insert(tk.END, f"Raw: {raw}\n")
            result_box_test.insert(tk.END, f"Expected: {expected}\n")
            result_box_test.insert(tk.END, f"Anonymized: {anonymized}\n")
        result_box_test.insert(tk.END, f"\nOverall Metrics:\n")
        result_box_test.insert(tk.END, f"Precision: {overall_metrics['Precision']:.2f}\n")
        result_box_test.insert(tk.END, f"Recall: {overall_metrics['Recall']:.2f}\n")
        result_box_test.insert(tk.END, f"F1-score: {overall_metrics['F1-score']:.2f}\n")
    
    tk.Button(frame_test_data, text="Run Test Cases", command=run_test_cases).pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    run_gui()

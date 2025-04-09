import re
import spacy
import logging
import tkinter as tk
from faker import Faker
from tkinter import scrolledtext
from sklearn.metrics import precision_score, recall_score, f1_score

# Set up logging
logging.basicConfig(filename="anonymizer.log", level=logging.INFO, 
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Load NLP model and Faker
nlp = spacy.load("en_core_web_lg")
faker = Faker()

# Precompile regex patterns for structured PII
regex_patterns = {
    "EMAIL": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "PHONE": re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}(?:x\d+)?\b"),
    "IP": re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
    "CREDIT_CARD": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
    "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "US_PASSPORT": re.compile(r"\b\d{9}\b"),
    "GPS_COORDINATES": re.compile(r"\b-?\d{1,2}\.\d{5,},\s*-?\d{1,3}\.\d{5,}\b"),
    "MEDICAL_LICENSE": re.compile(r"\b[A-Z]{1,2}\d{5,10}\b"),
    "US_BANK_NUMBER": re.compile(r"\b\d{8,17}\b"),
}

# Precompiled US Driver License patterns (covers most states)
us_driver_license_patterns = [
    re.compile(r"\b[A-Z]{1}\d{7}\b"),       # e.g., NY, NJ
    re.compile(r"\b\d{7,9}\b"),             # e.g., CA, TX
    re.compile(r"\b[A-Z]{2}\d{6,8}\b")       # e.g., FL, IL
]

def anonymize_text(text):
    """
    Anonymize text by gathering all regex and NLP-based PII matches, sorting them,
    filtering overlapping spans, and replacing them in one pass.
    """
    original_text = text
    matches = []  # Each match is a dict: {'start', 'end', 'label'}

    # Step 1: Collect structured PII using regex
    for label, pattern in regex_patterns.items():
        for match in pattern.finditer(text):
            matches.append({
                'start': match.start(),
                'end': match.end(),
                'label': label
            })

    # Collect US driver licenses
    for pattern in us_driver_license_patterns:
        for match in pattern.finditer(text):
            matches.append({
                'start': match.start(),
                'end': match.end(),
                'label': "US_DRIVER_LICENSE"
            })

    # Step 2: Use NLP for entity recognition (PERSON, GPE, LOC)
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "GPE", "LOC"]:
            matches.append({
                'start': ent.start_char,
                'end': ent.end_char,
                'label': ent.label_
            })

    # Step 3: Sort matches by starting index; if same start, use longer match first.
    matches.sort(key=lambda m: (m['start'], -m['end']))

    # Step 4: Filter out overlapping spans (greedy approach)
    filtered = []
    current_end = 0
    for m in matches:
        if m['start'] >= current_end:
            filtered.append(m)
            current_end = m['end']

    # Step 5: Reconstruct the anonymized text in one pass.
    anonymized_text = ""
    last_index = 0
    for m in filtered:
        anonymized_text += text[last_index:m['start']]
        anonymized_text += f"[{m['label']}]"
        last_index = m['end']
    anonymized_text += text[last_index:]

    logging.info(f"Original: {original_text}")
    logging.info(f"Anonymized: {anonymized_text}")
    return anonymized_text

def evaluate_anonymization(raw_text, labeled_text):
    """
    Given raw text and its labeled version, run the anonymizer on the raw text and
    compare the anonymized tokens with those in the labeled text. Returns accuracy metrics.
    """
    anonymized = anonymize_text(raw_text)
    expected_entities = re.findall(r"\[(.*?)\]", labeled_text)
    anonymized_entities = re.findall(r"\[(.*?)\]", anonymized)
    
    y_true, y_pred = [], []
    for entity in expected_entities:
        y_true.append(1)
        y_pred.append(1 if entity in anonymized_entities else 0)
    for entity in anonymized_entities:
        if entity not in expected_entities:
            y_true.append(0)
            y_pred.append(1)
            
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    return {"Precision": precision, "Recall": recall, "F1-score": f1, "anonymized": anonymized}

def generate_test_data(num_samples=5):
    """
    Generate synthetic test cases containing all PII types.
    Returns a list of tuples: (raw_text, expected_labeled_text).
    """
    test_cases = []
    for _ in range(num_samples):
        name = faker.name()
        email = faker.email()
        phone = faker.phone_number()
        clean_phone = phone.split(' x')[0]  # Removes anything after ' x'
        ip = faker.ipv4()
        credit_card = faker.credit_card_number()
        ssn = faker.ssn()
        bank_number = faker.random_int(min=10000000, max=99999999999999999)
        passport = faker.random_int(min=100000000, max=999999999)
        latitude, longitude = faker.latitude(), faker.longitude()
        medical_license = f"{faker.random_uppercase_letter()}{faker.random_int(10000, 999999)}"

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

def evaluate_test_cases(test_cases):
    """
    Evaluate a list of synthetic test cases.
    Returns aggregated precision, recall, and F1-score.
    """
    y_true, y_pred = [], []
    for raw, expected in test_cases:
        anonymized = anonymize_text(raw)
        expected_entities = re.findall(r"\[(.*?)\]", expected)
        anonymized_entities = re.findall(r"\[(.*?)\]", anonymized)
        for entity in expected_entities:
            y_true.append(1)
            y_pred.append(1 if entity in anonymized_entities else 0)
        for entity in anonymized_entities:
            if entity not in expected_entities:
                y_true.append(0)
                y_pred.append(1)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    return {"Precision": precision, "Recall": recall, "F1-score": f1}

def run_gui():
    root = tk.Tk()
    root.title("Chat Anonymizer & Evaluator")

    # --- Anonymize Text Section ---
    frame_anonymize = tk.LabelFrame(root, text="Anonymize Text", padx=10, pady=10)
    frame_anonymize.pack(padx=10, pady=5, fill="both", expand=True)

    tk.Label(frame_anonymize, text="Enter chat text:").pack(anchor="w")
    input_box = scrolledtext.ScrolledText(frame_anonymize, height=5, width=140)
    input_box.pack(padx=5, pady=5)

    result_box_anonymize = scrolledtext.ScrolledText(frame_anonymize, height=5, width=140)
    result_box_anonymize.pack(padx=5, pady=5)

    def anonymize_input():
        text = input_box.get("1.0", tk.END).strip()
        if not text:
            result_box_anonymize.delete("1.0", tk.END)
            result_box_anonymize.insert(tk.END, "Please enter text to anonymize.")
            return
        anonymized = anonymize_text(text)
        result_box_anonymize.delete("1.0", tk.END)
        result_box_anonymize.insert(tk.END, anonymized)

    tk.Button(frame_anonymize, text="Anonymize", command=anonymize_input).pack(pady=5)

    # --- Custom Evaluation Section ---
    frame_evaluation = tk.LabelFrame(root, text="Evaluate Anonymization Accuracy (Custom Input)", padx=10, pady=10)
    frame_evaluation.pack(padx=10, pady=5, fill="both", expand=True)

    tk.Label(frame_evaluation, text="Raw text:").pack(anchor="w")
    raw_text_box = scrolledtext.ScrolledText(frame_evaluation, height=5, width=140)
    raw_text_box.pack(padx=5, pady=5)

    tk.Label(frame_evaluation, text="Labeled text (with expected [LABEL] tokens):").pack(anchor="w")
    labeled_text_box = scrolledtext.ScrolledText(frame_evaluation, height=5, width=140)
    labeled_text_box.pack(padx=5, pady=5)

    result_box_eval = scrolledtext.ScrolledText(frame_evaluation, height=5, width=140)
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
        result_box_eval.insert(tk.END, f"Anonymized Text: {metrics['anonymized']}\n")
        result_box_eval.insert(tk.END, f"Precision: {metrics['Precision']:.2f}\n")
        result_box_eval.insert(tk.END, f"Recall: {metrics['Recall']:.2f}\n")
        result_box_eval.insert(tk.END, f"F1-score: {metrics['F1-score']:.2f}\n")

    tk.Button(frame_evaluation, text="Calculate Accuracy", command=evaluate_input).pack(pady=5)

    # --- Synthetic Test Cases Section ---
    frame_test_data = tk.LabelFrame(root, text="Test Data Evaluation (Synthetic Test Cases)", padx=10, pady=10)
    frame_test_data.pack(padx=10, pady=5, fill="both", expand=True)

    result_box_test = scrolledtext.ScrolledText(frame_test_data, height=10, width=140)
    result_box_test.pack(padx=5, pady=5)

    def run_test_cases():
        test_cases = generate_test_data(10)
        metrics = evaluate_test_cases(test_cases)
        result_box_test.delete("1.0", tk.END)
        result_box_test.insert(tk.END, "Synthetic Test Cases Evaluation:\n")
        for i, (raw, expected) in enumerate(test_cases, start=1):
            anonymized = anonymize_text(raw)
            result_box_test.insert(tk.END, f"\nTest Case {i}:\n")
            result_box_test.insert(tk.END, f"Raw: {raw}\n")
            result_box_test.insert(tk.END, f"Expected: {expected}\n")
            result_box_test.insert(tk.END, f"Anonymized: {anonymized}\n")
        result_box_test.insert(tk.END, f"\nOverall Metrics:\n")
        result_box_test.insert(tk.END, f"Precision: {metrics['Precision']:.2f}\n")
        result_box_test.insert(tk.END, f"Recall: {metrics['Recall']:.2f}\n")
        result_box_test.insert(tk.END, f"F1-score: {metrics['F1-score']:.2f}\n")

    tk.Button(frame_test_data, text="Run Test Cases", command=run_test_cases).pack(pady=5)

    root.mainloop()

# Run the GUI
run_gui()

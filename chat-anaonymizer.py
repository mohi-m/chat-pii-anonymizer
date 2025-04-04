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

# Load NLP model and faker
nlp = spacy.load("en_core_web_lg")
faker = Faker()

# Define regex patterns for structured PII
patterns = {
    "EMAIL": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "PHONE": r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "IP": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b",
    "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
    "US_BANK_NUMBER": r"\b\d{8,17}\b",
    "US_PASSPORT": r"\b\d{9}\b",
    "GPS_COORDINATES": r"\b-?\d{1,2}\.\d{5,},\s*-?\d{1,3}\.\d{5,}\b",
    "MEDICAL_LICENSE": r"\b[A-Z]{2}\d{5,10}\b"
}

# US Driver License formats (covers most states)
us_driver_license_patterns = [
    r"\b[A-Z]{1}\d{7}\b",       # NY, NJ, etc.
    r"\b\d{1,9}\b",             # CA, TX, etc.
    r"\b[A-Z]{2}\d{6,8}\b"      # FL, IL, etc.
]

# Function to anonymize text
def anonymize_text(text):
    original_text = text
    
    # Step 1: Anonymize structured PII using regex
    for label, pattern in patterns.items():
        text = re.sub(pattern, f"[{label}]", text)

    # Step 2: Anonymize US driver licenses
    for pattern in us_driver_license_patterns:
        text = re.sub(pattern, "[US_DRIVER_LICENSE]", text)

    # Step 3: Use NLP model for entity anonymization (Names, Locations, etc.)
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "GPE", "LOC"]:
            text = text.replace(ent.text, f"[{ent.label_}]")

    logging.info(f"Original: {original_text}")
    logging.info(f"Anonymized: {text}")
    return text

# Function to generate synthetic test cases
def generate_test_data(num_samples=5):
    test_cases = []
    for _ in range(num_samples):
        name = faker.name()
        email = faker.email()
        phone = faker.phone_number()
        ip = faker.ipv4()
        credit_card = faker.credit_card_number()
        ssn = faker.ssn()
        bank_number = faker.random_int(min=10000000, max=99999999999999999)
        passport = faker.random_int(min=100000000, max=999999999)
        latitude, longitude = faker.latitude(), faker.longitude()
        medical_license = f"{faker.random_uppercase_letter()}{faker.random_int(10000, 999999)}"

        original_text = (
            f"Hello, I'm {name}. Contact me at {email} or call {phone}. "
            f"My IP is {ip}, and my credit card is {credit_card}. "
            f"SSN: {ssn}, Bank: {bank_number}, Passport: {passport}, "
            f"GPS: {latitude}, {longitude}, Medical License: {medical_license}."
        )
        expected_output = (
            f"Hello, I'm [PERSON]. Contact me at [EMAIL] or call [PHONE]. "
            f"My IP is [IP], and my credit card is [CREDIT_CARD]. "
            f"SSN: [SSN], Bank: [US_BANK_NUMBER], Passport: [US_PASSPORT], "
            f"GPS: [GPS_COORDINATES], Medical License: [MEDICAL_LICENSE]."
        )

        test_cases.append((original_text, expected_output))
    
    return test_cases

# Function to evaluate anonymization accuracy
def evaluate_anonymizer(test_cases):
    y_true, y_pred = [], []

    for original, expected in test_cases:
        anonymized = anonymize_text(original)

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

# GUI for user interaction
def run_gui():
    def anonymize_input():
        input_text = input_box.get("1.0", tk.END).strip()
        if not input_text:
            result_box.delete("1.0", tk.END)
            result_box.insert(tk.END, "Please enter text to anonymize.")
            return

        anonymized_text = anonymize_text(input_text)
        result_box.delete("1.0", tk.END)
        result_box.insert(tk.END, anonymized_text)

    def test_anonymizer():
        test_cases = generate_test_data(5)
        metrics = evaluate_anonymizer(test_cases)
        result_box.delete("1.0", tk.END)
        result_box.insert(tk.END, f"Precision: {metrics['Precision']:.2f}\n")
        result_box.insert(tk.END, f"Recall: {metrics['Recall']:.2f}\n")
        result_box.insert(tk.END, f"F1-score: {metrics['F1-score']:.2f}\n")

    # Create GUI window
    root = tk.Tk()
    root.title("Chat Anonymizer")

    # Input box
    tk.Label(root, text="Enter chat text:").pack()
    input_box = scrolledtext.ScrolledText(root, height=5, width=50)
    input_box.pack()

    # Buttons
    tk.Button(root, text="Anonymize", command=anonymize_input).pack()
    tk.Button(root, text="Run Test Cases", command=test_anonymizer).pack()

    # Output box
    tk.Label(root, text="Anonymized Output / Evaluation:").pack()
    result_box = scrolledtext.ScrolledText(root, height=5, width=50)
    result_box.pack()

    # Start GUI loop
    root.mainloop()

# Run the GUI
run_gui()

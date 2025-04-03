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
    "SSN": r"\b\d{3}-\d{2}-\d{4}\b"
}

# Function to anonymize text
def anonymize_text(text):
    original_text = text
    
    # Step 1: Anonymize structured PII
    for label, pattern in patterns.items():
        text = re.sub(pattern, f"[{label}]", text)

    # Step 2: Use NLP model for entity anonymization
    doc = nlp(text)
    for ent in doc.ents:
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

        original_text = f"Hello, I'm {name}. Contact me at {email} or call {phone}. My server IP is {ip}. My credit card is {credit_card}."
        expected_output = f"Hello, I'm [PERSON]. Contact me at [EMAIL] or call [PHONE]. My server IP is [IP]. My credit card is [CREDIT_CARD]."

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

    precision = precision_score(y_true, y_pred)
    recall = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)

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

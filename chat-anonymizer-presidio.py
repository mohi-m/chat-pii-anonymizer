import re
import tkinter as tk
from tkinter import scrolledtext
from faker import Faker
from sklearn.metrics import precision_score, recall_score, f1_score

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

# Initialize Presidio components
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

def presidio_anonymize(text):
    """
    Uses Presidio's AnalyzerEngine and AnonymizerEngine to detect and anonymize PII.
    Uses the default anonymization configuration.
    """
    results = analyzer.analyze(text=text, language="en")
    anonymized_result = anonymizer.anonymize(text=text, analyzer_results=results)
    return anonymized_result.text

def evaluate_anonymization(raw_text, labeled_text):
    """
    Anonymizes the raw text using Presidio and compares the output with the expected labeled text.
    Extracts tokens enclosed in square brackets and computes precision, recall, and F1-score.
    """
    anonymized = presidio_anonymize(raw_text)
    
    # Extract tokens enclosed in square brackets from expected and anonymized outputs.
    # (If the default anonymizer does not output tokens in square brackets,
    #  adjust these extraction patterns accordingly.)
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
    recall    = recall_score(y_true, y_pred, zero_division=0)
    f1        = f1_score(y_true, y_pred, zero_division=0)
    
    return {"Precision": precision, "Recall": recall, "F1-score": f1, "anonymized": anonymized}

def generate_test_data(num_samples=5):
    """
    Generate synthetic test cases containing PII using Faker.
    The expected labeled text uses tokens in square brackets.
    Note: The default Presidio anonymizer may not output tokens with square brackets.
    Adjust the expected labels if needed.
    """
    fake = Faker()
    test_cases = []
    for _ in range(num_samples):
        name         = fake.name()
        email        = fake.email()
        phone        = fake.phone_number()
        ip           = fake.ipv4()
        ssn          = fake.ssn()
        credit_card  = fake.credit_card_number()
        
        raw_text = (
            f"Hello, I'm {name}. Contact me at {email} or call {phone}. "
            f"My IP is {ip}, my SSN is {ssn}, and my credit card is {credit_card}."
        )
        expected_labeled = (
            f"Hello, I'm <PERSON>. Contact me at <EMAIL_ADDRESS> or call <PHONE_NUMBER>. "
            f"My IP is <IP_ADDRESS>, my SSN is <US_SOCIAL_SECURITY_NUMBER>, and my credit card is <CREDIT_CARD>."
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

def run_gui():
    root = tk.Tk()
    root.title("Chat PII Anonymizer & Evaluator (Presidio)")

    # --- Anonymize Text Section ---
    frame_anonymize = tk.LabelFrame(root, text="Anonymize Text", padx=10, pady=10)
    frame_anonymize.pack(padx=10, pady=5, fill="both", expand=True)
    tk.Label(frame_anonymize, text="Enter chat text:").pack(anchor="w")
    input_box = scrolledtext.ScrolledText(frame_anonymize, height=5, width=160)
    input_box.pack(padx=5, pady=5)
    result_box_anonymize = scrolledtext.ScrolledText(frame_anonymize, height=5, width=160)
    result_box_anonymize.pack(padx=5, pady=5)

    def anonymize_input():
        text = input_box.get("1.0", tk.END).strip()
        if not text:
            result_box_anonymize.delete("1.0", tk.END)
            result_box_anonymize.insert(tk.END, "Please enter text to anonymize.")
            return
        anonymized = presidio_anonymize(text)
        result_box_anonymize.delete("1.0", tk.END)
        result_box_anonymize.insert(tk.END, anonymized)
    
    tk.Button(frame_anonymize, text="Anonymize", command=anonymize_input).pack(pady=5)

    # --- Custom Evaluation Section ---
    frame_evaluation = tk.LabelFrame(root, text="Evaluate Anonymization (Custom Input)", padx=10, pady=10)
    frame_evaluation.pack(padx=10, pady=5, fill="both", expand=True)
    tk.Label(frame_evaluation, text="Raw text:").pack(anchor="w")
    raw_text_box = scrolledtext.ScrolledText(frame_evaluation, height=5, width=160)
    raw_text_box.pack(padx=5, pady=5)
    tk.Label(frame_evaluation, text="Labeled text (with expected [LABEL] tokens):").pack(anchor="w")
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

    # --- Synthetic Test Cases Section ---
    frame_test_data = tk.LabelFrame(root, text="Synthetic Test Cases Evaluation", padx=10, pady=10)
    frame_test_data.pack(padx=10, pady=5, fill="both", expand=True)
    result_box_test = scrolledtext.ScrolledText(frame_test_data, height=5, width=160)
    result_box_test.pack(padx=5, pady=5)

    def run_test_cases():
        test_cases = generate_test_data(5)
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

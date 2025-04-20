import re
import tkinter as tk
from tkinter import scrolledtext, messagebox
from tkinter import ttk
from faker import Faker
from sklearn.metrics import precision_score, recall_score, f1_score

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_anonymizer import AnonymizerEngine

# --- Custom Recognizers for Additional PII Types ---


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


# --- Initialize Presidio Analyzer and Anonymizer ---

analyzer = AnalyzerEngine()
# Add our custom recognizers to the analyzer registry
analyzer.registry.add_recognizer(USBankNumberRecognizer())
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
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    return {
        "Precision": precision,
        "Recall": recall,
        "F1-score": f1,
        "anonymized": anonymized,
    }


def generate_test_data(num_samples=5):
    """
    Generates synthetic test cases containing all the specified PII types using Faker.
    The expected labeled text uses angle-bracket tokens.
    """
    fake = Faker()
    test_cases = []
    for _ in range(num_samples):
        name = fake.name()
        email = fake.email()
        phone = fake.phone_number()
        location = fake.city()
        ip = fake.ipv4()
        credit_card = fake.credit_card_number()
        us_bank = (
            fake.random_int(min=10000000, max=99999999)
            if fake.random_int(0, 1) == 0
            else fake.random_int(min=1000000000, max=99999999999999999)
        )
        us_driver_license = (
            f"{fake.random_uppercase_letter()}{fake.random_int(1000000, 9999999)}"
        )
        us_passport = fake.random_int(min=100000000, max=999999999)
        medical_license = (
            f"{fake.random_uppercase_letter()}{fake.random_int(10000, 999999)}"
        )
        ssn = fake.ssn()

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
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    return {"Precision": precision, "Recall": recall, "F1-score": f1}


def create_custom_style():
    """Create custom styles for the GUI elements"""
    style = ttk.Style()

    # Configure main theme
    style.configure(".", font=("Segoe UI", 10))

    # Custom button style
    style.configure(
        "Custom.TButton",
        padding=10,
        font=("Segoe UI", 10, "bold"),
        background="#2196F3",
        foreground="black",
    )


def create_scrolled_text(parent, height=5):
    """Create a custom styled ScrolledText widget"""
    text_widget = scrolledtext.ScrolledText(
        parent,
        height=height,
        width=80,
        font=("Consolas", 10),
        wrap=tk.WORD,
        borderwidth=2,
        relief="solid",
        background="#ffffff",
        foreground="#333333",
    )
    return text_widget


def run_gui():
    root = tk.Tk()
    root.title("Chat PII Anonymizer & Evaluator (Presidio with Custom Recognizers)")
    root.configure(background="#f0f0f0")

    # Set window size and position
    window_width = 1000
    window_height = 800
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # Create and apply custom styles
    create_custom_style()

    # Create main container
    main_container = ttk.Frame(root, padding="10")
    main_container.pack(fill="both", expand=True)

    # Create notebook for tabbed interface
    notebook = ttk.Notebook(main_container)
    notebook.pack(fill="both", expand=True, padx=5, pady=5)

    # Tab 1: Anonymize Text
    anonymize_tab = ttk.Frame(notebook)
    notebook.add(anonymize_tab, text="Anonymize Text")

    ttk.Label(
        anonymize_tab, text="Enter chat text to anonymize:", style="Custom.TLabel"
    ).pack(anchor="w", pady=(10, 5))

    input_box = create_scrolled_text(anonymize_tab)
    input_box.pack(fill="both", expand=True, padx=5, pady=5)

    result_box_anonymize = create_scrolled_text(anonymize_tab)
    result_box_anonymize.pack(fill="both", expand=True, padx=5, pady=5)

    def anonymize_with_loading():
        text = input_box.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "Please enter text to anonymize.")
            return

        # Show loading state
        anonymize_btn.configure(state="disabled")
        root.config(cursor="wait")
        root.update()

        try:
            anonymized = presidio_anonymize(text)
            result_box_anonymize.delete("1.0", tk.END)
            result_box_anonymize.insert(tk.END, anonymized)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            # Reset loading state
            anonymize_btn.configure(state="normal")
            root.config(cursor="")

    anonymize_btn = ttk.Button(
        anonymize_tab,
        text="Anonymize Text",
        command=anonymize_with_loading,
        style="Custom.TButton",
    )
    anonymize_btn.pack(pady=10)

    # Tab 2: Evaluation
    eval_tab = ttk.Frame(notebook)
    notebook.add(eval_tab, text="Evaluation")

    ttk.Label(eval_tab, text="Raw text:", style="Custom.TLabel").pack(
        anchor="w", pady=(10, 5)
    )

    raw_text_box = create_scrolled_text(eval_tab)
    raw_text_box.pack(fill="both", expand=True, padx=5, pady=5)

    ttk.Label(
        eval_tab,
        text="Labeled text (with expected <LABEL> tokens):",
        style="Custom.TLabel",
    ).pack(anchor="w", pady=(10, 5))

    labeled_text_box = create_scrolled_text(eval_tab)
    labeled_text_box.pack(fill="both", expand=True, padx=5, pady=5)

    result_box_eval = create_scrolled_text(eval_tab)
    result_box_eval.pack(fill="both", expand=True, padx=5, pady=5)

    def evaluate_with_loading():
        raw = raw_text_box.get("1.0", tk.END).strip()
        labeled = labeled_text_box.get("1.0", tk.END).strip()
        if not raw or not labeled:
            messagebox.showwarning("Warning", "Please enter both raw and labeled text.")
            return

        # Show loading state
        eval_btn.configure(state="disabled")
        root.config(cursor="wait")
        root.update()

        try:
            metrics = evaluate_anonymization(raw, labeled)
            result_box_eval.delete("1.0", tk.END)
            result_box_eval.insert(
                tk.END, f"Anonymized Text:\n{metrics['anonymized']}\n\n"
            )
            result_box_eval.insert(tk.END, "Metrics:\n")
            result_box_eval.insert(
                tk.END, f"📊 Precision: {metrics['Precision']:.2f}\n"
            )
            result_box_eval.insert(tk.END, f"📊 Recall: {metrics['Recall']:.2f}\n")
            result_box_eval.insert(tk.END, f"📊 F1-score: {metrics['F1-score']:.2f}\n")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            # Reset loading state
            eval_btn.configure(state="normal")
            root.config(cursor="")

    eval_btn = ttk.Button(
        eval_tab,
        text="Calculate Accuracy",
        command=evaluate_with_loading,
        style="Custom.TButton",
    )
    eval_btn.pack(pady=10)

    # Tab 3: Test Cases
    test_tab = ttk.Frame(notebook)
    notebook.add(test_tab, text="Test Cases")

    result_box_test = create_scrolled_text(test_tab, height=20)
    result_box_test.pack(fill="both", expand=True, padx=5, pady=5)

    def run_test_cases_with_loading():
        # Show loading state
        test_btn.configure(state="disabled")
        root.config(cursor="wait")
        root.update()

        try:
            test_cases = generate_test_data(5)
            metrics = evaluate_test_cases(test_cases)

            result_box_test.delete("1.0", tk.END)
            result_box_test.insert(tk.END, "🔍 Synthetic Test Cases Evaluation:\n")

            for i, (raw, expected) in enumerate(test_cases, start=1):
                anonymized = presidio_anonymize(raw)
                result_box_test.insert(tk.END, f"\n📝 Test Case {i}:\n")
                result_box_test.insert(tk.END, f"Raw: {raw}\n")
                result_box_test.insert(tk.END, f"Expected: {expected}\n")
                result_box_test.insert(tk.END, f"Anonymized: {anonymized}\n")

            result_box_test.insert(tk.END, f"\n📊 Overall Metrics:\n")
            result_box_test.insert(tk.END, f"Precision: {metrics['Precision']:.2f}\n")
            result_box_test.insert(tk.END, f"Recall: {metrics['Recall']:.2f}\n")
            result_box_test.insert(tk.END, f"F1-score: {metrics['F1-score']:.2f}\n")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            # Reset loading state
            test_btn.configure(state="normal")
            root.config(cursor="")

    test_btn = ttk.Button(
        test_tab,
        text="Run Test Cases",
        command=run_test_cases_with_loading,
        style="Custom.TButton",
    )
    test_btn.pack(pady=10)

    # Menu bar
    menubar = tk.Menu(root)
    root.config(menu=menubar)

    # File menu
    file_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Exit", command=root.quit)

    # Help menu
    help_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Help", menu=help_menu)
    help_menu.add_command(
        label="About",
        command=lambda: messagebox.showinfo(
            "About",
            "Chat PII Anonymizer v1.0 (Presidio)\n\nA tool for detecting and anonymizing personally identifiable information (PII) in chat data.",
        ),
    )

    # Add status bar
    status_bar = ttk.Label(
        root, text="Ready", relief=tk.SUNKEN, anchor=tk.W, padding=(5, 2)
    )
    status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    root.mainloop()


if __name__ == "__main__":
    run_gui()

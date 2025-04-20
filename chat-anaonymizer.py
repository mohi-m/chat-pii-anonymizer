import re
import spacy
import logging
import tkinter as tk
from faker import Faker
from tkinter import scrolledtext, ttk, messagebox
from sklearn.metrics import precision_score, recall_score, f1_score
from tkinter.font import Font

# Set up logging
logging.basicConfig(
    filename="anonymizer.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Load NLP model and Faker
nlp = spacy.load("en_core_web_lg")
faker = Faker()

# Precompile regex patterns for structured PII
regex_patterns = {
    "EMAIL": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "PHONE": re.compile(
        r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}(?:x\d+)?\b"
    ),
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
    re.compile(r"\b[A-Z]{1}\d{7}\b"),  # e.g., NY, NJ
    re.compile(r"\b\d{7,9}\b"),  # e.g., CA, TX
    re.compile(r"\b[A-Z]{2}\d{6,8}\b"),  # e.g., FL, IL
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
            matches.append({"start": match.start(), "end": match.end(), "label": label})

    # Collect US driver licenses
    for pattern in us_driver_license_patterns:
        for match in pattern.finditer(text):
            matches.append(
                {
                    "start": match.start(),
                    "end": match.end(),
                    "label": "US_DRIVER_LICENSE",
                }
            )

    # Step 2: Use NLP for entity recognition (PERSON, GPE, LOC)
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "GPE", "LOC"]:
            matches.append(
                {"start": ent.start_char, "end": ent.end_char, "label": ent.label_}
            )

    # Step 3: Sort matches by starting index; if same start, use longer match first.
    matches.sort(key=lambda m: (m["start"], -m["end"]))

    # Step 4: Filter out overlapping spans (greedy approach)
    filtered = []
    current_end = 0
    for m in matches:
        if m["start"] >= current_end:
            filtered.append(m)
            current_end = m["end"]

    # Step 5: Reconstruct the anonymized text in one pass.
    anonymized_text = ""
    last_index = 0
    for m in filtered:
        anonymized_text += text[last_index : m["start"]]
        anonymized_text += f"[{m['label']}]"
        last_index = m["end"]
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
    return {
        "Precision": precision,
        "Recall": recall,
        "F1-score": f1,
        "anonymized": anonymized,
    }


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
        clean_phone = phone.split(" x")[0]  # Removes anything after ' x'
        ip = faker.ipv4()
        credit_card = faker.credit_card_number()
        ssn = faker.ssn()
        bank_number = faker.random_int(min=10000000, max=99999999999999999)
        passport = faker.random_int(min=100000000, max=999999999)
        latitude, longitude = faker.latitude(), faker.longitude()
        medical_license = (
            f"{faker.random_uppercase_letter()}{faker.random_int(10000, 999999)}"
        )

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
        foreground="black",  # Changed from "white" to "black"
    )

    # Custom frame style
    style.configure("Custom.TLabelframe", background="#f5f5f5", padding=10)

    # Custom label style
    style.configure("Custom.TLabel", font=("Segoe UI", 10), padding=5)

    return style


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
    root.title("Chat PII Anonymizer & Evaluator")
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
    style = create_custom_style()

    # Create main container
    main_container = ttk.Frame(root, padding="10")
    main_container.pack(fill="both", expand=True)

    # Create notebook for tabbed interface
    notebook = ttk.Notebook(main_container)
    notebook.pack(fill="both", expand=True, padx=5, pady=5)

    # Tab 1: Anonymize Text
    anonymize_tab = ttk.Frame(notebook, style="Custom.TLabelframe")
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
            anonymized = anonymize_text(text)
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
    eval_tab = ttk.Frame(notebook, style="Custom.TLabelframe")
    notebook.add(eval_tab, text="Evaluation")

    ttk.Label(eval_tab, text="Raw text:", style="Custom.TLabel").pack(
        anchor="w", pady=(10, 5)
    )

    raw_text_box = create_scrolled_text(eval_tab)
    raw_text_box.pack(fill="both", expand=True, padx=5, pady=5)

    ttk.Label(
        eval_tab,
        text="Labeled text (with expected [LABEL] tokens):",
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
    test_tab = ttk.Frame(notebook, style="Custom.TLabelframe")
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
                anonymized = anonymize_text(raw)
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
            "Chat PII Anonymizer v1.0\n\nA tool for detecting and anonymizing personally identifiable information (PII) in chat data.",
        ),
    )

    # Add status bar
    status_bar = ttk.Label(
        root, text="Ready", relief=tk.SUNKEN, anchor=tk.W, padding=(5, 2)
    )
    status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    root.mainloop()


# Run the GUI
if __name__ == "__main__":
    run_gui()

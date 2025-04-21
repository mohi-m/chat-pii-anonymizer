import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import logging
from typing import Dict, Any

from ..regex import RegexAnonymizer
from ..presidio import PresidioAnonymizer
from ..base import BaseAnonymizer

# Set up logging
logging.basicConfig(
    filename="anonymizer.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class AnonymizerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PII Anonymizer")
        self.root.configure(background="#f0f0f0")

        # Initialize anonymizers
        self.anonymizers = {
            "Regex + NLP": RegexAnonymizer(),
            "Presidio": PresidioAnonymizer(),
        }
        self.current_anonymizer = None

        # Set window size and position
        window_width = 1000
        window_height = 800
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        self._create_styles()
        self._create_widgets()

    def _create_styles(self):
        """Create custom styles for GUI elements"""
        style = ttk.Style()
        style.configure(".", font=("Segoe UI", 10))
        style.configure(
            "Custom.TButton",
            padding=10,
            font=("Segoe UI", 10, "bold"),
            background="#2196F3",
            foreground="black",
        )
        style.configure("Custom.TLabelframe", background="#f5f5f5", padding=10)
        style.configure("Custom.TLabel", font=("Segoe UI", 10), padding=5)

    def _create_widgets(self):
        """Create and arrange all GUI widgets"""
        # Create main container
        main_container = ttk.Frame(self.root, padding="10")
        main_container.pack(fill="both", expand=True)

        # Create anonymizer selection
        selection_frame = ttk.LabelFrame(
            main_container, text="Anonymizer Selection", padding=5
        )
        selection_frame.pack(fill="x", padx=5, pady=5)

        self.anonymizer_var = tk.StringVar(value=list(self.anonymizers.keys())[0])
        for name in self.anonymizers.keys():
            ttk.Radiobutton(
                selection_frame,
                text=name,
                variable=self.anonymizer_var,
                value=name,
                command=self._on_anonymizer_change,
            ).pack(side="left", padx=10)

        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Tab 1: Anonymize Text
        self._create_anonymize_tab()

        # Tab 2: Evaluation
        self._create_evaluation_tab()

        # Tab 3: Test Cases
        self._create_test_cases_tab()

        # Create menu bar
        self._create_menu()

        # Add status bar
        self.status_bar = ttk.Label(
            self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W, padding=(5, 2)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Initialize with default anonymizer
        self._on_anonymizer_change()

    def _create_anonymize_tab(self):
        """Create the Anonymize Text tab"""
        anonymize_tab = ttk.Frame(self.notebook)
        self.notebook.add(anonymize_tab, text="Anonymize Text")

        ttk.Label(
            anonymize_tab, text="Enter text to anonymize:", style="Custom.TLabel"
        ).pack(anchor="w", pady=(10, 5))

        self.input_box = self._create_scrolled_text(anonymize_tab)
        self.input_box.pack(fill="both", expand=True, padx=5, pady=5)

        self.result_box_anonymize = self._create_scrolled_text(anonymize_tab)
        self.result_box_anonymize.pack(fill="both", expand=True, padx=5, pady=5)

        self.anonymize_btn = ttk.Button(
            anonymize_tab,
            text="Anonymize Text",
            command=self._anonymize_with_loading,
            style="Custom.TButton",
        )
        self.anonymize_btn.pack(pady=10)

    def _create_evaluation_tab(self):
        """Create the Evaluation tab"""
        eval_tab = ttk.Frame(self.notebook)
        self.notebook.add(eval_tab, text="Evaluation")

        ttk.Label(eval_tab, text="Raw text:", style="Custom.TLabel").pack(
            anchor="w", pady=(10, 5)
        )

        self.raw_text_box = self._create_scrolled_text(eval_tab)
        self.raw_text_box.pack(fill="both", expand=True, padx=5, pady=5)

        label_text = (
            "labeled text (with <LABEL> tokens for Presidio, [LABEL] for Regex):"
        )
        ttk.Label(eval_tab, text=label_text, style="Custom.TLabel").pack(
            anchor="w", pady=(10, 5)
        )

        self.labeled_text_box = self._create_scrolled_text(eval_tab)
        self.labeled_text_box.pack(fill="both", expand=True, padx=5, pady=5)

        self.result_box_eval = self._create_scrolled_text(eval_tab)
        self.result_box_eval.pack(fill="both", expand=True, padx=5, pady=5)

        self.eval_btn = ttk.Button(
            eval_tab,
            text="Calculate Accuracy",
            command=self._evaluate_with_loading,
            style="Custom.TButton",
        )
        self.eval_btn.pack(pady=10)

    def _create_test_cases_tab(self):
        """Create the Test Cases tab"""
        test_tab = ttk.Frame(self.notebook)
        self.notebook.add(test_tab, text="Test Cases")

        self.result_box_test = self._create_scrolled_text(test_tab, height=20)
        self.result_box_test.pack(fill="both", expand=True, padx=5, pady=5)

        self.test_btn = ttk.Button(
            test_tab,
            text="Run Test Cases",
            command=self._run_test_cases_with_loading,
            style="Custom.TButton",
        )
        self.test_btn.pack(pady=10)

    def _create_menu(self):
        """Create the menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.root.quit)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(
            label="About",
            command=lambda: messagebox.showinfo(
                "About",
                "PII Anonymizer v1.0\n\nA tool for detecting and anonymizing personally identifiable information (PII) in text data.",
            ),
        )

    def _create_scrolled_text(self, parent, height=5):
        """Create a custom styled ScrolledText widget"""
        return scrolledtext.ScrolledText(
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

    def _on_anonymizer_change(self):
        """Handle anonymizer selection change"""
        selection = self.anonymizer_var.get()
        self.current_anonymizer = self.anonymizers[selection]
        logging.info(f"Switched to {selection} anonymizer")

    def _anonymize_with_loading(self):
        """Anonymize text with loading state"""
        text = self.input_box.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "Please enter text to anonymize.")
            return

        self._set_loading_state(True)
        try:
            result = self.current_anonymizer.anonymize_text(text)
            self.result_box_anonymize.delete("1.0", tk.END)
            self.result_box_anonymize.insert(tk.END, result.text)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            self._set_loading_state(False)

    def _evaluate_with_loading(self):
        """Evaluate anonymization with loading state"""
        raw = self.raw_text_box.get("1.0", tk.END).strip()
        labeled = self.labeled_text_box.get("1.0", tk.END).strip()
        if not raw or not labeled:
            messagebox.showwarning("Warning", "Please enter both raw and labeled text.")
            return

        self._set_loading_state(True)
        try:
            metrics = self.current_anonymizer.evaluate_anonymization(raw, labeled)
            self._display_evaluation_results(metrics)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            self._set_loading_state(False)

    def _run_test_cases_with_loading(self):
        """Run test cases with loading state"""
        self._set_loading_state(True)
        try:
            test_cases = self.current_anonymizer.generate_test_data(5)
            metrics = self.current_anonymizer.evaluate_test_cases(test_cases)
            self._display_test_results(test_cases, metrics)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            self._set_loading_state(False)

    def _set_loading_state(self, is_loading: bool):
        """Set loading state for buttons and cursor"""
        state = "disabled" if is_loading else "normal"
        cursor = "wait" if is_loading else ""

        self.anonymize_btn.configure(state=state)
        self.eval_btn.configure(state=state)
        self.test_btn.configure(state=state)
        self.root.config(cursor=cursor)
        self.root.update()

    def _display_evaluation_results(self, metrics: Dict[str, Any]):
        """Display evaluation results in the evaluation tab"""
        self.result_box_eval.delete("1.0", tk.END)
        self.result_box_eval.insert(
            tk.END, f"Anonymized Text:\n{metrics['anonymized']}\n\n"
        )
        self.result_box_eval.insert(tk.END, "Metrics:\n")
        self.result_box_eval.insert(
            tk.END, f"📊 Precision: {metrics['Precision']:.2f}\n"
        )
        self.result_box_eval.insert(tk.END, f"📊 Recall: {metrics['Recall']:.2f}\n")
        self.result_box_eval.insert(tk.END, f"📊 F1-score: {metrics['F1-score']:.2f}\n")

    def _display_test_results(self, test_cases: list, metrics: Dict[str, float]):
        """Display test results in the test cases tab"""
        self.result_box_test.delete("1.0", tk.END)
        self.result_box_test.insert(tk.END, "🔍 Synthetic Test Cases Evaluation:\n")

        for i, (raw, expected) in enumerate(test_cases, start=1):
            result = self.current_anonymizer.anonymize_text(raw)
            self.result_box_test.insert(tk.END, f"\n📝 Test Case {i}:\n")
            self.result_box_test.insert(tk.END, f"Raw: {raw}\n")
            self.result_box_test.insert(tk.END, f"Expected: {expected}\n")
            self.result_box_test.insert(tk.END, f"Anonymized: {result.text}\n")

        self.result_box_test.insert(tk.END, f"\n📊 Overall Metrics:\n")
        self.result_box_test.insert(tk.END, f"Precision: {metrics['Precision']:.2f}\n")
        self.result_box_test.insert(tk.END, f"Recall: {metrics['Recall']:.2f}\n")
        self.result_box_test.insert(tk.END, f"F1-score: {metrics['F1-score']:.2f}\n")

    def run(self):
        """Start the GUI application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = AnonymizerGUI()
    app.run()

# Chat PII Anonymizer

The **Chat PII Anonymizer** is a Python-based tool designed to detect and anonymize Personally Identifiable Information (PII) from chat data. It leverages advanced libraries like **Presidio**, **spaCy**, and **Faker** to identify and mask sensitive information such as names, emails, phone numbers, IP addresses, and more.

## Features

- **Multiple Anonymization Methods**: Choose between Regex+NLP or Presidio-based anonymization
- **Custom Recognizers**: Extend Presidio's capabilities with custom recognizers for PII types like US bank numbers, medical licenses, and passports
- **Regex-Based Detection**: Identify structured PII (e.g., emails, phone numbers, IPs) using precompiled regex patterns
- **NLP-Based Detection**: Use spaCy's Named Entity Recognition (NER) to detect entities like PERSON, GPE (geopolitical entities), and LOC (locations)
- **Evaluation Metrics**: Evaluate anonymization accuracy with precision, recall, and F1-score
- **Synthetic Test Data**: Generate synthetic test cases with Faker for testing and evaluation
- **Modern GUI Interface**: A user-friendly GUI with tabbed interface for anonymization, evaluation, and testing

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/mohi-m/chat-pii-anonymizer.git
   cd chat-pii-anonymizer
   ```

2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Download the spaCy language model:
   ```bash
   python -m spacy download en_core_web_lg
   ```

## Usage

### Running the GUI

To launch the GUI:

```bash
python main.py
```

The GUI provides three main tabs:

1. **Anonymize Text**

   - Enter raw text and choose anonymization method (Regex+NLP or Presidio)
   - Click "Anonymize Text" to mask PII
   - View results in real-time

2. **Evaluation**

   - Input raw text and labeled text (using <LABEL> or [LABEL] format)
   - Calculate accuracy metrics
   - View detailed results including anonymized output

3. **Test Cases**
   - Generate and run synthetic test cases
   - View comprehensive test results with metrics
   - Analyze performance across different PII types

## Supported PII Types

| PII Type           | Detection Method | Example             |
| ------------------ | ---------------- | ------------------- |
| Email              | Regex            | example@mail.com    |
| Phone Number       | Regex            | +1-123-456-7890     |
| IP Address         | Regex            | 192.168.1.1         |
| Credit Card Number | Regex            | 4111 1111 1111 1111 |
| SSN                | Regex            | 123-45-6789         |
| US Passport        | Regex            | 123456789           |
| Medical License    | Regex            | A123456             |
| US Bank Number     | Regex            | 12345678901234567   |
| Person Name        | NLP (spaCy)      | John Doe            |
| Location (GPE/LOC) | NLP (spaCy)      | New York            |

## Project Structure

```
chat-pii-anonymizer/
├── main.py                 # Entry point
├── requirements.txt        # Python dependencies
├── src/
│   └── anonymizer/
│       ├── __init__.py
│       ├── base.py        # Abstract base class
│       ├── presidio.py    # Presidio implementation
│       ├── regex.py       # Regex+NLP implementation
│       ├── gui/
│       │   ├── __init__.py
│       │   └── app.py     # GUI implementation
│       └── utils/
│           └── __init__.py
├── test-data/             # Test datasets
└── tests/                 # Test cases
```

## Evaluation

The tool provides comprehensive evaluation metrics:

- **Precision**: Proportion of correctly identified PII among all detected PII
- **Recall**: Proportion of correctly identified PII among all actual PII
- **F1-Score**: Harmonic mean of precision and recall

Results are displayed with clear formatting and emoji indicators for better readability.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests to improve the project.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

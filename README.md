# Chat PII Anonymizer

The **Chat PII Anonymizer** is a Python-based tool designed to detect and anonymize Personally Identifiable Information (PII) from chat data. It leverages advanced libraries like **Presidio**, **spaCy**, and **Faker** to identify and mask sensitive information such as names, emails, phone numbers, IP addresses, and more.

## Features

- **Multiple Anonymization Methods**: Choose between Regex+NLP or Presidio-based anonymization
- **Custom PII Recognizers**: Built-in recognizers for:
  - US Passport Numbers
  - US Bank Account Numbers
  - Medical License Numbers
  - US Driver License Numbers (multiple state formats)
- **Regex-Based Detection**: Identify structured PII using precompiled regex patterns
- **NLP-Based Detection**: Use spaCy's Named Entity Recognition (NER) for unstructured PII
- **Comprehensive Evaluation**: Built-in evaluation tools with precision, recall, and F1-score metrics
- **Modern GUI Interface**: User-friendly interface with:
  - Real-time anonymization
  - Accuracy evaluation
  - Synthetic test data generation
  - Clear results visualization with emoji indicators

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/mohi-m/chat-pii-anonymizer.git
   cd chat-pii-anonymizer
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Download the spaCy model:
   ```bash
   python -m spacy download en_core_web_lg
   ```

## Usage

Run the application:

```bash
python main.py
```

### GUI Features

The application provides three main tabs:

1. **Anonymize Text**

   - Select anonymization method (Regex+NLP or Presidio)
   - Enter text and get real-time anonymization
   - View masked output with PII labels

2. **Evaluation**

   - Input raw and labeled text
   - Support for both formats:
     - Presidio format: `<LABEL>`
     - Regex format: `[LABEL]`
   - View detailed accuracy metrics

3. **Test Cases**
   - Generate synthetic test data
   - Run automated evaluations
   - View comprehensive performance metrics

## Supported PII Types

| Category       | PII Type        | Detection Method | Example             |
| -------------- | --------------- | ---------------- | ------------------- |
| **Personal**   | Name            | NLP (spaCy)      | John Doe            |
|                | SSN             | Regex            | 123-45-6789         |
|                | US Passport     | Custom Regex     | 123456789           |
|                | Medical License | Custom Regex     | A123456             |
| **Financial**  | Credit Card     | Regex            | 4111 1111 1111 1111 |
|                | Bank Account    | Custom Regex     | 12345678901234567   |
| **Contact**    | Email           | Regex            | user@example.com    |
|                | Phone           | Regex            | +1-123-456-7890     |
| **Location**   | Address         | NLP (spaCy)      | 123 Main St         |
|                | GPS Coordinates | Regex            | 40.7128,-74.0060    |
|                | IP Address      | Regex            | 192.168.1.1         |
| **Government** | Driver License  | Custom Regex     | Multiple formats    |
|                | Location/GPE    | NLP (spaCy)      | New York            |

## Project Structure

```
chat-pii-anonymizer/
├── main.py                     # Application entry point
├── requirements.txt            # Project dependencies
├── src/
│   └── anonymizer/
│       ├── base.py            # Abstract base class
│       ├── presidio.py        # Presidio implementation
│       ├── regex.py           # Regex+NLP implementation
│       ├── recognizers/       # Custom PII recognizers
│       │   ├── medical_license.py
│       │   ├── us_bank_number.py
│       │   └── us_passport.py
│       ├── gui/              # GUI components
│       │   ├── __init__.py
│       │   └── app.py
│       └── utils/            # Utility functions
├── test-data/                # Test datasets
└── tests/                    # Test cases
```

## Evaluation Metrics

The tool provides detailed evaluation metrics:

- **Precision**: Accuracy of PII detection (true positives / all detections)
- **Recall**: Coverage of PII detection (true positives / all actual PII)
- **F1-Score**: Balanced measure of precision and recall

Results include:

- 📊 Detailed metrics per anonymization run
- 🔍 Synthetic test case results
- 📝 Side-by-side comparison of raw and anonymized text

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

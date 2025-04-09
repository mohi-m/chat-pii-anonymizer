# Chat PII Anonymizer

The **Chat PII Anonymizer** is a Python-based tool designed to detect and anonymize Personally Identifiable Information (PII) from chat data. It leverages advanced libraries like **Presidio**, **spaCy**, and **Faker** to identify and mask sensitive information such as names, emails, phone numbers, IP addresses, and more.

## Features

- **Custom Recognizers**: Extend Presidio's capabilities with custom recognizers for PII types like US bank numbers, medical licenses, and passports.
- **Regex-Based Detection**: Identify structured PII (e.g., emails, phone numbers, IPs) using precompiled regex patterns.
- **NLP-Based Detection**: Use spaCy's Named Entity Recognition (NER) to detect entities like PERSON, GPE (geopolitical entities), and LOC (locations).
- **Evaluation Metrics**: Evaluate anonymization accuracy with precision, recall, and F1-score.
- **Synthetic Test Data**: Generate synthetic test cases with Faker for testing and evaluation.
- **GUI Interface**: A user-friendly GUI built with Tkinter for anonymization and evaluation.

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
To launch the GUI for anonymization and evaluation:
```bash
python chat-anonymizer-presidio.py
```

### Anonymizing Text
1. Enter the raw chat text in the input box.
2. Click the **Anonymize** button to mask PII.
3. View the anonymized text in the output box.

### Evaluating Anonymization
1. Enter the raw text and labeled text (with expected PII labels) in the respective input boxes.
2. Click the **Calculate Accuracy** button to compute precision, recall, and F1-score.

### Running Synthetic Test Cases
1. Click the **Run Test Cases** button to evaluate the tool on synthetic test cases.
2. View the anonymized results and overall metrics in the output box.

## Supported PII Types

| PII Type           | Detection Method | Example              |
|---------------------|------------------|----------------------|
| Email              | Regex            | example@mail.com     |
| Phone Number       | Regex            | +1-123-456-7890      |
| IP Address         | Regex            | 192.168.1.1          |
| Credit Card Number | Regex            | 4111 1111 1111 1111  |
| SSN                | Regex            | 123-45-6789          |
| US Passport        | Regex            | 123456789            |
| Medical License    | Regex            | A123456              |
| US Bank Number     | Regex            | 12345678901234567    |
| Person Name        | NLP (spaCy)      | John Doe             |
| Location (GPE/LOC) | NLP (spaCy)      | New York             |

## File Structure

```
chat-pii-anonymizer/
├── chat-anonymizer-presidio.py   # Main script using Presidio
├── chat-anonymizer.py            # Alternative script using spaCy and regex
├── README.md
├── requirements.txt              # Python dependencies
```

## Evaluation

The tool provides evaluation metrics to measure anonymization accuracy:

- **Precision**: Proportion of correctly identified PII among all detected PII.
- **Recall**: Proportion of correctly identified PII among all actual PII.
- **F1-Score**: Harmonic mean of precision and recall.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests to improve the project.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
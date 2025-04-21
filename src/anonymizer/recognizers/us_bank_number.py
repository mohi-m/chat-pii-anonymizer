from presidio_analyzer import Pattern, PatternRecognizer


class USBankNumberRecognizer(PatternRecognizer):
    def __init__(self):
        patterns = [Pattern("US_BANK_NUMBER", r"\b(?:\d{8}|\d{10,17})\b", 0.5)]
        super().__init__(
            supported_entity="US_BANK_NUMBER",
            patterns=patterns,
            name="USBankNumberRecognizer",
        )

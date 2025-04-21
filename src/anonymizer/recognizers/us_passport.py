from presidio_analyzer import Pattern, PatternRecognizer


class USPassportRecognizer(PatternRecognizer):
    def __init__(self):
        patterns = [Pattern("US_PASSPORT", r"\b\d{9}\b", 0.5)]
        super().__init__(
            supported_entity="US_PASSPORT",
            patterns=patterns,
            name="USPassportRecognizer",
        )

from presidio_analyzer import Pattern, PatternRecognizer


class MedicalLicenseRecognizer(PatternRecognizer):
    def __init__(self):
        patterns = [Pattern("MEDICAL_LICENSE", r"\b[A-Z]{1,2}\d{5,10}\b", 0.5)]
        super().__init__(
            supported_entity="MEDICAL_LICENSE",
            patterns=patterns,
            name="MedicalLicenseRecognizer",
        )

"""
PII Anonymizer - Main Entry Point
"""

from src.anonymizer.gui.app import AnonymizerGUI


def main():
    app = AnonymizerGUI()
    app.run()


if __name__ == "__main__":
    main()

from abc import ABC, abstractmethod
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class AnonymizationResult:
    """Data class to hold anonymization results"""
    text: str
    entities: List[Dict[str, Any]]

class BaseAnonymizer(ABC):
    """Abstract base class for text anonymizers"""
    
    @abstractmethod
    def anonymize_text(self, text: str) -> AnonymizationResult:
        """Anonymize the given text and return the result"""
        pass
    
    @abstractmethod
    def evaluate_anonymization(self, raw_text: str, labeled_text: str) -> Dict[str, float]:
        """Evaluate anonymization against labeled text"""
        pass
    
    @abstractmethod
    def generate_test_data(self, num_samples: int = 5) -> List[tuple]:
        """Generate test data for evaluation"""
        pass
    
    @abstractmethod
    def evaluate_test_cases(self, test_cases: List[tuple]) -> Dict[str, float]:
        """Evaluate a set of test cases"""
        pass
    
    def get_name(self) -> str:
        """Get the name of the anonymizer implementation"""
        return self.__class__.__name__
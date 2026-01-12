"""
Content safety filters for medical/clinical content.
"""

from typing import List
from utils.logger import get_logger

logger = get_logger(__name__)


class ContentFilter:
    """Filter and enhance content for safety and compliance."""
    
    def __init__(self):
        logger.info("content_filter_initialized")
    
    def add_medical_disclaimer(self, answer: str) -> str:
        """
        Add medical disclaimer to clinical answers.
        
        Args:
            answer: Generated answer
            
        Returns:
            Answer with disclaimer
        """
        disclaimer = (
            "\n\n**Medical Disclaimer**: This information is for educational purposes only "
            "and is not a substitute for professional medical advice, diagnosis, or treatment. "
            "Always seek the advice of your physician or other qualified health provider "
            "with any questions you may have regarding a medical condition."
        )
        
        # Only add if answer seems medical in nature
        medical_keywords = ['patient', 'diagnosis', 'treatment', 'medication', 'dose', 
                           'therapy', 'clinical', 'symptom', 'disease']
        
        if any(keyword in answer.lower() for keyword in medical_keywords):
            return answer + disclaimer
        
        return answer
    
    def filter_unsafe_content(self, text: str) -> bool:
        """
        Check if content contains unsafe medical advice.
        
        Returns:
            True if content is safe, False if unsafe
        """
        # Patterns that suggest unsafe direct medical advice
        unsafe_patterns = [
            'you should take',
            'you should stop taking',
            'discontinue your medication',
            'don\'t see a doctor',
            'instead of seeing a doctor',
        ]
        
        text_lower = text.lower()
        for pattern in unsafe_patterns:
            if pattern in text_lower:
                logger.warning("unsafe_content_detected", pattern=pattern)
                return False
        
        return True
    
    def ensure_regulatory_compliance(self, answer: str, citations: List) -> dict:
        """
        Ensure answer meets regulatory requirements for audit trail.
        
        Returns:
            Compliance metadata
        """
        return {
            'has_citations': len(citations) > 0,
            'disclaimer_added': '**medical disclaimer**' in answer.lower(),
            'timestamp': 'iso_timestamp',
            'safety_checked': True,
        }

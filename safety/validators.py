"""
Safety validators for prompt injection, PHI masking, grounding checks, and confidence scoring.
"""

import re
from typing import List, Tuple
from models.schemas import Citation, SafetyValidation, SafetyDecision
from utils.logger import get_logger
from config import get_settings

logger = get_logger(__name__)


class SafetyValidator:
    """Comprehensive safety validation for clinical AI system."""
    
    def __init__(self):
        self.settings = get_settings()
        logger.info("safety_validator_initialized")
    
    def validate(
        self, 
        query: str, 
        answer: str, 
        citations: List[Citation]
    ) -> SafetyValidation:
        """
        Run comprehensive safety validation.
        
        Args:
            query: User question
            answer: Generated answer
            citations: Retrieved citations with scores
            
        Returns:
            Safety validation result with decision and flags
        """
        flags = []
        
        # Check for prompt injection in query
        injection_score = self.detect_prompt_injection(query)
        if injection_score > self.settings.max_prompt_injection_score:
            flags.append(f"prompt_injection_detected:{injection_score:.2f}")
            return SafetyValidation(
                decision=SafetyDecision.REJECTED,
                confidence_score=0.0,
                grounding_score=0.0,
                flags=flags,
                message="Query rejected due to potential prompt injection"
            )
        
        # Check grounding score
        grounding_score = self.check_grounding(citations)
        if grounding_score < self.settings.grounding_threshold:
            flags.append(f"low_grounding:{grounding_score:.2f}")
            return SafetyValidation(
                decision=SafetyDecision.REJECTED,
                confidence_score=0.0,
                grounding_score=grounding_score,
                flags=flags,
                message="Insufficient evidence to answer this question"
            )
        
        # Calculate confidence score
        confidence_score = self.assess_confidence(answer, citations)
        if confidence_score < self.settings.confidence_threshold:
            flags.append(f"low_confidence:{confidence_score:.2f}")
        
        # Check for PHI in answer
        if self.contains_phi(answer):
            flags.append("phi_detected")
        
        # Determine final decision
        if flags:
            decision = SafetyDecision.WARNING
        else:
            decision = SafetyDecision.APPROVED
        
        return SafetyValidation(
            decision=decision,
            confidence_score=confidence_score,
            grounding_score=grounding_score,
            flags=flags,
            message=None if decision == SafetyDecision.APPROVED else "Review safety flags"
        )
    
    def detect_prompt_injection(self, text: str) -> float:
        """
        Detect potential prompt injection attempts using heuristics.
        
        Returns:
            Injection score (0-1, higher = more suspicious)
        """
        score = 0.0
        text_lower = text.lower()
        
        # Suspicious patterns
        injection_patterns = [
            r"ignore\s+(previous|above|all)\s+instructions",
            r"disregard\s+(previous|above|all)",
            r"forget\s+(previous|above|all)",
            r"system\s*[:>]",
            r"<\|.*?\|>",  # Special tokens
            r"act\s+as\s+a\s+different",
            r"pretend\s+you\s+are",
            r"you\s+are\s+now",
            r"new\s+instructions",
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, text_lower):
                score += 0.3
        
        # Excessive special characters
        special_char_ratio = len(re.findall(r'[<>|{}[\]]', text)) / max(len(text), 1)
        score += min(special_char_ratio * 2, 0.3)
        
        # Multiple instruction keywords
        instruction_keywords = ['print', 'output', 'show', 'reveal', 'tell', 'execute', 'run']
        keyword_count = sum(1 for kw in instruction_keywords if kw in text_lower)
        if keyword_count >= 3:
            score += 0.2
        
        return min(score, 1.0)
    
    def mask_phi(self, text: str) -> Tuple[str, List[str]]:
        """
        Mask PHI/PII in text using regex patterns.
        
        Returns:
            Tuple of (masked_text, list of detected PHI types)
        """
        detected_phi = []
        masked = text
        
        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if re.search(email_pattern, masked):
            detected_phi.append("email")
            masked = re.sub(email_pattern, '[EMAIL_REDACTED]', masked)
        
        # Phone numbers (various formats)
        phone_patterns = [
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
            r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}',
        ]
        for pattern in phone_patterns:
            if re.search(pattern, masked):
                detected_phi.append("phone")
                masked = re.sub(pattern, '[PHONE_REDACTED]', masked)
        
        # SSN
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        if re.search(ssn_pattern, masked):
            detected_phi.append("ssn")
            masked = re.sub(ssn_pattern, '[SSN_REDACTED]', masked)
        
        # Medical Record Numbers (MRN) - common patterns
        mrn_pattern = r'\bMRN[:\s]*\d{6,10}\b'
        if re.search(mrn_pattern, masked, re.IGNORECASE):
            detected_phi.append("mrn")
            masked = re.sub(mrn_pattern, '[MRN_REDACTED]', masked, flags=re.IGNORECASE)
        
        # Dates of birth
        dob_pattern = r'\b(?:DOB|Date of Birth)[:\s]*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
        if re.search(dob_pattern, masked, re.IGNORECASE):
            detected_phi.append("dob")
            masked = re.sub(dob_pattern, '[DOB_REDACTED]', masked, flags=re.IGNORECASE)
        
        return masked, list(set(detected_phi))
    
    def contains_phi(self, text: str) -> bool:
        """Check if text contains PHI."""
        _, detected_phi = self.mask_phi(text)
        return len(detected_phi) > 0
    
    def check_grounding(self, citations: List[Citation]) -> float:
        """
        Calculate grounding score based on citation similarity.
        
        Returns:
            Grounding score (0-1)
        """
        if not citations:
            return 0.0
        
        # Use the maximum similarity score as grounding
        max_similarity = max(c.similarity_score for c in citations)
        return max_similarity
    
    def assess_confidence(self, answer: str, citations: List[Citation]) -> float:
        """
        Assess confidence in the answer.
        
        Returns:
            Confidence score (0-1)
        """
        # Simple heuristic: combine grounding score with answer characteristics
        grounding = self.check_grounding(citations)
        
        # Penalize very short answers
        length_factor = min(len(answer) / 50, 1.0)
        
        # Penalize uncertain language
        uncertainty_terms = ['maybe', 'perhaps', 'might', 'possibly', 'unclear', 'unsure']
        uncertainty_count = sum(1 for term in uncertainty_terms if term in answer.lower())
        uncertainty_penalty = min(uncertainty_count * 0.1, 0.3)
        
        confidence = grounding * length_factor * (1 - uncertainty_penalty)
        return min(max(confidence, 0.0), 1.0)
    
    def apply_refusal_policy(self, validation: SafetyValidation) -> Tuple[bool, str]:
        """
        Apply refusal policy based on validation result.
        
        Returns:
            Tuple of (should_refuse, refusal_message)
        """
        if validation.decision == SafetyDecision.REJECTED:
            return True, validation.message or "Unable to provide a safe response"
        
        if validation.grounding_score < self.settings.grounding_threshold:
            return True, "I don't have sufficient information in the documents to answer this question accurately."
        
        if validation.confidence_score < self.settings.confidence_threshold:
            return True, "I'm not confident enough in my answer to provide a response. Please rephrase your question or consult original documents."
        
        return False, ""

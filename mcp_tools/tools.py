"""
MCP tool implementations: calculator and PHI detector.
"""

import re
from typing import Dict, Any, List
from utils.logger import get_logger

logger = get_logger(__name__)


class CalculatorTool:
    """Simple calculator tool for basic arithmetic operations."""
    
    name = "calculator"
    description = "Perform basic arithmetic operations: add, subtract, multiply, divide"
    
    def execute(self, operation: str, a: float, b: float) -> Dict[str, Any]:
        """
        Execute calculator operation.
        
        Args:
            operation: One of 'add', 'subtract', 'multiply', 'divide'
            a: First operand
            b: Second operand
            
        Returns:
            Result dictionary
        """
        logger.info("calculator_tool_called", operation=operation, a=a, b=b)
        
        try:
            if operation == "add":
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                if b == 0:
                    return {"error": "Division by zero", "result": None}
                result = a / b
            else:
                return {"error": f"Unknown operation: {operation}", "result": None}
            
            return {"result": result, "error": None}
        
        except Exception as e:
            logger.error("calculator_error", error=str(e))
            return {"error": str(e), "result": None}


class PHIDetectorTool:
    """Detect PHI/PII in text using regex patterns."""
    
    name = "phi_detector"
    description = "Detect Protected Health Information (PHI) and Personally Identifiable Information (PII) in text"
    
    def execute(self, text: str) -> Dict[str, Any]:
        """
        Detect PHI in text.
        
        Args:
            text: Text to scan for PHI
            
        Returns:
            Detection results
        """
        logger.info("phi_detector_called", text_length=len(text))
        
        detected = []
        
        # Email
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text):
            detected.append({
                'type': 'email',
                'confidence': 0.95,
                'description': 'Email address detected'
            })
        
        # Phone number
        if re.search(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', text):
            detected.append({
                'type': 'phone',
                'confidence': 0.90,
                'description': 'Phone number detected'
            })
        
        # SSN
        if re.search(r'\b\d{3}-\d{2}-\d{4}\b', text):
            detected.append({
                'type': 'ssn',
                'confidence': 0.98,
                'description': 'Social Security Number detected'
            })
        
        # Medical Record Number
        if re.search(r'\bMRN[:\s]*\d{6,10}\b', text, re.IGNORECASE):
            detected.append({
                'type': 'mrn',
                'confidence': 0.92,
                'description': 'Medical Record Number detected'
            })
        
        # Date of Birth
        if re.search(r'\b(?:DOB|Date of Birth)[:\s]*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', text, re.IGNORECASE):
            detected.append({
                'type': 'dob',
                'confidence': 0.85,
                'description': 'Date of Birth detected'
            })
        
        return {
            'has_phi': len(detected) > 0,
            'detected_types': detected,
            'count': len(detected),
            'error': None
        }


# Registry of available tools
TOOLS = {
    "calculator": CalculatorTool(),
    "phi_detector": PHIDetectorTool(),
}

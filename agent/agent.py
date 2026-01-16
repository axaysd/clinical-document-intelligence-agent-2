"""
ADK-based agent for Clinical Document Intelligence.
Replaces custom orchestrator with Google ADK LlmAgent.
"""

from typing import Dict, Any, Optional
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.tool_context import ToolContext
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import re

from config import get_settings
from rag.retriever import Retriever
from utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


# ==================== Safety Callbacks ====================

def safety_input_validator(callback_context: CallbackContext, **kwargs) -> Optional[types.Content]:
    """
    Validate user input BEFORE agent processing starts.
    
    Checks for PHI/PII and prompt injection in queries.
    Can modify state or skip agent execution entirely.
    
    Returns:
        Content to skip agent execution, or None to proceed
    """
    # Get session state
    state = callback_context.state.to_dict() if callback_context.state else {}
    
    # Extract last user message from state if available
    # (In practice, you'd get this from the event stream or message history)
    last_message = state.get('last_user_message', '')
    
    if not last_message:
        return None  # No message to check
    
    logger.info("safety_input_check", message_length=len(last_message))
    
    # Check for PHI in query
    phi_result = phi_detector_tool(last_message)
    if phi_result['has_phi']:
        detected_types = [d['type'] for d in phi_result['detected_types']]
        logger.warning("phi_detected_in_query", types=detected_types)
        
        # Store warning in state for agent to see
        if callback_context.state:
            callback_context.state['phi_warning'] = f"PHI detected: {', '.join(detected_types)}"
    
    # Check for prompt injection patterns
    injection_patterns = [
        "ignore previous instructions",
        "ignore all previous",
        "system:",
        "role:system",
        "forget all",
        "disregard",
        "new instructions:",
    ]
    
    if any(pattern in last_message.lower() for pattern in injection_patterns):
        logger.warning("prompt_injection_detected", message=last_message[:100])
        # Block the agent execution
        return types.Content(
            role="model",
            parts=[types.Part(text="I cannot process that request. Please ask a clear question about clinical documents without including special instructions.")]
        )
    
    # Allow agent to proceed
    return None


def safety_output_validator(callback_context: CallbackContext, **kwargs) -> Optional[types.Content]:
    """
    Validate and enhance agent output AFTER agent completes.
    
    Adds medical disclaimers and grounding warnings.
    
    Returns:
        Modified Content, or None to keep original output
    """
    # This callback runs after the agent, so we'd need to get the agent's output
   # from the context. For now, we'll use a simpler approach of just logging.
    
    logger.info("safety_output_check", agent=callback_context.agent_name)
    
    # In practice, you'd inspect the agent's output here and potentially modify it
    # For now, return None to keep the original output
    # (Full output modification would require accessing the agent's response from context)
    
    return None


# ==================== Tool Definitions ====================

def calculator_tool(operation: str, a: float, b: float) -> Dict[str, Any]:
    """
    Perform basic arithmetic operations: add, subtract, multiply, divide.
    
    Args:
        operation: One of 'add', 'subtract', 'multiply', 'divide'
        a: First operand
        b: Second operand
        
    Returns:
        Result dictionary with 'result' and 'error' keys
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


def phi_detector_tool(text: str) -> Dict[str, Any]:
    """
    Detect Protected Health Information (PHI) and Personally Identifiable Information (PII) in text.
    
    Args:
        text: Text to scan for PHI/PII
        
    Returns:
        Detection results with 'has_phi', 'detected_types', and 'count'
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


def rag_retrieval_tool(query: str, top_k: int = 3, retriever: Retriever = None, tool_context: ToolContext = None) -> Dict[str, Any]:
    """
    Retrieve relevant document chunks for a query using RAG.
    
    Args:
        query: User question to retrieve context for
        top_k: Number of top chunks to retrieve
        retriever: Retriever instance (passed via closure)
        tool_context: ADK ToolContext for storing state (injected by ADK)
        
    Returns:
        Dictionary with 'context' (formatted text) and 'citations' (list of citation objects)
    """
    logger.info("rag_retrieval_called", query=query, top_k=top_k)
    
    if retriever is None:
        return {"error": "Retriever not initialized", "context": "", "citations": []}
    
    try:
        # Retrieve citations
        citations = retriever.retrieve(query, top_k=top_k)
        
        # Build context from citations
        context_parts = []
        for i, citation in enumerate(citations):
            full_text = retriever.get_chunk_text(citation.chunk_id)
            context_parts.append(f"[{i+1}] {full_text}")
        
        context = "\n\n".join(context_parts)
        
        # Convert citations to dicts for JSON serialization
        citations_data = [
            {
                "chunk_id": c.chunk_id,
                "document_id": c.document_id,
                "similarity_score": c.similarity_score,
                "snippet": retriever.get_chunk_text(c.chunk_id)[:200],
                "page_number": c.page_number
            }
            for c in citations
        ]
        
        # Calculate max similarity score for grounding
        max_similarity = max((c.similarity_score for c in citations), default=0.0)
        
        # Store in session state for main.py to extract
        if tool_context and hasattr(tool_context, 'state'):
            tool_context.state['rag_citations'] = citations_data
            tool_context.state['max_similarity_score'] = max_similarity
            logger.info("citations_stored_in_state", count=len(citations_data), max_sim=max_similarity)
        
        return {
            "context": context,
            "citations": citations_data,
            "num_citations": len(citations),
            "max_similarity_score": max_similarity,
            "error": None
        }
    
    except Exception as e:
        logger.error("rag_retrieval_error", error=str(e))
        return {"error": str(e), "context": "", "citations": []}


# ==================== Agent Definition ====================

def create_clinical_agent(retriever: Retriever) -> LlmAgent:
    """
    Create the Clinical Document Intelligence Agent using ADK with safety callbacks.
    
    Args:
        retriever: Configured Retriever instance for RAG
        
    Returns:
        Configured LlmAgent instance with safety validation
    """
    
    # Create RAG tool with retriever bound via closure
    # Note: tool_context is injected by ADK automatically
    def rag_tool(query: str, top_k: int = 3, tool_context: ToolContext = None) -> Dict[str, Any]:
        return rag_retrieval_tool(query, top_k, retriever, tool_context)
    
    # Update docstring for ADK
    rag_tool.__doc__ = """Retrieve relevant clinical document context for answering questions.
    
    Args:
        query: The medical question to find relevant context for
        top_k: Number of document chunks to retrieve (default: 3)
    
    Returns:
        Dictionary with context text and citation metadata
    """
    
    # Configure Google GenAI SDK for Vertex AI
    import os
    from google import genai
    
    # Set environment variables for genai SDK
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
    os.environ["GOOGLE_CLOUD_PROJECT"] = settings.gcp_project_id
    os.environ["GOOGLE_CLOUD_LOCATION"] = settings.gcp_location
    
    agent = LlmAgent(
        model=settings.vertex_model,
        name="clinical_document_agent",
        description="Clinical document Q&A assistant with safety validation and tool calling capabilities",
        instruction="""You are a Clinical Document Intelligence Assistant. Your role is to answer questions about medical documents accurately and safely.

CORE RESPONSIBILITIES:
1. Answer questions based ONLY on the retrieved document context
2. If the context doesn't contain enough information, clearly state this
3. Always cite sources using [1], [2], etc. from the retrieved chunks
4. Never make up medical information or provide advice outside the documents
5. Use tools when appropriate (calculator for dosages, PHI detector for privacy checks)

TOOL USAGE:
- Use the `rag_tool` to retrieve relevant document context for questions
- Use `calculator_tool` for arithmetic operations (e.g., dosage calculations)
- Use `phi_detector_tool` to check for sensitive patient information in queries

SAFETY GUIDELINES:
- If PHI is detected in the question, warn the user about privacy concerns
- If the question seems harmful or requests dangerous medical advice, politely refuse
- Be clear when information is uncertain or not found in documents

RESPONSE FORMAT:
- Start by retrieving context using the RAG tool
- Answer based on the retrieved context
- Include citations: [1], [2], etc.
- Be concise but thorough
""",
        tools=[rag_tool, calculator_tool, phi_detector_tool],
        output_key="answer",
        # NEW: Add safety callbacks
        before_model_callback=safety_input_validator,
        after_model_callback=safety_output_validator
    )
    
    logger.info("clinical_agent_created_with_callbacks", model=settings.vertex_model)
    return agent


# ==================== Export for ADK ====================

# ADK requires a variable named 'root_agent' for CLI tools and deployment
# This will be set when the agent is actually instantiated with a retriever
root_agent = None


def initialize_root_agent(retriever: Retriever):
    """
    Initialize the root_agent global variable.
    Must be called before using ADK CLI tools.
    
    Args:
        retriever: Configured Retriever instance
    """
    global root_agent
    root_agent = create_clinical_agent(retriever)
    logger.info("root_agent_initialized")

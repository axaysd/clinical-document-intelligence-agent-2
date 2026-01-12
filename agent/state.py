"""
Agent state model for tracking workflow execution.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from models.schemas import Citation, ToolCall, AuditEvent, SafetyValidation

@dataclass
class AgentState:
    """State object passed through agent workflow."""
    
    # Input
    query: str
    session_id: str
    request_id: str
    top_k: int = 5
    
    # Intent classification
    intent: Optional[str] = None  # "retrieve", "tool_call", or "both"
    
    # Retrieval
    citations: List[Citation] = field(default_factory=list)
    retrieved_context: str = ""
    
    # Tool execution
    tool_calls: List[ToolCall] = field(default_factory=list)
    tool_results: Dict[str, Any] = field(default_factory=dict)
    
    # Answer generation
    answer: str = ""
    
    # Safety validation
    safety_validation: Optional[SafetyValidation] = None
    should_refuse: bool = False
    refusal_message: str = ""
    
    # Audit trail
    audit_events: List[AuditEvent] = field(default_factory=list)
    
    # Metadata
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    def add_audit_event(self, event: AuditEvent):
        """Add an audit event to the trail."""
        self.audit_events.append(event)
    
    def get_total_duration_ms(self) -> float:
        """Calculate total duration in milliseconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0

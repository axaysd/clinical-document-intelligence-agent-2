"""
Pydantic models for API request/response validation and data structures.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


# ==================== Enums ====================

class NodeType(str, Enum):
    """Agent node types."""
    INTENT_CLASSIFIER = "intent_classifier"
    RETRIEVER = "retriever"
    MCP_TOOL = "mcp_tool"
    SYNTHESIZER = "synthesizer"
    SAFETY_VALIDATOR = "safety_validator"
    AUDIT_LOGGER = "audit_logger"


class SafetyDecision(str, Enum):
    """Safety validation decisions."""
    APPROVED = "approved"
    REJECTED = "rejected"
    WARNING = "warning"


# ==================== Core Data Models ====================

class Citation(BaseModel):
    """Citation to a document chunk."""
    chunk_id: str
    document_id: str
    similarity_score: float
    snippet: str
    page_number: Optional[int] = None


class ToolCall(BaseModel):
    """Record of a tool invocation."""
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str


class AuditEvent(BaseModel):
    """Audit trail event."""
    node_type: NodeType
    timestamp: str
    data: Dict[str, Any]
    duration_ms: Optional[float] = None


class SafetyValidation(BaseModel):
    """Safety validation result."""
    decision: SafetyDecision
    confidence_score: float
    grounding_score: float
    flags: List[str] = Field(default_factory=list)
    message: Optional[str] = None


# ==================== API Models ====================

# Upload Endpoint
class UploadResponse(BaseModel):
    """Response from document upload."""
    document_id: str
    filename: str
    num_chunks: int
    status: str
    message: str


# Query Endpoint
class QueryRequest(BaseModel):
    """Request for document query."""
    question: str = Field(..., min_length=1, max_length=1000)
    session_id: Optional[str] = None
    top_k: Optional[int] = Field(default=5, ge=1, le=20)


class QueryResponse(BaseModel):
    """Response from document query."""
    request_id: str
    answer: str
    citations: List[Citation]
    confidence_score: float
    grounding_score: float
    tool_calls: List[ToolCall]
    safety_flags: List[str]
    timestamp: str


# Audit Endpoint
class AuditResponse(BaseModel):
    """Audit trail for a request."""
    request_id: str
    query: str
    retrieved_chunks: List[Citation]
    tool_calls: List[ToolCall]
    safety_validation: SafetyValidation
    audit_events: List[AuditEvent]
    total_duration_ms: float
    timestamp: str


# Evaluation Endpoint
class EvalRequest(BaseModel):
    """Request to run evaluation."""
    dataset_path: Optional[str] = None
    generate_new: bool = False
    num_samples: Optional[int] = None


class EvalMetrics(BaseModel):
    """Evaluation metrics."""
    dataset_version: str
    total_samples: int
    groundedness_avg: float
    correctness_avg: float
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    refusal_rate: float
    details: Optional[Dict[str, Any]] = None


class EvalResponse(BaseModel):
    """Response from evaluation run."""
    status: str
    metrics: Optional[EvalMetrics] = None
    output_path: Optional[str] = None
    message: str


# Health Endpoint
class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: str
    components: Dict[str, str]


# ==================== Internal Models ====================

class Chunk(BaseModel):
    """Document chunk with metadata."""
    chunk_id: str
    document_id: str
    text: str
    embedding: Optional[List[float]] = None
    page_number: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentMetadata(BaseModel):
    """Metadata for uploaded document."""
    document_id: str
    filename: str
    upload_timestamp: str
    num_pages: Optional[int] = None
    num_chunks: int
    index_path: str

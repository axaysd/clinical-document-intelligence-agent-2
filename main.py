"""
FastAPI application for Clinical Document Intelligence Agent.
Production-grade agentic RAG with MCP tools, safety validation, and audit logging.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pathlib import Path
import shutil
import json
from datetime import datetime

from config import get_settings
from utils.logger import configure_logging, get_logger, set_request_id
from utils.helpers import generate_request_id, generate_document_id, generate_session_id, sanitize_filename, get_timestamp
from models.schemas import (
    QueryRequest, QueryResponse, AuditResponse, EvalRequest, EvalResponse,
    HealthResponse, UploadResponse
)
from rag.extractor import PDFExtractor
from rag.chunker import TextChunker
from rag.embeddings import EmbeddingGenerator
from rag.index import FAISSIndexManager
from rag.retriever import Retriever
from agent.agent import create_clinical_agent, initialize_root_agent
from google.adk.runners import InMemoryRunner
from google.genai import types
from eval.dataset_generator import DatasetGenerator
# from eval.evaluator import Evaluator  # Disabled - needs refactor for ADK
# from eval.metrics import MetricsCalculator  # Disabled - needs refactor for ADK

# Initialize settings and logging
settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Clinical Document Intelligence Agent",
    description="Agentic RAG system for clinical document Q&A with safety validation",
    version="1.0.0"
)

# Global components (initialized once)
index_manager = FAISSIndexManager()
retriever = Retriever(index_manager)

# ADK components - Use InMemoryRunner (simpler, bundles session service)
clinical_agent = create_clinical_agent(retriever)
initialize_root_agent(retriever)  # For ADK CLI tools

runner = InMemoryRunner(
    agent=clinical_agent,
    app_name="mediagent_app"
)

# Access bundled session service
session_service = runner.session_service

# In-memory audit store (in production, use database)
audit_store = {}

logger.info("fastapi_app_initialized")


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    logger.info("application_starting")
    settings.ensure_directories()


@app.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a PDF document.
    
    - Extracts text from PDF
    - Chunks text with overlap
    - Generates embeddings
    - Stores in FAISS index
    """
    request_id = generate_request_id()
    set_request_id(request_id)
    logger.info("upload_requested", filename=file.filename)
    
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Save uploaded file
        safe_filename = sanitize_filename(file.filename)
        doc_id = generate_document_id(safe_filename)
        upload_path = Path(settings.upload_dir) / f"{doc_id}.pdf"
        
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info("file_saved", path=str(upload_path))
        
        # Extract text
        extractor = PDFExtractor()
        pages = extractor.extract_text(str(upload_path))
        
        # Chunk text
        chunker = TextChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        chunks = chunker.chunk_document(pages, doc_id)
        
        # Generate embeddings
        embedding_gen = EmbeddingGenerator()
        texts = [chunk.text for chunk in chunks]
        embeddings = embedding_gen.generate_embeddings(texts)
        
        # Add embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding
        
        # Add to index
        index_manager.add_chunks(chunks)
        index_manager.save()
        
        logger.info("document_indexed", doc_id=doc_id, num_chunks=len(chunks))
        
        return UploadResponse(
            document_id=doc_id,
            filename=safe_filename,
            num_chunks=len(chunks),
            status="success",
            message=f"Document processed successfully with {len(chunks)} chunks"
        )
    
    except Exception as e:
        logger.error("upload_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Query documents using ADK agent workflow.
    
    - Uses ADK Runner to execute agent
    - Retrieves relevant chunks via RAG tool
    - Calls tools if needed (calculator, PHI detector)
    - Generates grounded answer with safety validation
    - Returns answer with citations
    """
    request_id = generate_request_id()
    set_request_id(request_id)
    logger.info("query_requested", question=request.question)
    
    try:
        # Generate or use provided session ID
        session_id = request.session_id or generate_session_id()
        user_id = "default_user"  # Could be from authentication
        
        # Create or get session
        session = await session_service.get_session(
            app_name="mediagent_app",
            user_id=user_id,
            session_id=session_id
        )
        
        if session is None:
            session = await session_service.create_session(
                app_name="mediagent_app",
                user_id=user_id,
                session_id=session_id
            )
        
        # Store user message in session state for callbacks
        if session and hasattr(session, 'state'):
            session.state['last_user_message'] = request.question
        
        # Create user message  
        user_content = types.Content(
            role='user',
            parts=[types.Part(text=request.question)]
        )
        
        # Run agent and collect response
        final_answer = ""
        citations = []
        tool_calls = []
        
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_content
        ):
            # Collect final response
            if event.is_final_response() and event.content and event.content.parts:
                final_answer = event.content.parts[0].text
            
            # Collect tool calls from events
            if hasattr(event, 'function_calls') and event.function_calls:
                for fc in event.function_calls:
                    tool_calls.append({
                        "tool_name": fc.name,
                        "arguments": dict(fc.args) if hasattr(fc, 'args') else {},
                        "result": None  # Will be populated from function responses
                    })
        
        # Get updated session to extract citations and state
        updated_session = await session_service.get_session(
            app_name="mediagent_app",
            user_id=user_id,
            session_id=session_id
        )
        
        # Extract citations from session state (set by RAG tool via ToolContext)
        grounding_score = 0.0
        if updated_session and hasattr(updated_session, 'state'):
            state_dict = updated_session.state if isinstance(updated_session.state, dict) else {}
            if hasattr(updated_session.state, 'to_dict'):
                state_dict = updated_session.state.to_dict()
            
            # Citations stored by RAG tool
            if 'rag_citations' in state_dict:
                citations = state_dict['rag_citations']
                logger.info("citations_extracted", count=len(citations))
            
            # Use max similarity score for grounding (more accurate than count)
            if 'max_similarity_score' in state_dict:
                grounding_score = state_dict['max_similarity_score']
                logger.info("grounding_score_from_similarity", score=grounding_score)
        
        # Fallback: if still no grounding score but have citations, calculate from them
        if grounding_score == 0.0 and citations:
            similarity_scores = [c.get('similarity_score', 0) for c in citations if isinstance(c, dict)]
            if similarity_scores:
                grounding_score = max(similarity_scores)
        
        # Build response
        response = QueryResponse(
            request_id=request_id,
            answer=final_answer or "No answer generated",
            citations=citations,
            confidence_score=grounding_score,  # Use grounding as proxy for confidence
            grounding_score=grounding_score,
            tool_calls=tool_calls,
            safety_flags=[],       # TODO: Implement safety callback for flags
            timestamp=get_timestamp()
        )
        
        # Store minimal audit info (ADK has its own session tracking)
        audit_store[request_id] = {
            "question": request.question,
            "answer": final_answer,
            "session_id": session_id,
            "timestamp": get_timestamp()
        }
        
        logger.info("query_completed", request_id=request_id)
        return response
    
    except Exception as e:
        logger.error("query_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.get("/audit/{request_id}", response_model=AuditResponse)
async def get_audit_trail(request_id: str):
    """
    Retrieve audit information for a request.
    
    Note: With ADK, detailed audit trails are managed in sessions.
    This endpoint provides basic audit info from our tracking.
    """
    set_request_id(request_id)
    logger.info("audit_requested", request_id=request_id)
    
    if request_id not in audit_store:
        raise HTTPException(status_code=404, detail="Request ID not found")
    
    audit_data = audit_store[request_id]
    
    # Build simplified audit response
    # TODO: Enhance with ADK session history retrieval
    response = AuditResponse(
        request_id=request_id,
        query=audit_data.get("question", ""),
        retrieved_chunks=[],  # TODO: Extract from ADK session
        tool_calls=[],         # TODO: Extract from ADK session  
        safety_validation=None,  # TODO: Implement via callbacks
        audit_events=[],       # TODO: Extract from ADK session
        total_duration_ms=0,   # TODO: Calculate from ADK events
        timestamp=audit_data.get("timestamp", get_timestamp())
    )
    
    return response


# TODO: Eval endpoint disabled - needs rework for ADK
# The Evaluator class still uses the old AgentOrchestrator
# Need to update eval/evaluator.py to use ADK Runner
'''
@app.post("/eval", response_model=EvalResponse)
async def run_evaluation(request: EvalRequest):
    """
    Run evaluation pipeline.
    
    - Generate synthetic dataset (if requested)
    - Execute queries
    - Calculate metrics (groundedness, correctness, latency)
    - Return evaluation report
    """
    eval_request_id = generate_request_id()
    set_request_id(eval_request_id)
    logger.info("eval_requested", generate_new=request.generate_new)
    
    try:
        dataset_path = request.dataset_path
        
        # Generate new dataset if requested
        if request.generate_new or not dataset_path:
            generator = DatasetGenerator(index_manager)
            num_samples = request.num_samples or settings.eval_synthetic_samples
            dataset = generator.generate_dataset(num_samples=num_samples)
            dataset_path = generator.save_dataset(dataset)
            logger.info("dataset_generated", path=dataset_path, samples=len(dataset['samples']))
        
        # Run evaluation
        evaluator = Evaluator(orchestrator)
        eval_results = evaluator.run_evaluation(dataset_path)
        
        # Calculate metrics
        metrics_calc = MetricsCalculator()
        metrics = metrics_calc.calculate_metrics(eval_results)
        
        # Save results
        results_path = Path(settings.data_dir) / "eval_results.json"
        with open(results_path, 'w') as f:
            json.dump({
                'metrics': metrics.model_dump(),
                'eval_results': eval_results
            }, f, indent=2)
        
        logger.info("eval_completed", metrics_path=str(results_path))
        
        return EvalResponse(
            status="success",
            metrics=metrics,
            output_path=str(results_path),
            message=f"Evaluation completed: {metrics.total_samples} samples evaluated"
        )
    
    except Exception as e:
        logger.error("eval_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
'''


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring."""
    index_stats = index_manager.get_stats()
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=get_timestamp(),
        components={
            "faiss_index": f"{index_stats['num_chunks']} chunks",
            "adk_agent": "ready",
            "tools": "3 tools available"  # calculator, PHI detector, RAG
        }
    )


# ==================== Tool Endpoints ====================
# Direct access to tools for testing (also used internally by agent)

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from agent.agent import calculator_tool, phi_detector_tool


class CalculatorRequest(BaseModel):
    """Request for calculator tool."""
    operation: str = Field(..., description="One of: add, subtract, multiply, divide")
    a: float = Field(..., description="First operand")
    b: float = Field(..., description="Second operand")


class PHIDetectorRequest(BaseModel):
    """Request for PHI detector tool."""
    text: str = Field(..., description="Text to scan for PHI/PII")


class ToolResponse(BaseModel):
    """Generic tool response."""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None


@app.get("/tools", tags=["Tools"])
async def list_tools():
    """
    List all available tools.
    
    Returns the tools that can be called directly or used by the agent.
    """
    return {
        "tools": [
            {
                "name": "calculator",
                "endpoint": "/tools/calculator",
                "description": "Perform basic arithmetic: add, subtract, multiply, divide",
                "parameters": ["operation", "a", "b"]
            },
            {
                "name": "phi_detector",
                "endpoint": "/tools/phi_detector",
                "description": "Detect PHI/PII in text (email, phone, SSN, MRN, DOB)",
                "parameters": ["text"]
            },
            {
                "name": "rag_retrieval",
                "endpoint": "(internal only - use /query)",
                "description": "Retrieve relevant document chunks for a query",
                "parameters": ["query", "top_k"]
            }
        ]
    }


@app.post("/tools/calculator", response_model=ToolResponse, tags=["Tools"])
async def call_calculator(request: CalculatorRequest):
    """
    Call the calculator tool directly.
    
    Performs basic arithmetic operations.
    
    **Operations:**
    - `add`: a + b
    - `subtract`: a - b
    - `multiply`: a * b
    - `divide`: a / b (returns error if b is 0)
    
    **Example:**
    ```json
    {"operation": "multiply", "a": 70, "b": 0.5}
    ```
    """
    logger.info("direct_calculator_call", operation=request.operation, a=request.a, b=request.b)
    
    result = calculator_tool(request.operation, request.a, request.b)
    
    if result.get("error"):
        return ToolResponse(success=False, result=result.get("result"), error=result["error"])
    
    return ToolResponse(success=True, result=result["result"], error=None)


@app.post("/tools/phi_detector", response_model=ToolResponse, tags=["Tools"])
async def call_phi_detector(request: PHIDetectorRequest):
    """
    Call the PHI detector tool directly.
    
    Scans text for Protected Health Information (PHI) and Personally Identifiable Information (PII).
    
    **Detected patterns:**
    - Email addresses
    - Phone numbers (xxx-xxx-xxxx format)
    - Social Security Numbers (xxx-xx-xxxx)
    - Medical Record Numbers (MRN: xxxxxx)
    - Dates of Birth (DOB: xx/xx/xxxx)
    
    **Example:**
    ```json
    {"text": "Patient email: john@example.com, SSN: 123-45-6789"}
    ```
    """
    logger.info("direct_phi_detector_call", text_length=len(request.text))
    
    result = phi_detector_tool(request.text)
    
    return ToolResponse(
        success=True,
        result={
            "has_phi": result["has_phi"],
            "detected_types": result["detected_types"],
            "count": result["count"]
        },
        error=result.get("error")
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower()
    )

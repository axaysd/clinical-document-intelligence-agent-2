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
from agent.nodes import AgentNodes
from agent.orchestrator import AgentOrchestrator
from agent.state import AgentState
from eval.dataset_generator import DatasetGenerator
from eval.evaluator import Evaluator
from eval.metrics import MetricsCalculator

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
agent_nodes = AgentNodes(retriever)
orchestrator = AgentOrchestrator(agent_nodes)

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
    Query documents using agentic workflow.
    
    - Runs intent classification
    - Retrieves relevant chunks
    - Calls MCP tools if needed
    - Generates grounded answer
    - Validates safety
    - Returns answer with citations
    """
    request_id = generate_request_id()
    set_request_id(request_id)
    logger.info("query_requested", question=request.question)
    
    try:
        # Create agent state
        state = AgentState(
            query=request.question,
            session_id=request.session_id or generate_session_id(),
            request_id=request_id,
            top_k=request.top_k or settings.top_k_retrieval
        )
        
        # Execute agent workflow
        result_state = orchestrator.execute(state)
        
        # Store audit trail
        audit_store[request_id] = result_state
        
        # Build response
        response = QueryResponse(
            request_id=request_id,
            answer=result_state.answer,
            citations=result_state.citations,
            confidence_score=result_state.safety_validation.confidence_score if result_state.safety_validation else 0.0,
            grounding_score=result_state.safety_validation.grounding_score if result_state.safety_validation else 0.0,
            tool_calls=result_state.tool_calls,
            safety_flags=result_state.safety_validation.flags if result_state.safety_validation else [],
            timestamp=get_timestamp()
        )
        
        logger.info("query_completed", request_id=request_id)
        return response
    
    except Exception as e:
        logger.error("query_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.get("/audit/{request_id}", response_model=AuditResponse)
async def get_audit_trail(request_id: str):
    """
    Retrieve full audit trail for a request.
    
    - Retrieved chunks with similarity scores
    - Tool calls and results
    - Safety validation decisions
    - Performance metrics
    """
    set_request_id(request_id)
    logger.info("audit_requested", request_id=request_id)
    
    if request_id not in audit_store:
        raise HTTPException(status_code=404, detail="Request ID not found")
    
    state = audit_store[request_id]
    
    response = AuditResponse(
        request_id=request_id,
        query=state.query,
        retrieved_chunks=state.citations,
        tool_calls=state.tool_calls,
        safety_validation=state.safety_validation,
        audit_events=state.audit_events,
        total_duration_ms=state.get_total_duration_ms(),
        timestamp=get_timestamp()
    )
    
    return response


@app.post("/eval", response_model=EvalResponse)
async def run_evaluation(request: EvalRequest, background_tasks: BackgroundTasks):
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
        results_dir = Path(settings.eval_datasets_dir) / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
        results_path = results_dir / f"eval_results_{timestamp}.json"
        
        with open(results_path, 'w') as f:
            json.dump({
                'metrics': metrics.dict(),
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
            "agent": "ready",
            "mcp_tools": "available"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower()
    )

# Architecture Documentation

## System Architecture

### High-Level Overview

The Clinical Document Intelligence Agent is built as a production-grade agentic RAG system with the following key components:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FastAPI Service                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │   Upload     │    │    Query     │    │  Evaluation  │          │
│  │   Pipeline   │    │   Pipeline   │    │   Pipeline   │          │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘          │
│         │                   │                    │                  │
│  ┌──────▼──────────────────▼────────────────────▼──────┐           │
│  │           Agent Orchestrator (Custom ADK)            │           │
│  │                                                       │           │
│  │  ┌─────────────────────────────────────────────┐    │           │
│  │  │  1. Intent Classifier                       │    │           │
│  │  │     ↓                                        │    │           │
│  │  │  2. Retriever ──→ FAISS Index               │    │           │
│  │  │     ↓                                        │    │           │
│  │  │  3. MCP Tool Executor ──→ MCP Server        │    │           │
│  │  │     ↓                                        │    │           │
│  │  │  4. Answer Synthesizer (Gemini)             │    │           │
│  │  │     ↓                                        │    │           │
│  │  │  5. Safety Validator                        │    │           │
│  │  │     ↓                                        │    │           │
│  │  │  6. Audit Logger                            │    │           │
│  │  └─────────────────────────────────────────────┘    │           │
│  └────────────────────────────────────────────────────┘           │
│                                                                       │
├─────────────────────────────────────────────────────────────────────┤
│  RAG Components         │  Safety Layer      │  MCP Tools           │
│  • PDF Extractor        │  • Prompt Inj.     │  • Calculator        │
│  • Text Chunker         │  • PHI Masking     │  • PHI Detector      │
│  • Vertex Embeddings    │  • Grounding       │                      │
│  • FAISS Indexing       │  • Confidence      │                      │
│  • Citation Gen         │  • Refusal Policy  │                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. FastAPI Service Layer

**Purpose**: HTTP API interface for all operations

**Key Endpoints**:
- `/upload` - Document ingestion pipeline
- `/query` - Agentic question-answering
- `/audit/{request_id}` - Audit trail retrieval
- `/eval` - Evaluation pipeline execution
- `/health` - Health check

**Technology**: FastAPI with Uvicorn, async I/O, Pydantic validation

---

### 2. Agent Orchestrator

**Purpose**: Coordinates multi-stage agent workflow

**Workflow Stages**:

#### Stage 1: Intent Classification
- Analyzes user query to determine intent
- Routes to appropriate pipeline (retrieval, tools, or both)
- Uses Gemini for intent understanding

#### Stage 2: Retrieval
- Generates query embedding using Vertex AI
- Performs similarity search in FAISS index
- Returns top-k most relevant chunks with scores

#### Stage 3: MCP Tool Execution
- Invokes external tools via MCP protocol
- Available tools: Calculator, PHI Detector
- Validates tool inputs and outputs

#### Stage 4: Answer Synthesis
- Combines retrieved context + tool results
- Generates grounded answer using Gemini
- Enforces citation requirements

#### Stage 5: Safety Validation
- Checks for prompt injection attempts
- Validates grounding score (min 0.7)
- Assesses confidence score
- Applies refusal policy if needed

#### Stage 6: Audit Logging
- Records all decisions and data flows
- Stores retrieval results, tool calls, safety flags
- Enables full traceability

---

### 3. RAG Pipeline

#### Document Upload Flow

```
PDF Upload
    ↓
Text Extraction (PyPDF2/pdfplumber)
    ↓
Smart Chunking (512 chars, 64 overlap)
    ↓
Embedding Generation (Vertex AI)
    ↓
FAISS Indexing + Metadata Storage
    ↓
Success Response
```

**Components**:

- **PDF Extractor** (`rag/extractor.py`)
  - Dual-mode extraction (PyPDF2 primary, pdfplumber fallback)
  - Handles complex layouts and scanned documents
  
- **Text Chunker** (`rag/chunker.py`)
  - Sentence-aware splitting
  - Configurable chunk size and overlap
  - Preserves document structure

- **Embedding Generator** (`rag/embeddings.py`)
  - Uses Vertex AI `text-embedding-004`
  - Batch processing for efficiency
  - Error handling and retries

- **FAISS Index Manager** (`rag/index.py`)
  - Local persistence with metadata
  - Efficient similarity search
  - Incremental updates

---

### 4. Query Processing Flow

```
User Query
    ↓
Intent Classification
    ↓
    ├─→ Retrieval Path
    │       ↓
    │   FAISS Search (top-k chunks)
    │       ↓
    │   Context Assembly
    │
    ├─→ Tool Path
    │       ↓
    │   MCP Tool Invocation
    │       ↓
    │   Tool Result Processing
    │
    └─→ Synthesis
            ↓
        Gemini Answer Generation
            ↓
        Safety Validation
            ↓
        Response with Citations
```

---

### 5. Safety Validation Pipeline

**Multi-Layer Defense**:

#### Layer 1: Input Validation
- Prompt injection detection
- Input sanitization
- Length limits

#### Layer 2: Retrieval Safety
- Grounding threshold enforcement (0.7)
- PHI masking in retrieved chunks
- Citation requirement

#### Layer 3: Generation Safety
- Template-based prompts
- Low temperature (0.1) for consistency
- Content filtering

#### Layer 4: Output Validation
- Confidence scoring
- Refusal policy application
- Medical disclaimer injection

**Safety Validators** (`safety/validators.py`):
- `PromptInjectionDetector`: Heuristic pattern matching
- `GroundingValidator`: Similarity score checking
- `ConfidenceAssessor`: Combined quality assessment

**Content Filters** (`safety/filters.py`):
- `PHIMasker`: Regex-based PII redaction
- `MedicalDisclaimerAdder`: Auto-disclaimer injection

---

### 6. MCP Tool Integration

**Model Context Protocol (MCP)** enables external tool calling:

**Architecture**:
```
Agent → MCP Client → MCP Server → Tool Implementation
```

**Available Tools**:

1. **Calculator** (`mcp/tools.py`)
   - Basic arithmetic operations
   - Input validation
   - Error handling

2. **PHI Detector** (`mcp/tools.py`)
   - Detects Protected Health Information
   - Returns masked output
   - Compliance support

**MCP Server** (`mcp/server.py`):
- Runs on port 50051
- gRPC-based communication
- Tool registration and discovery

---

### 7. Evaluation Pipeline

**Purpose**: Automated quality assessment

**Workflow**:

```
1. Dataset Generation
   ↓
   Sample chunks from FAISS
   ↓
   Generate Q/A pairs (Gemini)
   ↓
   Store versioned dataset

2. Evaluation Execution
   ↓
   Run queries through agent
   ↓
   Collect predictions + metadata

3. Metrics Calculation
   ↓
   LLM-as-Judge scoring
   ↓
   Latency analysis
   ↓
   Refusal rate calculation

4. Results Storage
   ↓
   Timestamped JSON output
```

**Metrics** (`eval/metrics.py`):
- **Groundedness**: Answer supported by facts (0-1)
- **Correctness**: Semantic similarity to expected (0-1)
- **Latency**: p50/p95/p99 percentiles
- **Refusal Rate**: % of queries refused

---

## Data Flow

### Upload Pipeline

```
Client → FastAPI → PDFExtractor → TextChunker → EmbeddingGenerator → FAISSIndex
                                                                            ↓
                                                                    Persistence
```

### Query Pipeline

```
Client → FastAPI → AgentOrchestrator
                        ↓
                   IntentClassifier
                        ↓
                   ┌────┴────┐
                   ↓         ↓
              Retriever   MCPClient
                   ↓         ↓
              FAISSIndex  MCPServer
                   ↓         ↓
                   └────┬────┘
                        ↓
                 AnswerSynthesizer (Gemini)
                        ↓
                 SafetyValidator
                        ↓
                   AuditLogger
                        ↓
                    Response
```

---

## Deployment Architecture

### Local Development

```
Developer Machine
    ↓
Docker Container (mediagent:latest)
    ↓
FastAPI (port 8000)
    ↓
Vertex AI APIs (cloud)
```

### Production (GKE)

```
Internet
    ↓
LoadBalancer (External IP)
    ↓
GKE Service (port 80 → 8000)
    ↓
Deployment (2 replicas)
    ↓
Pods (mediagent containers)
    ↓
    ├─→ FAISS Index (EmptyDir volume)
    ├─→ Vertex AI APIs
    └─→ MCP Server (internal)
```

**Infrastructure**:
- **Cluster**: GKE Standard with 2 nodes (e2-standard-2)
- **Networking**: LoadBalancer service with external IP
- **Storage**: EmptyDir for FAISS index (ephemeral)
- **Auth**: Workload Identity for GCP API access
- **Monitoring**: Health probes (liveness + readiness)

---

## Security Architecture

### Authentication & Authorization
- **GCP**: Application Default Credentials
- **Workload Identity**: Pod-to-GCP service mapping
- **IAM**: Least-privilege service accounts

### Data Protection
- **In-Transit**: HTTPS for external, gRPC for internal
- **At-Rest**: Encrypted GCP storage
- **PHI Masking**: Regex-based PII redaction

### Safety Gates
- **Input**: Prompt injection detection
- **Processing**: Grounding validation
- **Output**: Confidence thresholds, refusal policy

---

## Scalability Considerations

### Current Limitations
- **FAISS Index**: In-memory, single-node
- **State**: Ephemeral (EmptyDir volumes)
- **Concurrency**: Limited by pod resources

### Future Enhancements
- **Distributed FAISS**: Sharded index across nodes
- **Persistent Storage**: Cloud Storage for index
- **Horizontal Scaling**: Autoscaling based on load
- **Caching**: Redis for frequent queries
- **Async Processing**: Pub/Sub for document uploads

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **API Framework** | FastAPI, Uvicorn |
| **LLM** | Google Gemini 1.5 Pro (Vertex AI) |
| **Embeddings** | Vertex AI text-embedding-004 |
| **Vector Store** | FAISS (CPU) |
| **PDF Processing** | PyPDF2, pdfplumber |
| **Validation** | Pydantic |
| **Logging** | Structlog |
| **Containerization** | Docker |
| **Orchestration** | Kubernetes (GKE) |
| **Tool Protocol** | MCP (Model Context Protocol) |

---

## Performance Characteristics

### Latency Targets
- **Upload**: <5s for 10-page PDF
- **Query**: <2s (p95) for simple retrieval
- **Query with Tools**: <3s (p95)

### Throughput
- **Concurrent Queries**: ~10 req/s per pod
- **Upload Rate**: ~5 docs/min

### Resource Usage
- **Memory**: ~2GB per pod (with index)
- **CPU**: ~1 vCPU per pod
- **Storage**: ~100MB per 1000 chunks

---

Built with ❤️ for regulated healthcare applications

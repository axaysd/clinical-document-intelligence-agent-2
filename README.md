# Clinical Document Intelligence Agent

<div align="center">

**Production-grade Agentic RAG system for clinical/pharma document Q&A**

[![Status](https://img.shields.io/badge/status-MVP-blue)](https://github.com/axaysd/clinical-document-intelligence-agent)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-00a393)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED)](https://www.docker.com/)
[![GKE](https://img.shields.io/badge/GKE-deployable-4285F4)](https://cloud.google.com/kubernetes-engine)

[Features](#-key-features) • [Quick Start](#-quick-start) • [Architecture](#️-architecture-overview) • [Deployment](#-docker-deployment) • [Cost Estimation](#-cost-estimation)

</div>

---

## 📋 Overview

A production-ready **Agentic RAG** system that combines retrieval-augmented generation with intelligent agent workflows for clinical document analysis. Built with Google Vertex AI, FAISS vector search, MCP tool integration, and comprehensive safety validation.

**Key Capabilities:**
- 🤖 Multi-stage agent workflow with intent classification and tool calling
- 📚 RAG pipeline with PDF processing, chunking, and vector search
- 🛡️ Multi-layer safety validation (prompt injection, PHI masking, grounding)
- 📊 Automated evaluation with LLM-as-judge metrics
- 🔍 Full audit trail and structured logging
- ☸️ Production deployment on Google Kubernetes Engine

---

## 🏗️ Architecture Overview

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

## ✨ Key Features

### Agentic Workflow
- **Intent Classification**: Routes queries to retrieval, tools, or both
- **Dynamic Tool Calling**: MCP protocol for calculator and PHI detector
- **Grounded Synthesis**: Gemini generates answers with citation enforcement
- **Safety Gates**: Multi-layer validation before response delivery

### RAG Pipeline
- **PDF Processing**: PyPDF2 + pdfplumber with fallback
- **Smart Chunking**: Sentence-aware splitting with overlap (512/64 chars)
- **Vertex Embeddings**: text-embedding-004 with batching
- **FAISS Vector Store**: Local persistence with metadata tracking
- **Citation Quality**: Similarity scores + snippet extraction

### Safety & Compliance
- **Prompt Injection Detection**: Heuristic-based pattern matching
- **PHI Masking**: Regex for email, phone, SSN, MRN, DOB
- **Grounding Threshold**: Configurable minimum similarity (default: 0.7)
- **Refusal Policy**: Explicit "I don't know" when evidence insufficient
- **Medical Disclaimers**: Auto-added to clinical answers

### Evaluation Pipeline
- **Synthetic Dataset Generation**: Gemini creates Q/A pairs from documents
- **LLM-as-Judge**: Groundedness and correctness scoring
- **Performance Metrics**: Latency p50/p95/p99, refusal rate
- **Versioned Artifacts**: Timestamped dataset storage

### Production Ready
- **Structured Logging**: JSON logs with request ID tracking
- **Audit Trail**: Full traceability of retrieval, tools, and safety decisions
- **Health Checks**: Liveness and readiness endpoints
- **Containerized**: Docker + Kubernetes manifests

---

## 📁 Project Structure

```
MediAgent/
├── main.py                      # FastAPI application (all endpoints)
├── config.py                    # Environment-based configuration
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Multi-stage container build
├── .env.example                 # Environment variable template
│
├── agent/                       # Agent orchestration
│   ├── orchestrator.py          # Workflow executor
│   ├── nodes.py                 # Agent nodes (classifier, retriever, etc.)
│   └── state.py                 # State management
│
├── rag/                         # RAG pipeline
│   ├── extractor.py             # PDF text extraction
│   ├── chunker.py               # Text chunking with overlap
│   ├── embeddings.py            # Vertex AI embeddings
│   ├── index.py                 # FAISS index manager
│   └── retriever.py             # Retrieval orchestration
│
├── mcp/                         # MCP server & client
│   ├── server.py                # MCP tool server (port 50051)
│   ├── client.py                # MCP client for agent
│   └── tools.py                 # Calculator + PHI detector tools
│
├── safety/                      # Safety validation
│   ├── validators.py            # Prompt injection, grounding, confidence
│   └── filters.py               # Medical disclaimers, content safety
│
├── eval/                        # Evaluation pipeline
│   ├── dataset_generator.py    # Synthetic Q/A generation
│   ├── evaluator.py             # Evaluation job runner
│   └── metrics.py               # LLM-as-judge scoring
│
├── models/                      # Data models
│   └── schemas.py               # Pydantic models for API
│
├── utils/                       # Utilities
│   ├── logger.py                # Structured logging
│   └── helpers.py               # ID generation, hashing
│
└── k8s/                         # Kubernetes manifests
    ├── deployment.yaml          # GKE deployment
    └── service.yaml             # LoadBalancer service
```

---

## 🚀 Quick Start

### Prerequisites

#### Required Software
- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop)
- **Google Cloud SDK** - [Install](https://cloud.google.com/sdk/docs/install)
- **kubectl** (for GKE deployment) - [Install](https://kubernetes.io/docs/tasks/tools/)

#### Google Cloud Setup

1. **Create a GCP Project**
   ```bash
   gcloud projects create YOUR_PROJECT_ID
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Enable Required APIs**
   ```bash
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable artifactregistry.googleapis.com
   gcloud services enable container.googleapis.com
   ```

3. **Set Up Authentication**
   ```bash
   gcloud auth application-default login
   ```

4. **Create Service Account** (for production deployment)
   ```bash
   gcloud iam service-accounts create mediagent
   
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:mediagent@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"
   ```

#### Local Development Setup

**Minimum Requirements:**
- 8GB RAM (16GB recommended)
- 10GB free disk space
- Active internet connection for API calls

### 1. Setup Environment

```bash
# Clone/navigate to project
cd MediAgent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your GCP project ID and settings
```

### 2. Authenticate with Google Cloud

```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### 3. Start MCP Server (Terminal 1)

```bash
python -m mcp.server
# Server runs on http://localhost:50051
```

### 4. Start FastAPI Application (Terminal 2)

```bash
python main.py
# API runs on http://localhost:8000
```

### 5. Test Endpoints

#### Upload a Document

```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@path/to/clinical_document.pdf"

# Response:
# {
#   "document_id": "doc_a1b2c3d4e5f6",
#   "filename": "clinical_document.pdf",
#   "num_chunks": 42,
#   "status": "success",
#   "message": "Document processed successfully with 42 chunks"
# }
```

#### Query the System

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the recommended dosage for hypertension?",
    "session_id": "user123",
    "top_k": 5
  }'

# Response:
# {
#   "request_id": "req_xyz789abc012",
#   "answer": "Based on the documentation, the recommended dosage is...",
#   "citations": [
#     {
#       "chunk_id": "doc_a1b2_chunk_0012",
#       "similarity_score": 0.89,
#       "snippet": "For hypertension management, the initial dose..."
#     }
#   ],
#   "confidence_score": 0.85,
#   "grounding_score": 0.89,
#   "tool_calls": [],
#   "safety_flags": []
# }
```

#### Retrieve Audit Trail

```bash
curl "http://localhost:8000/audit/req_xyz789abc012"

# Response:
# {
#   "request_id": "req_xyz789abc012",
#   "query": "What is the recommended dosage for hypertension?",
#   "retrieved_chunks": [...],
#   "tool_calls": [],
#   "safety_validation": {
#     "decision": "approved",
#     "grounding_score": 0.89,
#     "confidence_score": 0.85
#   },
#   "audit_events": [...]
# }
```

#### Run Evaluation

```bash
curl -X POST "http://localhost:8000/eval" \
  -H "Content-Type: application/json" \
  -d '{
    "generate_new": true,
    "num_samples": 20
  }'

# Response:
# {
#   "status": "success",
#   "metrics": {
#     "groundedness_avg": 0.92,
#     "correctness_avg": 0.85,
#     "latency_p50_ms": 1200,
#     "latency_p95_ms": 2800,
#     "refusal_rate": 0.04
#   },
#   "output_path": "data/eval_datasets/results/eval_results_2026-01-11_18-20-00.json"
# }
```

---

## 🔒 Safety Design

### Multi-Layer Safety Architecture

#### 1. **Input Validation**
- **Prompt Injection Detection**: Heuristic patterns for "ignore instructions", special tokens
- **Input Sanitization**: Length limits, character filtering

#### 2. **Retrieval Safety**
- **Grounding Threshold**: Minimum similarity score (0.7) for answer generation
- **Citation Enforcement**: Every answer must reference source chunks
- **PHI Masking**: Redact email, phone, SSN, MRN, DOB in retrieved chunks

#### 3. **Generation Safety**
- **Template-Based Prompts**: Structured prompts with clear boundaries
- **Parameter Constraints**: Low temperature (0.1) for factual consistency
- **Content Filtering**: Block unsafe medical advice patterns

#### 4. **Output Validation**
- **Confidence Scoring**: Combined grounding + answer quality assessment
- **Refusal Policy**: Explicit rejection when confidence < threshold
- **Medical Disclaimers**: Auto-added to clinical content
- **Safety Flags**: Transparent reporting of detected issues

### Example Safety Flow

```
User Query: "What is aspirin dosage?"
  ↓
[Prompt Injection Check] ✓ Pass
  ↓
[FAISS Retrieval] → Top chunk: similarity = 0.92
  ↓
[Grounding Check] ✓ Pass (0.92 > 0.7)
  ↓
[PHI Masking] → No PHI detected
  ↓
[Gemini Synthesis] → "Based on [1], aspirin dosage is 75-325mg..."
  ↓
[Confidence Assessment] → 0.88
  ↓
[Medical Disclaimer] → Added to answer
  ↓
[Response] ✓ Delivered with citations
```

---

## 📊 Evaluation Workflow

### 1. **Dataset Generation**

```python
# Synthetic Q/A pairs generated from indexed documents
POST /eval {"generate_new": true, "num_samples": 50}
```

**Process**:
1. Sample chunks from FAISS index
2. Use Gemini to generate question + expected answer
3. Store with source chunk ID
4. Version dataset (timestamped folder)

**Output**: `data/eval_datasets/2026-01-11_18-20-00/dataset.json`

### 2. **Evaluation Execution**

- Load dataset samples
- Execute each question through agent workflow
- Collect predictions, latencies, safety flags
- Store results with metadata

### 3. **Metrics Calculation**

#### Groundedness (LLM-as-Judge)
```
Prompt: "Rate if answer is supported by facts (0-1)"
Scoring: Average across all samples
```

#### Correctness (LLM-as-Judge)
```
Prompt: "Rate semantic similarity to expected answer (0-1)"
Scoring: Average across all samples
```

#### Latency Metrics
```
p50, p95, p99 percentiles from query execution times
```

#### Refusal Rate
```
Percentage of queries where system refused to answer
```

### 4. **Output**

```json
{
  "metrics": {
    "dataset_version": "2026-01-11_18-20-00",
    "total_samples": 50,
    "groundedness_avg": 0.92,
    "correctness_avg": 0.85,
    "latency_p50_ms": 1200,
    "latency_p95_ms": 2800,
    "latency_p99_ms": 3500,
    "refusal_rate": 0.04
  }
}
```

---

## 🐳 Docker Deployment

### Build Image

```bash
docker build -t mediagent:latest .
```

### Run Locally

**Linux/Mac:**
```bash
docker run -p 8000:8000 \
  -e GCP_PROJECT_ID=your-project-id \
  -e GCP_REGION=us-central1 \
  -v $(pwd)/data:/app/data \
  mediagent:latest
```

**Windows PowerShell:**
```powershell
docker run -p 8000:8000 -e GCP_PROJECT_ID=your-project-id -e GCP_REGION=us-central1 -v ${PWD}/data:/app/data mediagent:latest
```

### Push to Container Registry

#### 1. Enable Artifact Registry API

```bash
gcloud services enable artifactregistry.googleapis.com
```

#### 2. Configure Docker Authentication

```bash
gcloud auth configure-docker
```

#### 3. Tag and Push Image

```bash
docker tag mediagent:latest gcr.io/YOUR_PROJECT_ID/mediagent:latest
docker push gcr.io/YOUR_PROJECT_ID/mediagent:latest
```

---

## ☸️ Kubernetes Deployment (GKE)

### Step 1: Create GKE Cluster

Create a GKE cluster with Workload Identity enabled:

```bash
gcloud container clusters create mediagent-cluster \
  --region us-central1 \
  --num-nodes 2 \
  --machine-type e2-standard-2 \
  --workload-pool=YOUR_PROJECT_ID.svc.id.goog
```

**Note:** This may take 5-10 minutes to complete.

### Step 2: Set Up Service Account & Permissions

#### 1. Create GCP Service Account

```bash
gcloud iam service-accounts create mediagent
```

#### 2. Grant Vertex AI Permissions

```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:mediagent@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

#### 3. Bind Workload Identity

```bash
gcloud iam service-accounts add-iam-policy-binding \
  mediagent@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:YOUR_PROJECT_ID.svc.id.goog[default/mediagent-sa]"
```

### Step 3: Configure kubectl

Connect kubectl to your GKE cluster:

```bash
gcloud container clusters get-credentials mediagent-cluster --region us-central1
```

### Step 4: Update Kubernetes Manifests

Update `k8s/deployment.yaml` with your project ID:
- Line 20: Replace `YOUR_PROJECT_ID` in image path
- Line 26: Replace `your-project-id` with actual project ID
- Line 66: Replace `YOUR_PROJECT_ID` in service account annotation

### Step 5: Deploy Application

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### Step 6: Get External IP

Wait for LoadBalancer to provision (may take 2-3 minutes):

```bash
kubectl get service mediagent-service
```

Look for the `EXTERNAL-IP` column. Once it shows an IP address (not `<pending>`), your application is accessible at `http://EXTERNAL-IP:8000`.

### Verify Deployment

```bash
# Check pod status
kubectl get pods

# View logs
kubectl logs -f deployment/mediagent

# Test health endpoint
curl http://EXTERNAL-IP:8000/health
```

---

## 🧪 Development

### Run Tests (Future)

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black .

# Type checking
mypy .

# Linting
flake8 .
```

---

## 🔧 Configuration Reference

See `.env.example` for all configurable parameters:

| Variable | Description | Default |
|----------|-------------|---------|
| `GCP_PROJECT_ID` | Google Cloud project ID | (required) |
| `VERTEX_MODEL` | Gemini model name | `gemini-1.5-pro` |
| `GROUNDING_THRESHOLD` | Min similarity for answers | `0.7` |
| `CONFIDENCE_THRESHOLD` | Min confidence for answers | `0.6` |
| `CHUNK_SIZE` | Characters per chunk | `512` |
| `CHUNK_OVERLAP` | Overlap between chunks | `64` |
| `TOP_K_RETRIEVAL` | Number of chunks to retrieve | `5` |
| `MCP_SERVER_PORT` | MCP tool server port | `50051` |

---

## 🎯 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload` | POST | Upload PDF, extract, chunk, embed, index |
| `/query` | POST | Run agentic Q&A with citations |
| `/audit/{request_id}` | GET | Retrieve audit trail for a request |
| `/eval` | POST | Run evaluation pipeline |
| `/health` | GET | Health check for monitoring |

Full API docs (Swagger): `http://localhost:8000/docs`

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. **ImagePullBackOff** on GKE

**Problem**: Pods fail to pull Docker image from Artifact Registry.

**Solution**:
```bash
# Grant Artifact Registry read permissions to compute service account
gcloud artifacts repositories add-iam-policy-binding gcr.io \
  --location=us \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/artifactregistry.reader"

# Restart deployment
kubectl rollout restart deployment/mediagent
```

#### 2. **Quota Exceeded** - SSD Storage

**Problem**: `Insufficient regional quota to satisfy request: resource "SSD_TOTAL_GB"`

**Solution**:
```bash
# Use standard persistent disks instead of SSD
gcloud container clusters create mediagent-cluster \
  --region us-central1 \
  --num-nodes 2 \
  --machine-type e2-standard-2 \
  --disk-type=pd-standard \
  --scopes="https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/cloud-platform"
```

#### 3. **403 Forbidden** - API Not Enabled

**Problem**: `API [container.googleapis.com] not enabled on project`

**Solution**:
```bash
# Enable required APIs
gcloud services enable container.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

#### 4. **Module Not Found** in Docker Container

**Problem**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**: Ensure Dockerfile uses a virtual environment accessible to the non-root user. See the updated `Dockerfile` in this repo.

#### 5. **PowerShell Line Continuation Errors**

**Problem**: `unrecognized arguments: \` when running gcloud commands

**Solution**: Use backticks (`` ` ``) for line continuation in PowerShell, or run as a single line:
```powershell
# Single line (recommended for PowerShell)
gcloud container clusters create mediagent-cluster --region us-central1 --num-nodes 2 --machine-type e2-standard-2
```

### Getting Help

- Check logs: `kubectl logs -f deployment/mediagent`
- Describe pod: `kubectl describe pod POD_NAME`
- View events: `kubectl get events --sort-by='.lastTimestamp'`

---

## 💰 Cost Estimation

### Google Cloud Platform Costs

#### Development/Testing (Local Docker)
- **Cost**: $0/hour (runs locally)
- **Vertex AI API calls**: ~$0.01-0.05 per test session
- **Recommended for**: Initial development and testing

#### Production Deployment (GKE)

**Hourly Costs:**
| Resource | Specification | Cost/Hour | Cost/Day |
|----------|--------------|-----------|----------|
| GKE Cluster Management | - | $0.10 | $2.40 |
| Compute Nodes (6 nodes) | e2-standard-2 (2 vCPU, 8GB) | $0.42 | $10.08 |
| LoadBalancer | External IP | $0.025 | $0.60 |
| **Total** | | **~$0.55/hour** | **~$13/day** |

**Monthly Estimate**: ~$390/month (24/7 operation)

**Additional Costs:**
- **Vertex AI Embeddings**: ~$0.025 per 1,000 characters
- **Gemini API**: ~$0.00025 per 1,000 characters (input)
- **Artifact Registry Storage**: ~$0.10/GB/month
- **Egress**: ~$0.12/GB (after free tier)

### Cost Optimization Tips

1. **Use Autopilot GKE** (pay only for pods, not nodes)
2. **Scale down during off-hours**:
   ```bash
   kubectl scale deployment mediagent --replicas=0
   ```
3. **Use preemptible nodes** (up to 80% savings)
4. **Set budget alerts** in GCP Console
5. **Delete resources when not in use**:
   ```bash
   gcloud container clusters delete mediagent-cluster --region us-central1
   ```

### Free Tier Considerations

- **Vertex AI**: $300 free credit for new GCP accounts
- **GKE**: $74.40/month free cluster management credit
- **Artifact Registry**: 0.5 GB free storage

**Estimated cost for a 30-minute demo**: ~$0.30-0.50

---

## 🚧 Future Improvements

### RAG Enhancements
- [ ] Hybrid search (dense + sparse vectors with BM25)
- [ ] Reranking with cross-encoder model
- [ ] Query expansion using Gemini
- [ ] Multi-document synthesis

### Agent Capabilities
- [ ] Multi-turn conversation memory
- [ ] Dynamic plan adjustment based on partial results
- [ ] Tool composition (chain multiple tools)
- [ ] Human-in-the-loop for high-risk queries

### Safety & Compliance
- [ ] Fine-tuned PHI detector model
- [ ] Adversarial prompt testing framework
- [ ] HIPAA compliance audit logging
- [ ] Encryption at rest and in transit

### Evaluation
- [ ] Human evaluation UI
- [ ] A/B testing framework
- [ ] Continuous monitoring dashboard
- [ ] Automated regression testing

### Production Infrastructure
- [ ] PostgreSQL for persistent audit logs
- [ ] Redis for session state management
- [ ] Cloud Pub/Sub for async document processing
- [ ] Cloud Storage for PDF persistence
- [ ] Cloud Logging and Trace integration
- [ ] Prometheus metrics export

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**MIT License Summary:**
- ✅ Commercial use allowed
- ✅ Modification allowed
- ✅ Distribution allowed
- ✅ Private use allowed
- ⚠️ Liability and warranty disclaimer

---

## 🤝 Contributing

This is an MVP scaffold. Contributions welcome:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📧 Contact

For questions or issues, please open a GitHub issue.

---

## 🙏 Acknowledgments

- **Google Vertex AI** for embeddings and Gemini LLM
- **FAISS** by Meta AI for vector search
- **FastAPI** for web framework
- **Structlog** for structured logging

---

Built with ❤️ for regulated healthcare applications

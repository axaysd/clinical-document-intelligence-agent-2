# Testing Guide for Clinical Document Intelligence Agent

## 📋 Prerequisites

Before running the system, ensure you have:
- ✅ Python 3.11+ installed
- ✅ Google Cloud Project with Vertex AI API enabled
- ✅ GCP authentication set up

---

## 🔧 Step 1: Configure Environment

You have the `.env` file open. **Update the following line**:

```env
GCP_PROJECT_ID=your-actual-gcp-project-id
```

Replace `your-actual-gcp-project-id` with your real GCP project ID.

**All other settings can remain as defaults for testing.**

---

## 🔐 Step 2: Authenticate with Google Cloud

Open a terminal and run:

```bash
# Authenticate with GCP
gcloud auth application-default login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Verify Vertex AI is enabled
gcloud services enable aiplatform.googleapis.com
```

---

## 📦 Step 3: Install Dependencies

```bash
cd C:\Users\axays\Downloads\MediAgent

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

---

## 🚀 Step 4: Start the MCP Server

Open **Terminal 1**:

```bash
cd C:\Users\axays\Downloads\MediAgent
venv\Scripts\activate
python -m mcp.server
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://localhost:50051
```

**Keep this terminal open!**

---

## 🌐 Step 5: Start the FastAPI Application

Open **Terminal 2**:

```bash
cd C:\Users\axays\Downloads\MediAgent
venv\Scripts\activate
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## ✅ Step 6: Test the Health Endpoint

Open **Terminal 3** or use your browser:

```bash
# Using curl
curl http://localhost:8000/health

# Or open in browser
http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-01-12T10:50:00Z",
  "components": {
    "faiss_index": "0 chunks",
    "agent": "ready",
    "mcp_tools": "available"
  }
}
```

---

## 📄 Step 7: Test Document Upload

**Create a sample PDF** or use an existing one. For testing, create a simple text file and convert to PDF, or download any medical/clinical PDF.

```bash
# Upload a PDF
curl -X POST "http://localhost:8000/upload" \
  -F "file=@path\to\your\document.pdf"
```

Replace `path\to\your\document.pdf` with actual path.

**PowerShell alternative**:
```powershell
$file = Get-Item "C:\path\to\document.pdf"
$form = @{
    file = $file
}
Invoke-WebRequest -Uri "http://localhost:8000/upload" -Method POST -Form $form
```

Expected response:
```json
{
  "document_id": "doc_a1b2c3d4e5f6",
  "filename": "document.pdf",
  "num_chunks": 25,
  "status": "success",
  "message": "Document processed successfully with 25 chunks"
}
```

---

## 💬 Step 8: Test Query Endpoint

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"What is the main topic of the document?\", \"top_k\": 5}"
```

**PowerShell alternative**:
```powershell
$body = @{
    question = "What is the main topic of the document?"
    top_k = 5
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/query" -Method POST -Body $body -ContentType "application/json"
```

Expected response:
```json
{
  "request_id": "req_xyz789abc012",
  "answer": "Based on the document, the main topic is...",
  "citations": [
    {
      "chunk_id": "doc_a1b2_chunk_0001",
      "document_id": "doc_a1b2c3d4e5f6",
      "similarity_score": 0.89,
      "snippet": "The document discusses...",
      "page_number": 1
    }
  ],
  "confidence_score": 0.85,
  "grounding_score": 0.89,
  "tool_calls": [],
  "safety_flags": [],
  "timestamp": "2026-01-12T10:55:00Z"
}
```

---

## 🔍 Step 9: Test Audit Trail

Using the `request_id` from previous query:

```bash
curl http://localhost:8000/audit/req_xyz789abc012
```

---

## 🧮 Step 10: Test MCP Tools

### Test Calculator Tool

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"Calculate 25 plus 17\"}"
```

The agent should detect the calculation need and call the MCP calculator tool.

Expected response includes:
```json
{
  "answer": "25 plus 17 equals 42",
  "tool_calls": [
    {
      "tool_name": "calculator",
      "arguments": {"operation": "add", "a": 25, "b": 17},
      "result": {"result": 42, "error": null}
    }
  ]
}
```

### Test PHI Detector Tool

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"Check for PHI in the document\"}"
```

---

## 📊 Step 11: Test Evaluation Pipeline

```bash
curl -X POST "http://localhost:8000/eval" \
  -H "Content-Type: application/json" \
  -d "{\"generate_new\": true, \"num_samples\": 10}"
```

This will:
1. Generate 10 synthetic Q/A pairs from uploaded documents
2. Run evaluation on them
3. Calculate metrics

Expected response:
```json
{
  "status": "success",
  "metrics": {
    "dataset_version": "2026-01-12_10-55-00",
    "total_samples": 10,
    "groundedness_avg": 0.92,
    "correctness_avg": 0.85,
    "latency_p50_ms": 1200,
    "latency_p95_ms": 2800,
    "latency_p99_ms": 3500,
    "refusal_rate": 0.0
  },
  "output_path": "data/eval_datasets/results/eval_results_2026-01-12_10-55-00.json"
}
```

---

## 🌐 Step 12: Use Swagger UI

Open your browser and go to:
```
http://localhost:8000/docs
```

This provides an **interactive API documentation** where you can:
- See all endpoints
- Test them directly in the browser
- View request/response schemas

---

## 🐛 Troubleshooting

### Issue: "Module not found"
**Solution**: Make sure virtual environment is activated and dependencies installed:
```bash
venv\Scripts\activate
pip install -r requirements.txt
```

### Issue: "Vertex AI authentication error"
**Solution**: Run authentication again:
```bash
gcloud auth application-default login
```

### Issue: "MCP server connection refused"
**Solution**: Make sure MCP server is running on port 50051 (Terminal 1)

### Issue: "No chunks in index"
**Solution**: Upload a PDF first using `/upload` endpoint

### Issue: "Connection timeout to Vertex AI"
**Solution**: 
1. Check your GCP project ID in `.env`
2. Verify Vertex AI API is enabled
3. Check internet connection

---

## 📝 Sample Test Workflow

Here's a complete test workflow:

```bash
# 1. Check health
curl http://localhost:8000/health

# 2. Upload a document
curl -X POST "http://localhost:8000/upload" -F "file=@sample.pdf"

# 3. Ask a question
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"Summarize the key findings\"}"

# 4. Check audit trail (use request_id from step 3)
curl http://localhost:8000/audit/req_xxxxx

# 5. Test calculator
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"What is 100 divided by 4?\"}"

# 6. Run evaluation
curl -X POST "http://localhost:8000/eval" \
  -H "Content-Type: application/json" \
  -d "{\"generate_new\": true, \"num_samples\": 5}"
```

---

## 📊 Expected Directory Structure After Testing

```
MediAgent/
├── data/
│   ├── uploads/              # Uploaded PDFs
│   │   └── doc_xxxxx.pdf
│   ├── faiss_index/          # Vector index
│   │   ├── faiss.index
│   │   └── metadata.pkl
│   └── eval_datasets/        # Evaluation data
│       ├── 2026-01-12_10-55-00/
│       │   └── dataset.json
│       └── results/
│           └── eval_results_2026-01-12_10-55-00.json
```

---

## 🎯 Next Steps After Successful Testing

1. **Try different types of questions**:
   - Factual queries
   - Summarization requests
   - Questions requiring calculations
   - Questions about PHI

2. **Test safety features**:
   - Try prompt injection attempts
   - Ask questions without uploaded documents
   - Query topics not in documents

3. **Run comprehensive evaluation**:
   - Generate 50 samples
   - Review metrics
   - Analyze refusal cases

4. **Prepare for deployment**:
   - Build Docker image
   - Test containerized version
   - Deploy to GKE

---

## 🚀 Quick Start Commands (TL;DR)

```bash
# Terminal 1: MCP Server
cd C:\Users\axays\Downloads\MediAgent
venv\Scripts\activate
python -m mcp.server

# Terminal 2: FastAPI
cd C:\Users\axays\Downloads\MediAgent
venv\Scripts\activate
python main.py

# Terminal 3: Test
curl http://localhost:8000/health
curl http://localhost:8000/docs  # Open in browser
```

---

**Note**: The first query might take longer as Vertex AI initializes. Subsequent queries will be faster.

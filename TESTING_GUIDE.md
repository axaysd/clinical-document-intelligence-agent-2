# 🧪 MediAgent Testing Guide

## Overview
Your MediAgent application is now running successfully on `http://localhost:8000`. This guide will help you test all available functionalities.

## 📋 Available Endpoints

### 1. **Health Check** ✅
**Endpoint:** `GET /health`

**Purpose:** Verify the API is running and check component status

**Test Command:**
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-01-13T15:11:00.000Z",
  "components": {
    "faiss_index": "18 chunks",
    "adk_agent": "ready",
    "tools": "3 tools available"
  }
}
```

---

### 2. **Upload Document** 📄
**Endpoint:** `POST /upload`

**Purpose:** Upload and index PDF clinical documents

**What it does:**
- Extracts text from PDF using PyPDF2
- Chunks text (512 chars with 50 char overlap)
- Generates embeddings using `text-embedding-004`
- Stores in FAISS vector index

**Test Command:**
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@/path/to/your/document.pdf"
```

**PowerShell Version:**
```powershell
$filePath = "C:\path\to\your\document.pdf"
$uri = "http://localhost:8000/upload"
$fileContent = [System.IO.File]::ReadAllBytes($filePath)
$boundary = [System.Guid]::NewGuid().ToString()
$LF = "`r`n"

$bodyLines = (
    "--$boundary",
    "Content-Disposition: form-data; name=`"file`"; filename=`"$(Split-Path $filePath -Leaf)`"",
    "Content-Type: application/pdf$LF",
    [System.Text.Encoding]::GetEncoding("iso-8859-1").GetString($fileContent),
    "--$boundary--$LF"
) -join $LF

Invoke-RestMethod -Uri $uri -Method Post -ContentType "multipart/form-data; boundary=$boundary" -Body $bodyLines
```

**Expected Response:**
```json
{
  "document_id": "doc_abc123",
  "filename": "clinical_report.pdf",
  "num_chunks": 45,
  "status": "success",
  "message": "Document processed successfully with 45 chunks"
}
```

---

### 3. **Query Documents** 🔍
**Endpoint:** `POST /query`

**Purpose:** Ask questions about uploaded documents using agentic RAG

**What it does:**
- Uses ADK (Agent Development Kit) with Gemini 1.5 Pro
- Retrieves relevant chunks via semantic search
- Can invoke tools:
  - **RAG Tool**: Retrieves relevant document chunks
  - **Calculator Tool**: Performs mathematical calculations
  - **PHI Detector**: Detects Protected Health Information
- Generates grounded answers with citations
- Maintains conversation history via session

**Test Command:**
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the patient'\''s vital signs?",
    "session_id": "test-session-001"
  }'
```

**PowerShell Version:**
```powershell
$body = @{
    question = "What are the patient's vital signs?"
    session_id = "test-session-001"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/query" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

**Expected Response:**
```json
{
  "request_id": "req_xyz789",
  "answer": "Based on the clinical document, the patient's vital signs are...",
  "citations": [
    {
      "chunk_id": "chunk_001",
      "document_id": "doc_abc123",
      "text": "Vital signs: BP 120/80, HR 72...",
      "page": 1,
      "score": 0.92
    }
  ],
  "confidence_score": 0.85,
  "grounding_score": 0.92,
  "tool_calls": [
    {
      "tool_name": "retrieve_documents",
      "arguments": {"query": "vital signs"},
      "result": "Retrieved 3 relevant chunks"
    }
  ],
  "safety_flags": [],
  "timestamp": "2026-01-13T15:20:00.000Z"
}
```

**Sample Questions to Test:**
```json
// Basic retrieval
{"question": "What is this document about?", "session_id": "test-001"}

// Medical information
{"question": "What medications are mentioned?", "session_id": "test-002"}

// Calculator tool
{"question": "Calculate the BMI if weight is 70kg and height is 1.75m", "session_id": "test-003"}

// Multi-turn conversation
{"question": "What is the patient's diagnosis?", "session_id": "conv-001"}
{"question": "What treatment was recommended?", "session_id": "conv-001"}

// PHI detection
{"question": "Extract all patient identifiers", "session_id": "test-004"}
```

---

### 4. **Audit Trail** 📊
**Endpoint:** `GET /audit/{request_id}`

**Purpose:** Retrieve audit information for a specific query

**Test Command:**
```bash
curl http://localhost:8000/audit/req_xyz789
```

**Expected Response:**
```json
{
  "request_id": "req_xyz789",
  "query": "What are the patient's vital signs?",
  "retrieved_chunks": [],
  "tool_calls": [],
  "safety_validation": null,
  "audit_events": [],
  "total_duration_ms": 0,
  "timestamp": "2026-01-13T15:20:00.000Z"
}
```

**Note:** Some audit fields are TODO and will be enhanced with ADK session history.

---

## 🌐 Interactive Testing (Recommended!)

### **Swagger UI** (Best Option)
Open in your browser: **http://localhost:8000/docs**

Features:
- ✅ Interactive "Try it out" buttons for each endpoint
- ✅ Automatic request/response validation
- ✅ Schema documentation
- ✅ No need to write curl commands
- ✅ File upload interface for PDFs

### **ReDoc** (Alternative Documentation)
Open in your browser: **http://localhost:8000/redoc**

Features:
- Clean, readable documentation
- Better for understanding schemas
- Not interactive (read-only)

---

## 🔬 Testing Scenarios

### Scenario 1: Basic Document Upload & Query
```bash
# 1. Upload a document
curl -X POST "http://localhost:8000/upload" \
  -F "file=@clinical_report.pdf"

# 2. Query the document
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "Summarize the key findings", "session_id": "test-001"}'
```

### Scenario 2: Multi-Turn Conversation
```bash
# First question
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the patient diagnosis?", "session_id": "conversation-123"}'

# Follow-up question (same session)
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What treatment was prescribed?", "session_id": "conversation-123"}'
```

### Scenario 3: Tool Usage Testing
```bash
# Test calculator tool
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "Calculate 150 multiplied by 2.5", "session_id": "calc-test"}'

# Test RAG retrieval
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "Find all mentions of blood pressure", "session_id": "rag-test"}'
```

---

## 🐍 Python Test Script

A test script has been created at `test_api.py`. Run it with:

```bash
python test_api.py
```

To test with a specific PDF:
```python
from test_api import run_full_test
run_full_test("path/to/your/clinical_document.pdf")
```

---

## 📊 Current System Status

Based on your running container:
- ✅ **FAISS Index**: 18 chunks loaded
- ✅ **Embedding Model**: text-embedding-004
- ✅ **LLM Model**: gemini-1.5-pro
- ✅ **Tools Available**: 3 (RAG, Calculator, PHI Detector)
- ✅ **Documents Uploaded**: 5 PDFs in `data/uploads/`

---

## 🔍 Monitoring & Debugging

### View Application Logs
Your Docker container is already showing logs. Watch for:
- `query_requested` - When a query is received
- `query_completed` - When a query finishes
- `upload_requested` - When a document is uploaded
- `document_indexed` - When indexing completes

### Check Index Stats
```bash
curl http://localhost:8000/health | jq '.components.faiss_index'
```

### Test Health Continuously
```bash
# Check every 5 seconds
while true; do curl -s http://localhost:8000/health | jq '.status'; sleep 5; done
```

---

## 🎯 Key Features to Test

1. **Document Upload & Indexing**
   - Upload various PDF sizes
   - Check chunking quality
   - Verify embedding generation

2. **Semantic Search**
   - Test different query types
   - Check citation quality
   - Verify grounding scores

3. **Agent Tools**
   - Calculator for medical calculations
   - RAG for document retrieval
   - PHI detection for privacy

4. **Conversation Memory**
   - Multi-turn conversations
   - Context retention
   - Session management

5. **Safety & Validation**
   - Input validation
   - Output grounding
   - Medical disclaimers

---

## 🚨 Common Issues

### Issue: "No answer generated"
**Cause:** No documents in index or query doesn't match content
**Solution:** Upload documents first, try broader queries

### Issue: Upload fails
**Cause:** File not PDF or too large
**Solution:** Ensure file is PDF, check file size limits

### Issue: Low grounding score
**Cause:** Answer not well-supported by documents
**Solution:** Upload more relevant documents, refine query

---

## 📚 Next Steps

1. **Open Swagger UI**: http://localhost:8000/docs
2. **Upload a test PDF** using the `/upload` endpoint
3. **Ask questions** using the `/query` endpoint
4. **Review citations** to see how answers are grounded
5. **Test multi-turn conversations** with the same session_id

---

## 💡 Pro Tips

- Use **Swagger UI** for easiest testing experience
- Keep the same `session_id` for multi-turn conversations
- Check `grounding_score` to assess answer quality
- Review `citations` to understand answer sources
- Monitor Docker logs for detailed execution traces

---

**Happy Testing! 🎉**

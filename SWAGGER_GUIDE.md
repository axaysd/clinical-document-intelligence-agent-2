# How to Use Swagger UI - Step-by-Step Guide

![Swagger UI Interface](file:///C:/Users/axays/.gemini/antigravity/brain/f7688ab5-9e31-48ff-9e82-338534ae4bf4/swagger_ui_endpoints_1768220740980.png)

## 🌐 You Now Have Swagger UI Open!

URL: **http://localhost:8000/docs**

You should see 5 endpoints listed:
- ✅ **POST /upload** - Upload Document
- ✅ **POST /query** - Query Documents  
- ✅ **GET /audit/{request_id}** - Get Audit Trail
- ✅ **POST /eval** - Run Evaluation
- ✅ **GET /health** - Health Check

---

## 📖 How to Use Each Endpoint

### 1️⃣ Test Health Check (Easiest to Start)

1. **Find** the `GET /health` endpoint (green box)
2. **Click** on it to expand
3. **Click** the "Try it out" button (top right of the section)
4. **Click** the blue "Execute" button
5. **See** the response below showing system status

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "faiss_index": "0 chunks",
    "agent": "ready"
  }
}
```

---

### 2️⃣ Upload a PDF Document

1. **Find** `POST /upload` (orange box at top)
2. **Click** on it to expand
3. **Click** "Try it out"
4. **Click** "Choose File" button
5. **Select** a PDF from your computer
6. **Click** "Execute"
7. **Wait** for processing (may take 30-60 seconds)

**What Happens:**
- Extracts text from PDF
- Chunks it into pieces
- Generates embeddings
- Stores in FAISS index

**Expected Response:**
```json
{
  "document_id": "doc_a1b2c3d4",
  "filename": "your_document.pdf",
  "num_chunks": 25,
  "status": "success",
  "message": "Document processed successfully with 25 chunks"
}
```

---

### 3️⃣ Ask Questions About Your Document

1. **Find** `POST /query` (orange box)
2. **Click** on it to expand
3. **Click** "Try it out"
4. **Edit** the JSON in the Request body:

```json
{
  "question": "What is the main topic of this document?",
  "session_id": "test-session",
  "top_k": 5
}
```

5. **Click** "Execute"
6. **See** the answer with citations!

**Expected Response:**
```json
{
  "request_id": "req_xyz789abc",
  "answer": "Based on [1] and [2], the document discusses...",
  "citations": [
    {
      "chunk_id": "doc_a1b2_chunk_0001",
      "similarity_score": 0.89,
      "snippet": "The document covers clinical trials..."
    }
  ],
  "confidence_score": 0.85,
  "grounding_score": 0.89,
  "tool_calls": [],
  "safety_flags": []
}
```

---

### 4️⃣ Test Calculator Tool (via Query)

Query with math:

```json
{
  "question": "Calculate 100 divided by 4",
  "top_k": 3
}
```

The agent will:
- Detect the calculation need
- Call the MCP calculator tool
- Return: "100 divided by 4 equals 25"

**Response will include:**
```json
{
  "tool_calls": [
    {
      "tool_name": "calculator",
      "arguments": {"operation": "divide", "a": 100, "b": 4},
      "result": {"result": 25, "error": null}
    }
  ]
}
```

---

### 5️⃣ Check Audit Trail

1. **Find** `GET /audit/{request_id}` (blue box)
2. **Click** on it to expand
3. **Click** "Try it out"
4. **Paste** a request_id from a previous query
5. **Click** "Execute"

**See:**
- Retrieved chunks with scores
- Tool calls made
- Safety validation details
- Timestamps and duration
- Full audit events

---

### 6️⃣ Run Evaluation Pipeline

1. **Find** `POST /eval` (orange box)
2. **Click** on it to expand
3. **Click** "Try it out"
4. **Edit** the request:

```json
{
  "dataset_path": null,
  "generate_new": true,
  "num_samples": 10
}
```

5. **Click** "Execute"
6. **Wait** (may take 2-3 minutes for 10 samples)

**What it Does:**
- Generates 10 Q/A pairs from your uploaded documents
- Runs evaluation on them
- Calculates metrics (groundedness, correctness, latency)

**Expected Response:**
```json
{
  "status": "success",
  "metrics": {
    "groundedness_avg": 0.92,
    "correctness_avg": 0.85,
    "latency_p50_ms": 1200,
    "refusal_rate": 0.0
  }
}
```

---

## 💡 Pro Tips

### Swagger UI Features:

1. **Schemas** - Click "Schemas" at bottom to see all data models
2. **Responses** - Each endpoint shows possible response codes (200, 404, 500)
3. **Copy** - Click clipboard icon to copy curl commands
4. **Test Multiple Times** - You can execute repeatedly without reloading

### Common Workflow:

```
1. Upload PDF → /upload
2. Ask question → /query  
3. Check audit → /audit/{request_id}
4. Run eval → /eval
```

---

## 🎬 Quick Demo Workflow

Try this complete workflow:

1. **Health Check**
   - Expand `GET /health`
   - Try it out → Execute
   - ✅ Should show "healthy"

2. **Upload Document**
   - Expand `POST /upload`
   - Try it out → Choose File → Select PDF → Execute
   - ✅ Get document_id

3. **Ask a Question**
   - Expand `POST /query`
   - Try it out → Edit question → Execute
   - ✅ Get answer with citations

4. **Math Question** (triggers MCP tool)
   - Use `/query` again
   - Question: "What is 25 times 8?"
   - ✅ See calculator tool in response

5. **View Audit**
   - Copy request_id from query response
   - Expand `GET /audit/{request_id}`
   - Try it out → Paste request_id → Execute
   - ✅ See full trace

---

## ⌨️ Keyboard Shortcuts in Swagger

- **Expand/Collapse** - Click endpoint title
- **Ctrl+A** - Select all in text box
- **Ctrl+C** - Copy JSON response

---

## 🔍 Understanding Responses

### Response Codes:
- **200** ✅ Success
- **400** ❌ Bad request (check your JSON)
- **404** ❌ Not found (wrong request_id)
- **500** ❌ Server error (check terminal logs)

### Look for:
- **Citations** = Where the answer came from
- **Grounding Score** = How well-supported the answer is (0-1)
- **Confidence Score** = How confident the system is (0-1)
- **Safety Flags** = Any safety issues detected
- **Tool Calls** = Which MCP tools were used

---

**Ready?** Try the health check first, then upload a PDF! 🚀

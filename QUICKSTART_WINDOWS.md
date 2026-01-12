# Quick Start Guide - Windows Installation

## ⚠️ Important Note for Windows Users

Some dependencies (numpy, faiss-cpu) require pre-built wheels on Windows. The installation encountered a compiler issue.

## 🔧 Solution: Use Pre-built Wheels

### Option 1: Install with Pre-built Wheels (Recommended)

```powershell
cd C:\Users\axays\Downloads\MediAgent

# Activate virtual environment
.\venv\Scripts\activate

# Install packages one by one to avoid conflicts
pip install numpy
pip install fastapi uvicorn[standard] python-multipart
pip install google-cloud-aiplatform vertexai google-auth
pip install pydantic pydantic-settings
pip install structlog python-dotenv requests aiofiles
pip install PyPDF2 pdfplumber
pip install pandas scikit-learn typing-extensions

# Install FAISS last (may need wheel from unofficial source)
pip install faiss-cpu
```

### Option 2: Skip FAISS for Initial Testing

If FAISS installation fails, you can test the MCP server independently first:

```powershell
# Install everything except faiss-cpu
pip install fastapi uvicorn[standard] python-multipart
pip install google-cloud-aiplatform vertexai google-auth  
pip install pydantic pydantic-settings
pip install structlog python-dotenv requests

# Test MCP server only
python -m mcp.server
```

## 🚀 Quick Test (MCP Server Only)

### 1. Edit .env File

Open `.env` and update:
```
GCP_PROJECT_ID=your-actual-project-id
```

### 2. Start MCP Server

```powershell
cd C:\Users\axays\Downloads\MediAgent
.\venv\Scripts\activate
python -m mcp.server
```

### 3. Test MCP Tools (New Terminal)

```powershell
# Test health
curl http://localhost:50051/health

# Test calculator
curl -X POST http://localhost:50051/tools/execute `
  -H "Content-Type: application/json" `
  -d '{\"tool_name\": \"calculator\", \"arguments\": {\"operation\": \"add\", \"a\": 5, \"b\": 3}}'

# Test PHI detector  
curl -X POST http://localhost:50051/tools/execute `
  -H "Content-Type: application/json" `
  -d '{\"tool_name\": \"phi_detector\", \"arguments\": {\"text\": \"Contact: john@example.com or 555-123-4567\"}}'
```

## 🔍 Alternative: Use Conda

If pip wheels fail, use Conda which has pre-built packages:

```powershell
# Install Miniconda from https://docs.conda.io/en/latest/miniconda.html

# Create environment
conda create -n mediagent python=3.11
conda activate mediagent

# Install packages via conda when available
conda install -c conda-forge numpy pandas scikit-learn
conda install -c conda-forge faiss-cpu

# Install remaining via pip
pip install fastapi uvicorn[standard]
pip install google-cloud-aiplatform vertexai
pip install pydantic pydantic-settings structlog
pip install PyPDF2 pdfplumber python-dotenv requests
```

## 📝 Next Steps After Installation

1. **Configure GCP**: Edit `.env` with your project ID
2. **Authenticate**: Run `gcloud auth application-default login`
3. **Test MCP Server**: `python -m mcp.server`
4. **Test Full API** (if FAISS installed): `python main.py`

## 🐛 Troubleshooting

### Issue: "No module named 'numpy'"
**Solution**: Install numpy separately first:
```powershell
pip install numpy
```

### Issue: "Could not build faiss-cpu"
**Solution**: Download pre-built wheel from:
- https://www.lfd.uci.edu/~gohlke/pythonlibs/#faiss
- Then: `pip install <downloaded-wheel>.whl`

Or use conda: `conda install -c conda-forge faiss-cpu`

### Issue: "MSVCP140.dll not found"
**Solution**: Install Visual C++ Redistributable:
- https://aka.ms/vs/17/release/vc_redist.x64.exe

## ✅ Minimal Test Without Full Installation

You can test the MCP tools with minimal dependencies:

```powershell
pip install fastapi uvicorn requests pydantic

# Run MCP server
python -m mcp.server

# In another terminal, test it
curl http://localhost:50051/tools  

```

This will at least verify the MCP server and tools work correctly.

## 📖Full Documentation

See `TESTING.md` for comprehensive testing guide once all dependencies are installed.

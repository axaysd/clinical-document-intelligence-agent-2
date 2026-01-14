# 🏠 Local Setup Guide for MediAgent

This guide will help you run MediAgent locally on your machine (without Docker).

## ⚠️ Prerequisites

- **Python 3.11+** installed
- **Google Cloud Project** with Vertex AI API enabled
- **GCP Project ID** (e.g., `mediagent-demo`)

---

## 📋 Step-by-Step Setup

### Step 1: Install Google Cloud CLI

If you haven't already, install the Google Cloud CLI:

**Windows:**
Download and run the installer from: https://cloud.google.com/sdk/docs/install

**Verify installation:**
```powershell
gcloud --version
```

---

### Step 2: Authenticate with Google Cloud

This is the **critical step** that fixes the authentication error you're seeing.

```powershell
# Login to your Google account
gcloud auth application-default login
```

This will:
1. Open a browser window
2. Ask you to sign in to your Google account
3. Grant permissions to access Google Cloud APIs
4. Save credentials locally at: `C:\Users\axays\AppData\Roaming\gcloud\application_default_credentials.json`

**Set your project:**
```powershell
gcloud config set project mediagent-demo
```

**Verify authentication:**
```powershell
gcloud auth application-default print-access-token
```

If this prints a long token, you're authenticated! ✅

---

### Step 3: Enable Required APIs

```powershell
# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com

# Enable Generative AI API
gcloud services enable generativelanguage.googleapis.com
```

---

### Step 4: Configure Environment Variables

Make sure your `.env` file has the correct values:

```env
GCP_PROJECT_ID=mediagent-demo
GCP_REGION=us-central1
GCP_LOCATION=us-central1

VERTEX_MODEL=gemini-1.5-pro
VERTEX_EMBEDDING_MODEL=text-embedding-004
```

---

### Step 5: Install Python Dependencies

```powershell
# Navigate to project directory
cd C:\Users\axays\Downloads\MediAgent

# Activate virtual environment (if not already active)
.\venv\Scripts\Activate

# Install dependencies
pip install -r requirements.txt
```

---

### Step 6: Run the Application

**Option A: Using Python directly**
```powershell
python main.py
```

**Option B: Using Uvicorn (recommended for development)**
```powershell
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The `--reload` flag will auto-reload when you make code changes.

---

## 🧪 Test the Application

Once running, test with:

1. **Health Check:**
   ```
   http://localhost:8000/health
   ```

2. **Interactive API Docs:**
   ```
   http://localhost:8000/docs
   ```

3. **Upload a PDF:**
   - Go to http://localhost:8000/docs
   - Click on `POST /upload`
   - Click "Try it out"
   - Choose a PDF file
   - Click "Execute"

---

## 🔧 Troubleshooting

### Error: "Unable to authenticate your request"

**Cause:** Google Cloud credentials not set up

**Solution:**
```powershell
gcloud auth application-default login
gcloud config set project mediagent-demo
```

---

### Error: "Permission denied" or "403 Forbidden"

**Cause:** Your Google account doesn't have permissions to use Vertex AI

**Solution:**
1. Go to https://console.cloud.google.com/iam-admin/iam
2. Find your user account
3. Add role: **Vertex AI User** (`roles/aiplatform.user`)

Or via command line:
```powershell
gcloud projects add-iam-policy-binding mediagent-demo `
  --member="user:YOUR_EMAIL@gmail.com" `
  --role="roles/aiplatform.user"
```

---

### Error: "API not enabled"

**Cause:** Vertex AI API not enabled for your project

**Solution:**
```powershell
gcloud services enable aiplatform.googleapis.com
```

Or enable manually:
1. Go to https://console.cloud.google.com/apis/library/aiplatform.googleapis.com
2. Click "Enable"

---

### Error: "Module not found"

**Cause:** Dependencies not installed

**Solution:**
```powershell
pip install -r requirements.txt
```

---

### Port 8000 already in use

**Cause:** Docker container or another process using port 8000

**Solution:**

**Stop Docker container:**
```powershell
docker ps
docker stop <container_id>
```

**Or use a different port:**
```powershell
uvicorn main:app --host 0.0.0.0 --port 8001
```

---

## 🚀 Quick Start Commands (All-in-One)

```powershell
# 1. Authenticate
gcloud auth application-default login
gcloud config set project mediagent-demo

# 2. Enable APIs
gcloud services enable aiplatform.googleapis.com

# 3. Navigate to project
cd C:\Users\axays\Downloads\MediAgent

# 4. Activate virtual environment
.\venv\Scripts\Activate

# 5. Install dependencies (if needed)
pip install -r requirements.txt

# 6. Run application
python main.py
```

Then open: **http://localhost:8000/docs**

---

## 📊 Verify Everything is Working

### 1. Check Authentication
```powershell
gcloud auth application-default print-access-token
```
Should print a long token.

### 2. Check Project
```powershell
gcloud config get-value project
```
Should print: `mediagent-demo`

### 3. Check APIs
```powershell
gcloud services list --enabled | Select-String "aiplatform"
```
Should show: `aiplatform.googleapis.com`

### 4. Check Application
```powershell
curl http://localhost:8000/health
```
Should return:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  ...
}
```

---

## 🎯 Common Workflow

### Daily Development

```powershell
# 1. Navigate to project
cd C:\Users\axays\Downloads\MediAgent

# 2. Activate venv
.\venv\Scripts\Activate

# 3. Run with auto-reload
uvicorn main:app --reload

# 4. Open browser
start http://localhost:8000/docs
```

### Upload and Query Documents

1. **Upload PDF:**
   - Go to http://localhost:8000/docs
   - Use `POST /upload` endpoint
   - Upload your clinical PDF

2. **Query:**
   - Use `POST /query` endpoint
   - Enter question: "What is this document about?"
   - Get AI-powered answer with citations

---

## 🔐 Security Notes

- **Credentials Location:** `C:\Users\axays\AppData\Roaming\gcloud\application_default_credentials.json`
- **Never commit** this file to Git
- **Never share** your credentials
- **Rotate credentials** periodically

---

## 💡 Pro Tips

1. **Use `--reload` during development:**
   ```powershell
   uvicorn main:app --reload
   ```
   Auto-reloads on code changes.

2. **Check logs in real-time:**
   The application logs are printed to console with structured JSON.

3. **Use Swagger UI for testing:**
   http://localhost:8000/docs is much easier than curl commands.

4. **Keep Docker container for production testing:**
   Docker simulates the production environment more closely.

---

## 📚 Next Steps

After setup:
1. ✅ Upload a test PDF document
2. ✅ Query the document
3. ✅ Check citations and grounding scores
4. ✅ Review the `TESTING_GUIDE.md` for more test scenarios

---

## 🆘 Still Having Issues?

1. **Check Python version:**
   ```powershell
   python --version
   ```
   Should be 3.11 or higher.

2. **Check virtual environment:**
   ```powershell
   where python
   ```
   Should point to: `C:\Users\axays\Downloads\MediAgent\venv\Scripts\python.exe`

3. **Reinstall dependencies:**
   ```powershell
   pip install --upgrade -r requirements.txt
   ```

4. **Check GCP quota:**
   - Go to https://console.cloud.google.com/iam-admin/quotas
   - Search for "Vertex AI"
   - Ensure you have quota available

---

**Happy Coding! 🎉**

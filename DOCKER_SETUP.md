# 🐳 Docker Setup with Google Cloud Authentication

## Problem
When running MediAgent in Docker, the container can't access your local Google Cloud credentials, causing authentication errors.

## Solution: Mount Credentials into Container

### Step 1: Authenticate Locally First

```powershell
# Login and create application default credentials
gcloud auth application-default login

# Set your project
gcloud config set project mediagent-demo
```

This creates credentials at:
```
C:\Users\axays\AppData\Roaming\gcloud\application_default_credentials.json
```

### Step 2: Run Docker with Mounted Credentials

**Windows PowerShell:**
```powershell
docker run -p 8000:8000 `
  -e GCP_PROJECT_ID=mediagent-demo `
  -e GCP_REGION=us-central1 `
  -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/keys/application_default_credentials.json `
  -v "$env:APPDATA\gcloud:/tmp/keys:ro" `
  gcr.io/mediagent-demo/mediagent:latest
```

**Explanation:**
- `-e GOOGLE_APPLICATION_CREDENTIALS=/tmp/keys/application_default_credentials.json` - Tells the app where to find credentials
- `-v "$env:APPDATA\gcloud:/tmp/keys:ro"` - Mounts your local credentials into the container (read-only)

### Step 3: Verify It Works

1. Container should start without authentication errors
2. Go to http://localhost:8000/docs
3. Try uploading a PDF - should work now! ✅

---

## Alternative: Use Service Account (Production Method)

### Step 1: Create Service Account

```powershell
# Create service account
gcloud iam service-accounts create mediagent-local `
  --display-name="MediAgent Local Development"

# Grant Vertex AI permissions
gcloud projects add-iam-policy-binding mediagent-demo `
  --member="serviceAccount:mediagent-local@mediagent-demo.iam.gserviceaccount.com" `
  --role="roles/aiplatform.user"

# Create and download key
gcloud iam service-accounts keys create mediagent-key.json `
  --iam-account=mediagent-local@mediagent-demo.iam.gserviceaccount.com
```

This creates `mediagent-key.json` in your current directory.

### Step 2: Run Docker with Service Account Key

```powershell
docker run -p 8000:8000 `
  -e GCP_PROJECT_ID=mediagent-demo `
  -e GCP_REGION=us-central1 `
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/keys/mediagent-key.json `
  -v "${PWD}/mediagent-key.json:/app/keys/mediagent-key.json:ro" `
  gcr.io/mediagent-demo/mediagent:latest
```

---

## Quick Reference

### Option 1: User Credentials (Development)
```powershell
# One-time setup
gcloud auth application-default login

# Run container
docker run -p 8000:8000 `
  -e GCP_PROJECT_ID=mediagent-demo `
  -e GCP_REGION=us-central1 `
  -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/keys/application_default_credentials.json `
  -v "$env:APPDATA\gcloud:/tmp/keys:ro" `
  gcr.io/mediagent-demo/mediagent:latest
```

### Option 2: Service Account (Production-like)
```powershell
# One-time setup
gcloud iam service-accounts keys create mediagent-key.json `
  --iam-account=mediagent-local@mediagent-demo.iam.gserviceaccount.com

# Run container
docker run -p 8000:8000 `
  -e GCP_PROJECT_ID=mediagent-demo `
  -e GCP_REGION=us-central1 `
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/keys/mediagent-key.json `
  -v "${PWD}/mediagent-key.json:/app/keys/mediagent-key.json:ro" `
  gcr.io/mediagent-demo/mediagent:latest
```

---

## Troubleshooting

### Error: "Unable to authenticate your request"
**Cause:** Credentials not mounted or path incorrect

**Check:**
1. Verify credentials exist:
   ```powershell
   Test-Path "$env:APPDATA\gcloud\application_default_credentials.json"
   ```
   Should return `True`

2. Check environment variable in container:
   ```powershell
   docker exec <container_id> env | Select-String GOOGLE
   ```

### Error: "Permission denied"
**Cause:** Service account doesn't have Vertex AI permissions

**Fix:**
```powershell
gcloud projects add-iam-policy-binding mediagent-demo `
  --member="serviceAccount:mediagent-local@mediagent-demo.iam.gserviceaccount.com" `
  --role="roles/aiplatform.user"
```

### Error: "File not found"
**Cause:** Volume mount path incorrect

**Windows paths use:**
- `$env:APPDATA` for AppData\Roaming
- `${PWD}` for current directory
- Use backticks (`) for line continuation in PowerShell

---

## Security Best Practices

1. **Never commit** `mediagent-key.json` to Git
2. **Add to .gitignore:**
   ```
   *.json
   !.env.example
   ```
3. **Use read-only mounts** (`:ro` flag)
4. **Rotate service account keys** regularly
5. **Use Workload Identity** in production (GKE)

---

## Comparison: Docker vs Local

| Aspect | Docker | Local (python main.py) |
|--------|--------|------------------------|
| Setup | More complex (credentials) | Simpler (auto-detects) |
| Isolation | Full isolation | Uses system Python |
| Production-like | ✅ Yes | ❌ No |
| Hot reload | ❌ No | ✅ Yes (with --reload) |
| Best for | Testing deployment | Development |

---

## Recommended Workflow

1. **Development:** Run locally with `python main.py` or `uvicorn main:app --reload`
2. **Testing:** Use Docker with mounted credentials
3. **Production:** Deploy to GKE with Workload Identity (no keys needed!)

---

**Next Steps:**
1. Stop current Docker container (Ctrl+C)
2. Run `gcloud auth application-default login`
3. Restart Docker with credentials mounted
4. Test upload at http://localhost:8000/docs

✅ **You should now be able to upload PDFs successfully!**

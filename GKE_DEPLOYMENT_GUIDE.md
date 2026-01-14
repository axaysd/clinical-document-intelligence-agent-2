# 🚀 GKE Deployment Guide (Beginner-Friendly)

This guide will help you deploy MediAgent to **Google Kubernetes Engine (GKE)** step-by-step. Perfect for learning Kubernetes concepts for interviews!

---

## 📚 What You'll Learn

By following this guide, you'll understand:
- ✅ How to create a GKE cluster
- ✅ Docker containerization basics
- ✅ Kubernetes deployments and services
- ✅ Workload Identity for secure authentication
- ✅ kubectl commands for managing applications

**Time needed:** 30-45 minutes (first time)

---

## 🎯 Prerequisites

Before starting, make sure you have:

1. **Google Cloud Account** with billing enabled
2. **gcloud CLI** installed ([Download here](https://cloud.google.com/sdk/docs/install))
3. **Docker Desktop** installed ([Download here](https://www.docker.com/products/docker-desktop))
4. **kubectl** installed (comes with gcloud)

### Verify Your Setup

```bash
# Check gcloud is installed
gcloud --version

# Check Docker is running
docker --version

# Check kubectl is installed
kubectl version --client

# Login to Google Cloud
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID
```

---

## 📋 Overview: What We're Building

```
┌─────────────────────────────────────────────────────────┐
│                    Internet                              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              GKE Load Balancer                           │
│              (External IP)                               │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Kubernetes Service                          │
│              (mediagent-service)                         │
└────────────────────┬────────────────────────────────────┘
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
    ┌─────────┐           ┌─────────┐
    │  Pod 1  │           │  Pod 2  │
    │ MediAgent│          │ MediAgent│
    └─────────┘           └─────────┘
          │                     │
          └──────────┬──────────┘
                     ▼
              Vertex AI API
```

---

## 🐳 Step 1: Build and Push Docker Image

### Why Docker?
Docker packages your app and all its dependencies into a container that runs the same everywhere.

### 1.1 Enable Required APIs

```bash
# Enable Container Registry and Artifact Registry
gcloud services enable containerregistry.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable container.googleapis.com
```

### 1.2 Configure Docker Authentication

```bash
# Allow Docker to push to Google Container Registry
gcloud auth configure-docker
```

### 1.3 Build Your Docker Image

```bash
# Navigate to your project
cd c:\Users\axays\Downloads\MediAgent

# Build the image (replace YOUR_PROJECT_ID)
docker build -t gcr.io/YOUR_PROJECT_ID/mediagent:latest .
```

**What this does:**
- Reads the `Dockerfile`
- Installs Python and dependencies
- Copies your code into the container
- Creates a runnable image

**Expected time:** 3-5 minutes

### 1.4 Test Locally (Optional but Recommended)

```bash
# Run the container locally to test
docker run -p 8000:8000 -e GCP_PROJECT_ID=mediagent-demo -e GCP_REGION=us-central1 -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/keys/application_default_credentials.json -v "$env:APPDATA\gcloud:/tmp/keys:ro" gcr.io/mediagent-demo/mediagent:latest

# Test in another terminal
curl http://localhost:8000/health

# Stop with Ctrl+C when done
```

### 1.5 Push to Container Registry

```bash
# Push the image to Google Cloud
docker push gcr.io/YOUR_PROJECT_ID/mediagent:latest
```

**Expected time:** 2-3 minutes

✅ **Checkpoint:** Your Docker image is now in Google Cloud!

---

## ☸️ Step 2: Create GKE Cluster

### Why GKE?
GKE manages Kubernetes for you - handles updates, scaling, and infrastructure.

### 2.1 Create the Cluster

```bash
# Create a GKE cluster (replace YOUR_PROJECT_ID)
gcloud container clusters create mediagent-cluster \
  --region us-central1 \
  --num-nodes 2 \
  --machine-type e2-standard-2 \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 3 \
  --workload-pool=YOUR_PROJECT_ID.svc.id.goog
```

**What each flag means:**
- `--region us-central1`: Where to create the cluster
- `--num-nodes 2`: Start with 2 worker nodes
- `--machine-type e2-standard-2`: 2 vCPUs, 8GB RAM per node
- `--enable-autoscaling`: Automatically add/remove nodes based on load
- `--min-nodes 1 --max-nodes 3`: Scale between 1-3 nodes
- `--workload-pool`: Enables Workload Identity (secure authentication)

**Expected time:** 5-10 minutes ⏰

**Cost estimate:** ~$50-70/month (can delete cluster when not using)

### 2.2 Connect kubectl to Your Cluster

```bash
# Get credentials for kubectl
gcloud container clusters get-credentials mediagent-cluster --region us-central1
```

**Test the connection:**
```bash
# Should show your cluster nodes
kubectl get nodes
```

✅ **Checkpoint:** Your Kubernetes cluster is ready!

---

## 🔐 Step 3: Set Up Workload Identity

### Why Workload Identity?
Allows your pods to authenticate with Google Cloud services (like Vertex AI) securely without storing credentials.

### 3.1 Create Google Cloud Service Account

```bash
# Create a service account for your app
gcloud iam service-accounts create mediagent \
  --display-name="MediAgent Service Account"
```

### 3.2 Grant Vertex AI Permissions

```bash
# Allow the service account to use Vertex AI
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:mediagent@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

### 3.3 Create Kubernetes Service Account

```bash
# Create a Kubernetes service account
kubectl create serviceaccount mediagent-sa
```

### 3.4 Bind Workload Identity

```bash
# Link Kubernetes SA to Google Cloud SA
gcloud iam service-accounts add-iam-policy-binding \
  mediagent@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:YOUR_PROJECT_ID.svc.id.goog[default/mediagent-sa]"

# Annotate the Kubernetes service account
kubectl annotate serviceaccount mediagent-sa \
  iam.gke.io/gcp-service-account=mediagent@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

✅ **Checkpoint:** Authentication is configured!

---

## 📦 Step 4: Deploy to Kubernetes

### 4.1 Update Deployment Manifest

Open `k8s/deployment.yaml` and replace `YOUR_PROJECT_ID` with your actual project ID:

**Find and replace these lines:**
- Line ~20: `image: gcr.io/YOUR_PROJECT_ID/mediagent:latest`
- Line ~26: `value: "your-project-id"`
- Line ~66: `iam.gke.io/gcp-service-account: mediagent@YOUR_PROJECT_ID.iam.gserviceaccount.com`

**Or use this command to do it automatically:**
```bash
# Windows PowerShell
$projectId = "YOUR_PROJECT_ID"
(Get-Content k8s\deployment.yaml) -replace 'YOUR_PROJECT_ID', $projectId | Set-Content k8s\deployment.yaml
(Get-Content k8s\deployment.yaml) -replace 'your-project-id', $projectId | Set-Content k8s\deployment.yaml
```

### 4.2 Deploy the Application

```bash
# Apply the deployment
kubectl apply -f k8s/deployment.yaml

# Apply the service (creates load balancer)
kubectl apply -f k8s/service.yaml
```

**What this does:**
- Creates 2 pods running your app
- Creates a LoadBalancer service
- Provisions an external IP address

### 4.3 Check Deployment Status

```bash
# Watch pods starting up
kubectl get pods -w

# You should see something like:
# NAME                        READY   STATUS    RESTARTS   AGE
# mediagent-xxxxxxxxx-xxxxx   1/1     Running   0          30s
# mediagent-xxxxxxxxx-xxxxx   1/1     Running   0          30s

# Press Ctrl+C to stop watching
```

**Pod Status Meanings:**
- `Pending`: Waiting for resources
- `ContainerCreating`: Pulling Docker image
- `Running`: App is running! ✅
- `CrashLoopBackOff`: Something's wrong (check logs)

### 4.4 Get External IP Address

```bash
# Check service status
kubectl get service mediagent-service

# Wait until EXTERNAL-IP shows an IP (not <pending>)
# This can take 2-3 minutes
```

**Example output:**
```
NAME                TYPE           CLUSTER-IP      EXTERNAL-IP      PORT(S)
mediagent-service   LoadBalancer   10.XX.XX.XX     34.XX.XX.XX      8000:30XXX/TCP
```

✅ **Checkpoint:** Your app is live on the internet!

---

## 🧪 Step 5: Test Your Deployment

### 5.1 Health Check

```bash
# Replace with your EXTERNAL-IP
curl http://34.XX.XX.XX:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "faiss_index": "0 chunks",
    "adk_agent": "ready",
    "tools": "3 tools available"
  }
}
```

### 5.2 View API Docs

Open in your browser:
```
http://34.XX.XX.XX:8000/docs
```

### 5.3 Upload a Test Document

```bash
# Upload a PDF
curl -X POST "http://34.XX.XX.XX:8000/upload" \
  -F "file=@path/to/test.pdf"
```

### 5.4 Query the System

```bash
curl -X POST "http://34.XX.XX.XX:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is this document about?",
    "session_id": "test-session"
  }'
```

---

## 🔍 Step 6: Monitor and Debug

### View Logs

```bash
# Get pod name
kubectl get pods

# View logs (replace pod name)
kubectl logs mediagent-xxxxxxxxx-xxxxx

# Follow logs in real-time
kubectl logs -f mediagent-xxxxxxxxx-xxxxx

# View logs from all pods
kubectl logs -l app=mediagent
```

### Check Pod Details

```bash
# Describe a pod (shows events and status)
kubectl describe pod mediagent-xxxxxxxxx-xxxxx
```

### Execute Commands in Pod

```bash
# Open a shell inside the pod
kubectl exec -it mediagent-xxxxxxxxx-xxxxx -- /bin/bash

# Check environment variables
kubectl exec mediagent-xxxxxxxxx-xxxxx -- env
```

### Common Issues and Fixes

#### Pods stuck in "ImagePullBackOff"
```bash
# Check if image exists
gcloud container images list --repository=gcr.io/YOUR_PROJECT_ID

# Verify image name in deployment.yaml matches
kubectl describe pod mediagent-xxx | grep Image
```

#### Pods in "CrashLoopBackOff"
```bash
# Check logs for errors
kubectl logs mediagent-xxx

# Common causes:
# - Missing environment variables
# - Authentication issues
# - Application errors
```

#### Can't reach external IP
```bash
# Check service status
kubectl get service mediagent-service

# Check firewall rules
gcloud compute firewall-rules list

# Verify pods are running
kubectl get pods
```

---

## 📊 Step 7: Scale Your Application

### Manual Scaling

```bash
# Scale to 3 replicas
kubectl scale deployment mediagent --replicas=3

# Check status
kubectl get pods
```

### Auto-scaling (HPA)

```bash
# Create horizontal pod autoscaler
kubectl autoscale deployment mediagent \
  --cpu-percent=70 \
  --min=2 \
  --max=5

# Check autoscaler status
kubectl get hpa
```

---

## 🔄 Step 8: Update Your Application

### When you make code changes:

```bash
# 1. Rebuild Docker image
docker build -t gcr.io/YOUR_PROJECT_ID/mediagent:v2 .

# 2. Push new version
docker push gcr.io/YOUR_PROJECT_ID/mediagent:v2

# 3. Update deployment
kubectl set image deployment/mediagent \
  mediagent=gcr.io/YOUR_PROJECT_ID/mediagent:v2

# 4. Watch rollout
kubectl rollout status deployment/mediagent
```

### Rollback if needed:

```bash
# Undo last deployment
kubectl rollout undo deployment/mediagent

# Check rollout history
kubectl rollout history deployment/mediagent
```

---

## 🧹 Step 9: Clean Up (Save Money!)

### When you're done testing:

```bash
# Delete the service (removes load balancer)
kubectl delete service mediagent-service

# Delete the deployment
kubectl delete deployment mediagent

# Delete the cluster (saves the most money)
gcloud container clusters delete mediagent-cluster --region us-central1

# Delete Docker images (optional)
gcloud container images delete gcr.io/YOUR_PROJECT_ID/mediagent:latest
```

**Cost savings:** Deleting the cluster stops all charges!

---

## 🎓 Interview Preparation: Key Concepts

### Kubernetes Concepts to Know

1. **Pod**: Smallest deployable unit, runs one or more containers
2. **Deployment**: Manages pods, handles updates and scaling
3. **Service**: Exposes pods to network traffic
4. **LoadBalancer**: Provides external IP for accessing your app
5. **ConfigMap**: Stores configuration data
6. **Secret**: Stores sensitive data (passwords, keys)
7. **Namespace**: Logical cluster separation
8. **Replica**: Copy of a pod for high availability

### Common kubectl Commands

```bash
# Get resources
kubectl get pods
kubectl get services
kubectl get deployments

# Describe resources (detailed info)
kubectl describe pod <pod-name>
kubectl describe service <service-name>

# Logs
kubectl logs <pod-name>
kubectl logs -f <pod-name>  # Follow logs

# Execute commands
kubectl exec -it <pod-name> -- /bin/bash

# Apply configurations
kubectl apply -f <file.yaml>

# Delete resources
kubectl delete pod <pod-name>
kubectl delete -f <file.yaml>

# Scale
kubectl scale deployment <name> --replicas=3

# Update image
kubectl set image deployment/<name> <container>=<new-image>

# Rollback
kubectl rollout undo deployment/<name>
```

### GKE-Specific Concepts

1. **Workload Identity**: Secure way for pods to access GCP services
2. **Node Pools**: Groups of nodes with same configuration
3. **Cluster Autoscaler**: Automatically adds/removes nodes
4. **Regional vs Zonal**: Regional = multi-zone HA, Zonal = single zone

### Architecture Questions You Might Get

**Q: How does traffic reach your pod?**
```
Internet → LoadBalancer → Service → Pod
```

**Q: What happens when you deploy a new version?**
```
1. New pods created with new image
2. Wait for new pods to be ready
3. Old pods terminated
4. Zero downtime rolling update
```

**Q: How does your app authenticate with Vertex AI?**
```
Pod → Kubernetes SA → Workload Identity → GCP SA → Vertex AI
```

---

## 📚 Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Docker Documentation](https://docs.docker.com/)

---

## 🎯 Quick Reference: Complete Deployment

```bash
# 1. Build and push image
docker build -t gcr.io/YOUR_PROJECT_ID/mediagent:latest .
docker push gcr.io/YOUR_PROJECT_ID/mediagent:latest

# 2. Create cluster
gcloud container clusters create mediagent-cluster \
  --region us-central1 --num-nodes 2 \
  --machine-type e2-standard-2 \
  --workload-pool=YOUR_PROJECT_ID.svc.id.goog

# 3. Setup authentication
gcloud iam service-accounts create mediagent
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:mediagent@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
kubectl create serviceaccount mediagent-sa
gcloud iam service-accounts add-iam-policy-binding \
  mediagent@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:YOUR_PROJECT_ID.svc.id.goog[default/mediagent-sa]"

# 4. Deploy
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# 5. Get IP
kubectl get service mediagent-service

# 6. Test
curl http://EXTERNAL-IP:8000/health
```

---

**Good luck with your interview! 🚀** You've got this!

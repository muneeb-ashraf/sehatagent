# 🚀 SehatAgent - Complete Step-by-Step Execution Guide

## For IDEAX92 Hackathon - 1-Day Implementation

---

## ⏰ Timeline Overview (8-10 Hours)

| Phase | Time | Tasks |
|-------|------|-------|
| 1. Setup | 30 min | Project setup, dependencies |
| 2. GCP Config | 30 min | Configure GCP access |
| 3. Database | 30 min | Setup Cloud SQL |
| 4. Test Local | 1 hour | Run and test locally |
| 5. Docker | 30 min | Build container |
| 6. Deploy | 1 hour | Deploy to Cloud Run |
| 7. Test & Demo | 1-2 hours | End-to-end testing |
| 8. Polish | 1-2 hours | Documentation, demo prep |

---

## Phase 1: Project Setup (30 minutes)

### Step 1.1: Create Project Directory

```bash
# Create project directory
mkdir sehatagent
cd sehatagent
```

### Step 1.2: Copy All Files

Copy all the files I created into this structure:

```
sehatagent/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py
│   │   ├── orchestrator.py
│   │   ├── symptom_agent.py
│   │   ├── risk_agent.py
│   │   ├── recommendation_agent.py
│   │   ├── safety_agent.py
│   │   └── fallback_agent.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── health.py
│   │   ├── voice.py
│   │   ├── worker.py
│   │   └── degraded.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── vertex_ai.py
│   │   ├── rag_service.py
│   │   ├── language_service.py
│   │   └── speech_service.py
│   └── database/
│       ├── __init__.py
│       ├── connection.py
│       ├── models.py
│       └── crud.py
├── data/
│   ├── faiss_index/
│   └── fallback_rules.json
├── scripts/
│   ├── build_faiss_index.py
│   └── init_db.py
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

### Step 1.3: Setup Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 1.4: Create .env File

```bash
cp .env.example .env
```

Edit `.env` with your hackathon-provided credentials.

---

## Phase 2: GCP Configuration (30 minutes)

### Step 2.1: Install gcloud CLI

If not already installed:

```bash
# Download and install from:
# https://cloud.google.com/sdk/docs/install
```

### Step 2.2: Authenticate

```bash
# Login to GCP
gcloud auth login

# Set your project (provided by hackathon organizers)
gcloud config set project YOUR_PROJECT_ID

# Verify
gcloud config get-value project
```

### Step 2.3: Enable APIs

```bash
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    aiplatform.googleapis.com \
    sqladmin.googleapis.com \
    speech.googleapis.com
```

### Step 2.4: Setup Application Default Credentials

```bash
gcloud auth application-default login
```

This allows local development to access GCP services.

---

## Phase 3: Database Setup (30 minutes)

### Step 3.1: Get Database Credentials

The hackathon organizers will provide:
- `DB_HOST` - Cloud SQL host or instance connection name
- `DB_NAME` - Database name
- `DB_USER` - Username
- `DB_PASSWORD` - Password

### Step 3.2: Update .env File

```env
# Cloud SQL Configuration
DB_HOST=your-provided-host
DB_PORT=5432
DB_NAME=sehatagent
DB_USER=your-provided-user
DB_PASSWORD=your-provided-password

# For Cloud Run (if provided)
# DB_INSTANCE_CONNECTION_NAME=project:region:instance
```

### Step 3.3: Initialize Database Tables

```bash
python scripts/init_db.py
```

You should see output showing tables created:
- health_sessions
- agent_logs
- session_feedback
- cached_responses
- aggregated_stats

---

## Phase 4: Local Testing (1 hour)

### Step 4.1: Build FAISS Index

```bash
# Set project ID for Vertex AI
export GCP_PROJECT_ID=your-project-id

# Build index (creates embeddings)
python scripts/build_faiss_index.py
```

If Vertex AI isn't available yet, the script will create a keyword-based index.

### Step 4.2: Run Application Locally

```bash
uvicorn app.main:app --reload --port 8080
```

### Step 4.3: Test Endpoints

Open another terminal:

```bash
# Test root endpoint
curl http://localhost:8080/

# Test health check
curl http://localhost:8080/health

# Test health analysis (English)
curl -X POST http://localhost:8080/api/v1/health/analyze \
    -H "Content-Type: application/json" \
    -d '{"query": "I have fever and headache for 2 days", "language": "en"}'

# Test health analysis (Roman Urdu)
curl -X POST http://localhost:8080/api/v1/health/analyze \
    -H "Content-Type: application/json" \
    -d '{"query": "Mujhe 2 din se bukhar aur sir dard hai", "language": "auto"}'

# Test health analysis (Urdu)
curl -X POST http://localhost:8080/api/v1/health/analyze \
    -H "Content-Type: application/json" \
    -d '{"query": "مجھے بخار ہے اور سر میں درد ہے", "language": "ur"}'

# Test offline mode
curl -X POST http://localhost:8080/api/v1/offline/analyze \
    -H "Content-Type: application/json" \
    -d '{"query": "bukhar hai", "language": "roman_urdu"}'

# Test quick check
curl -X POST http://localhost:8080/api/v1/health/quick-check \
    -H "Content-Type: application/json" \
    -d '{"symptoms": ["fever", "headache"], "language": "en"}'

# Test worker dashboard
curl http://localhost:8080/api/v1/worker/dashboard

# Test emergency check (offline)
curl "http://localhost:8080/api/v1/offline/emergency-check?query=chest%20pain"
```

### Step 4.4: Access API Documentation

Open browser: http://localhost:8080/docs

This shows the interactive Swagger UI documentation.

---

## Phase 5: Docker Build (30 minutes)

### Step 5.1: Build Docker Image

```bash
# Build the image
docker build -t sehatagent:latest .

# Verify build
docker images | grep sehatagent
```

### Step 5.2: Test Docker Locally

```bash
# Run container
docker run -p 8080:8080 \
    -e GCP_PROJECT_ID=your-project-id \
    -e DB_HOST=host.docker.internal \
    -e DB_PORT=5432 \
    -e DB_NAME=sehatagent \
    -e DB_USER=your-user \
    -e DB_PASSWORD=your-password \
    sehatagent:latest

# Test
curl http://localhost:8080/health
```

---

## Phase 6: Deploy to Cloud Run (1 hour)

### Step 6.1: Create Artifact Registry Repository

```bash
gcloud artifacts repositories create sehatagent-repo \
    --repository-format=docker \
    --location=us-central1 \
    --description="SehatAgent Docker repository"
```

### Step 6.2: Configure Docker for GCP

```bash
gcloud auth configure-docker us-central1-docker.pkg.dev
```

### Step 6.3: Tag and Push Image

```bash
# Tag the image
docker tag sehatagent:latest \
    us-central1-docker.pkg.dev/YOUR_PROJECT_ID/sehatagent-repo/sehatagent:v1

# Push to Artifact Registry
docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/sehatagent-repo/sehatagent:v1
```

### Step 6.4: Deploy to Cloud Run

```bash
# Basic deployment
gcloud run deploy sehatagent \
    --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/sehatagent-repo/sehatagent:v1 \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --min-instances 0 \
    --max-instances 5 \
    --set-env-vars "GCP_PROJECT_ID=YOUR_PROJECT_ID,VERTEX_AI_LOCATION=us-central1,ENABLE_DEGRADED_MODE=true"
```

### Step 6.5: Deploy with Cloud SQL (if using Unix socket)

```bash
gcloud run deploy sehatagent \
    --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/sehatagent-repo/sehatagent:v1 \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --set-env-vars "GCP_PROJECT_ID=YOUR_PROJECT_ID" \
    --set-env-vars "DB_NAME=sehatagent" \
    --set-env-vars "DB_USER=your-user" \
    --set-env-vars "DB_PASSWORD=your-password" \
    --add-cloudsql-instances YOUR_INSTANCE_CONNECTION_NAME \
    --set-env-vars "DB_INSTANCE_CONNECTION_NAME=YOUR_INSTANCE_CONNECTION_NAME"
```

### Step 6.6: Get Service URL

After deployment, you'll get a URL like:
```
https://sehatagent-xxxxx-uc.a.run.app
```

---

## Phase 7: End-to-End Testing (1-2 hours)

### Step 7.1: Test Deployed API

```bash
# Replace with your actual URL
SERVICE_URL=https://sehatagent-xxxxx-uc.a.run.app

# Test root
curl $SERVICE_URL/

# Test health analysis
curl -X POST $SERVICE_URL/api/v1/health/analyze \
    -H "Content-Type: application/json" \
    -d '{
        "query": "Mujhe 3 din se bukhar hai aur sir mein dard hai",
        "language": "auto"
    }'
```

### Step 7.2: Test All Features

Run through each feature:

1. ✅ Symptom Analysis (English)
2. ✅ Symptom Analysis (Urdu)
3. ✅ Symptom Analysis (Roman Urdu)
4. ✅ Risk Assessment
5. ✅ Recommendations
6. ✅ Explainability (check response.explanation)
7. ✅ Offline Mode
8. ✅ Emergency Detection
9. ✅ Healthcare Worker Dashboard

### Step 7.3: Test Degraded Mode

Simulate offline mode:

```bash
curl -X POST $SERVICE_URL/api/v1/offline/analyze \
    -H "Content-Type: application/json" \
    -d '{"query": "mujhe bukhar hai", "language": "roman_urdu"}'
```

---

## Phase 8: Demo Preparation (1-2 hours)

### Step 8.1: Prepare Demo Script

**Demo Flow:**

1. **Introduction** (1 min)
   - Show the problem: healthcare access in Pakistan
   - Introduce SehatAgent

2. **Live Demo** (5-7 min)
   - Enter symptoms in Roman Urdu: "Mujhe 2 din se bukhar hai"
   - Show multilingual support (switch to Urdu)
   - Demonstrate risk assessment
   - Show recommendations in simple language
   - Show explainability (agent reasoning)

3. **Offline Mode** (2 min)
   - Demonstrate degraded mode working
   - Show rule-based fallback

4. **Healthcare Worker View** (2 min)
   - Show dashboard with aggregated insights

5. **Technical Architecture** (2 min)
   - Explain multi-agent system
   - Show GCP infrastructure compliance

### Step 8.2: Prepare Demo Data

Have these queries ready:

```
English:
"I have fever and headache for 3 days"
"Feeling very tired and dizzy"
"My child has diarrhea and vomiting"

Roman Urdu:
"Mujhe 3 din se bukhar hai aur sir mein dard hai"
"Bohat kamzori hai aur chakkar aa rahe hain"
"Bachay ko dast aur ulti ho rahi hai"

Urdu:
"مجھے تین دن سے بخار ہے"
"پیٹ میں درد ہے اور الٹی آ رہی ہے"

Emergency (to show safety):
"Seene mein shadeed dard hai"
```

### Step 8.3: Prepare Slides (Optional)

Key slides to have:
1. Problem Statement
2. Solution Overview
3. Architecture Diagram
4. Agent Flow
5. Technology Stack
6. Live Demo
7. Differentiators
8. Future Roadmap

---

## 🔧 Troubleshooting

### Common Issues

**1. Vertex AI Permission Denied**
```bash
# Grant Vertex AI access
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="user:your-email@gmail.com" \
    --role="roles/aiplatform.user"
```

**2. Cloud SQL Connection Issues**
- Make sure Cloud SQL Admin API is enabled
- Check if the service account has Cloud SQL Client role

**3. Docker Build Fails**
- Check if all files are in correct locations
- Verify requirements.txt has no typos

**4. Import Errors**
- Make sure all `__init__.py` files exist
- Check Python path

### Quick Fixes

```bash
# Reset and rebuild
docker system prune -f
docker build --no-cache -t sehatagent:latest .

# Check logs
gcloud run logs read sehatagent --region us-central1

# Redeploy
gcloud run deploy sehatagent --image ... --region us-central1
```

---

## 📋 Final Checklist

Before submission, verify:

- [ ] All endpoints working on Cloud Run
- [ ] Symptom analysis works in all 3 languages
- [ ] Risk assessment produces meaningful results
- [ ] Recommendations are in simple language
- [ ] Offline/degraded mode functional
- [ ] Healthcare worker dashboard accessible
- [ ] Explainability shown in responses
- [ ] Emergency detection working
- [ ] Docker container runs successfully
- [ ] README documentation complete
- [ ] Demo script prepared

---

## 🏆 Good Luck!

You have a comprehensive, production-ready solution. Focus on:
1. Clean demo flow
2. Highlighting differentiators
3. Showing real-world applicability

The multi-agent architecture, Pakistan-specific health knowledge, and robust offline mode will set you apart!

# 🏥 SehatAgent - صحت ایجنٹ

## Multi-Agent AI Health System for IDEAX92

> "Har Pakistani ki Sehat, AI ki Nigrani Mein"
> (Every Pakistani's Health, Under AI's Care)

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com)
[![GCP](https://img.shields.io/badge/GCP-Cloud%20Run-orange.svg)](https://cloud.google.com/run)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🌟 Overview

SehatAgent is a **Multi-Agent AI Health System** that provides preventive, explainable, and accessible healthcare guidance for Pakistan. Built for the IDEAX92 Hackathon, it demonstrates how specialized AI agents collaborate to analyze symptoms, assess risks, and generate personalized health recommendations.

### Key Features

- 🩺 **Symptom Analysis** - Analyzes symptoms in English, Urdu, and Roman Urdu
- ⚠️ **Risk Assessment** - Identifies health & nutrition risks (Pakistan-specific)
- 💊 **Preventive Guidance** - Simple language recommendations
- 👨‍⚕️ **Healthcare Worker Dashboard** - Summarized insights for doctors/LHWs
- 🗣️ **Voice Input** - Supports Urdu, Punjabi, and English voice
- 📴 **Offline Mode** - Works without internet using cached knowledge

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                            │
│              (Web/Mobile - English/Urdu/Punjabi)                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    FastAPI Backend                               │
│                   (Google Cloud Run)                             │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                  Agent Orchestrator                              │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────┤
│  Symptom    │    Risk     │   Health    │   Safety    │ Offline │
│  Analyzer   │  Assessor   │   Advisor   │   Guard     │ Helper  │
└─────────────┴──────┬──────┴─────────────┴─────────────┴─────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼───────┐       ┌────────▼────────┐
│   Vertex AI   │       │      FAISS      │
│   (Gemini)    │       │  (Local Index)  │
└───────────────┘       └─────────────────┘
        │
┌───────▼───────┐
│   Cloud SQL   │
│  (PostgreSQL) │
└───────────────┘
```

### Agent Roles

| Agent | Role | Responsibility |
|-------|------|----------------|
| **SymptomAnalyzer** | Analysis | Extract symptoms from multilingual input |
| **RiskAssessor** | Assessment | Identify health/nutrition risks |
| **HealthAdvisor** | Recommendation | Generate preventive guidance |
| **SafetyGuard** | Ethics | Ensure safe, ethical responses |
| **OfflineHelper** | Fallback | Rule-based guidance when offline |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker
- GCP Account (provided by hackathon)
- gcloud CLI installed

### 1. Clone & Setup

```bash
# Clone repository
git clone <your-repo-url>
cd sehatagent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your credentials
```

### 2. Configure Environment

Edit `.env` with your GCP credentials:

```env
GCP_PROJECT_ID=your-project-id
DB_HOST=your-db-host
DB_NAME=sehatagent
DB_USER=your-db-user
DB_PASSWORD=your-db-password
```

### 3. Initialize Database

```bash
python scripts/init_db.py
```

### 4. Build FAISS Index

```bash
python scripts/build_faiss_index.py
```

### 5. Run Locally

```bash
uvicorn app.main:app --reload --port 8080
```

Visit: http://localhost:8080

---

## 🐳 Docker Deployment

### Build Docker Image

```bash
docker build -t sehatagent:latest .
```

### Run Locally with Docker

```bash
docker run -p 8080:8080 --env-file .env sehatagent:latest
```

---

## ☁️ GCP Cloud Run Deployment

### Step 1: Authenticate with GCP

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### Step 2: Enable Required APIs

```bash
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    aiplatform.googleapis.com \
    sqladmin.googleapis.com \
    speech.googleapis.com
```

### Step 3: Create Artifact Registry Repository

```bash
gcloud artifacts repositories create sehatagent-repo \
    --repository-format=docker \
    --location=us-central1
```

### Step 4: Build and Push Docker Image

```bash
# Configure Docker for GCP
gcloud auth configure-docker us-central1-docker.pkg.dev

# Build and tag
docker build -t us-central1-docker.pkg.dev/YOUR_PROJECT_ID/sehatagent-repo/sehatagent:v1 .

# Push to Artifact Registry
docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/sehatagent-repo/sehatagent:v1
```

### Step 5: Deploy to Cloud Run

```bash
gcloud run deploy sehatagent \
    --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/sehatagent-repo/sehatagent:v1 \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars "GCP_PROJECT_ID=YOUR_PROJECT_ID" \
    --set-env-vars "DB_HOST=/cloudsql/YOUR_INSTANCE_CONNECTION" \
    --set-env-vars "DB_NAME=sehatagent" \
    --set-env-vars "DB_USER=your-user" \
    --set-env-vars "DB_PASSWORD=your-password" \
    --add-cloudsql-instances YOUR_INSTANCE_CONNECTION \
    --memory 2Gi \
    --cpu 2 \
    --min-instances 0 \
    --max-instances 10
```

---

## 📚 API Documentation

### Main Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health/analyze` | POST | Analyze health query |
| `/api/v1/health/quick-check` | POST | Quick symptom check |
| `/api/v1/voice/transcribe` | POST | Voice to text |
| `/api/v1/voice/analyze` | POST | Voice health analysis |
| `/api/v1/worker/dashboard` | GET | Healthcare worker insights |
| `/api/v1/offline/analyze` | POST | Offline mode analysis |

### Example: Health Analysis

```bash
curl -X POST "https://your-service-url/api/v1/health/analyze" \
    -H "Content-Type: application/json" \
    -d '{
        "query": "Mujhe 3 din se bukhar hai aur sir mein dard hai",
        "language": "auto"
    }'
```

### Example Response

```json
{
    "success": true,
    "session_id": "abc123",
    "mode": "full",
    "language": "roman_urdu",
    "symptoms_identified": ["fever", "headache"],
    "risk_level": "MEDIUM",
    "recommendations": [
        "Rest and stay hydrated with water and ORS",
        "Take paracetamol for fever",
        "See doctor if fever persists beyond 3 days"
    ],
    "explanation": {
        "summary": "Based on your fever and headache...",
        "agent_reasoning": [...]
    },
    "disclaimer": "This is not medical advice..."
}
```

---

## 🔒 Degraded Mode

SehatAgent works offline using:

1. **Rule-based symptom matching** - Pre-defined patterns
2. **Local FAISS index** - Cached embeddings
3. **Offline knowledge base** - JSON-based health data

### Testing Degraded Mode

```bash
curl -X POST "http://localhost:8080/api/v1/offline/analyze" \
    -H "Content-Type: application/json" \
    -d '{"query": "bukhar hai", "language": "roman_urdu"}'
```

---

## 🌍 Supported Languages

| Language | Input | Output | Voice |
|----------|-------|--------|-------|
| English | ✅ | ✅ | ✅ |
| Urdu (اردو) | ✅ | ✅ | ✅ |
| Roman Urdu | ✅ | ✅ | - |
| Punjabi (پنجابی) | - | - | ✅ |

---

## 📊 Healthcare Worker Dashboard

Access aggregated insights at `/api/v1/worker/dashboard`:

- Total consultations
- Common symptoms distribution
- Risk level breakdown
- Urgent cases requiring attention
- Community health trends

---

## 🧪 Testing

```bash
# Run tests
pytest tests/ -v

# Test specific module
pytest tests/test_agents.py -v
```

---

## 📁 Project Structure

```
sehatagent/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── agents/              # Multi-agent system
│   │   ├── orchestrator.py  # Agent coordination
│   │   ├── symptom_agent.py # Symptom analysis
│   │   ├── risk_agent.py    # Risk assessment
│   │   ├── recommendation_agent.py
│   │   ├── safety_agent.py  # Ethical guardrails
│   │   └── fallback_agent.py # Offline mode
│   ├── api/                 # API endpoints
│   ├── services/            # External services
│   │   ├── vertex_ai.py     # Gemini integration
│   │   ├── rag_service.py   # FAISS RAG
│   │   ├── language_service.py
│   │   └── speech_service.py
│   └── database/            # PostgreSQL models
├── data/                    # Preloaded data
├── scripts/                 # Utility scripts
├── Dockerfile               # Container config
└── requirements.txt         # Dependencies
```

---

## 🏆 Winning Features

1. **Pakistan-Specific Health Knowledge** - Typhoid, Dengue, TB patterns
2. **Multilingual Voice Input** - Urdu, Punjabi support
3. **Robust Offline Mode** - Works in low-connectivity areas
4. **Explainable AI** - Shows reasoning for all decisions
5. **Healthcare Worker Support** - Dashboard for LHWs
6. **Privacy-First** - No raw health data stored

---

## 🤝 Contributing

Built for IDEAX92 Hackathon by **BiTech Digital**

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🆘 Support

- **Emergency (Pakistan)**: 1122
- **Edhi Foundation**: 115

---

*Built with ❤️ for Pakistan's Healthcare*

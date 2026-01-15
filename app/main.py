"""
SehatAgent - Main FastAPI Application
Multi-Agent Preventive Healthcare System for IDEAX92
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import structlog
import time

from app.config import get_settings
from app.api import health, voice, worker, degraded
from app.database.connection import init_db, close_db
from app.services.rag_service import RAGService
from app.agents.orchestrator import AgentOrchestrator

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

settings = get_settings()

# Global instances
rag_service: RAGService = None
orchestrator: AgentOrchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global rag_service, orchestrator
    
    logger.info("Starting SehatAgent", version=settings.APP_VERSION)
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Initialize RAG service with FAISS
    rag_service = RAGService()
    await rag_service.initialize()
    logger.info("RAG service initialized with FAISS")
    
    # Initialize Agent Orchestrator
    orchestrator = AgentOrchestrator(rag_service=rag_service)
    await orchestrator.initialize()
    logger.info("Agent orchestrator initialized")
    
    yield
    
    # Cleanup
    await close_db()
    logger.info("SehatAgent shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="SehatAgent - صحت ایجنٹ",
    description="""
    Multi-Agent AI Health System for Preventive, Accessible & Sustainable Healthcare
    
    ## Features
    - 🩺 Symptom Analysis & Health Indicators
    - ⚠️ Health & Nutrition Risk Assessment
    - 💊 Preventive Guidance in Simple Language
    - 👨‍⚕️ Healthcare Worker Insights Dashboard
    - 🗣️ Voice Input (Urdu, Punjabi, English)
    - 📴 Offline/Degraded Mode Support
    
    ## Languages Supported
    - English
    - اردو (Urdu)
    - Roman Urdu
    - پنجابی (Punjabi - Voice)
    
    Built for IDEAX92 Hackathon by BiTech Digital
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "message_ur": "سسٹم میں خرابی۔ براہ کرم دوبارہ کوشش کریں۔",
            "degraded_mode_available": settings.ENABLE_DEGRADED_MODE
        }
    )


# Include routers
app.include_router(health.router, prefix="/api/v1/health", tags=["Health Analysis"])
app.include_router(voice.router, prefix="/api/v1/voice", tags=["Voice Input"])
app.include_router(worker.router, prefix="/api/v1/worker", tags=["Healthcare Worker"])
app.include_router(degraded.router, prefix="/api/v1/offline", tags=["Degraded Mode"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "name": "SehatAgent - صحت ایجنٹ",
        "tagline": "Har Pakistani ki Sehat, AI ki Nigrani Mein",
        "version": settings.APP_VERSION,
        "status": "operational",
        "endpoints": {
            "health_analysis": "/api/v1/health/analyze",
            "voice_input": "/api/v1/voice/transcribe",
            "worker_dashboard": "/api/v1/worker/insights",
            "offline_mode": "/api/v1/offline/analyze"
        },
        "supported_languages": ["English", "اردو", "Roman Urdu", "پنجابی"],
        "agents": [
            "SymptomAnalyzer",
            "RiskAssessor", 
            "HealthAdvisor",
            "SafetyGuard",
            "OfflineHelper"
        ]
    }


# Health check endpoint (required for Cloud Run)
@app.get("/health")
async def health_check():
    """Health check for Cloud Run"""
    return {
        "status": "healthy",
        "database": "connected",
        "rag_service": "ready",
        "agents": "initialized"
    }


# Degraded mode check endpoint
@app.get("/api/v1/status")
async def system_status():
    """Check system status and available modes"""
    global orchestrator
    
    vertex_ai_available = await orchestrator.check_vertex_ai_health() if orchestrator else False
    
    return {
        "vertex_ai": "available" if vertex_ai_available else "unavailable",
        "mode": "full" if vertex_ai_available else "degraded",
        "faiss_index": "loaded",
        "supported_features": {
            "symptom_analysis": True,
            "nutrition_assessment": True,
            "voice_input": vertex_ai_available,
            "multilingual": True,
            "offline_mode": True
        }
    }


# Get orchestrator instance (for dependency injection)
def get_orchestrator() -> AgentOrchestrator:
    """Dependency to get agent orchestrator"""
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="System initializing")
    return orchestrator


def get_rag() -> RAGService:
    """Dependency to get RAG service"""
    if rag_service is None:
        raise HTTPException(status_code=503, detail="RAG service initializing")
    return rag_service

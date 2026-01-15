"""
Health Analysis API Endpoints
Main endpoints for symptom analysis and health guidance
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import structlog

from app.agents.orchestrator import AgentOrchestrator
from app.services.rag_service import RAGService
from app.config import get_settings, MEDICAL_SAFETY_CONFIG

logger = structlog.get_logger()
settings = get_settings()

router = APIRouter()


# Request/Response Models
class HealthQueryRequest(BaseModel):
    """Request model for health analysis"""
    query: str = Field(..., description="Health query or symptoms description", min_length=3, max_length=2000)
    language: str = Field(default="auto", description="Language: en, ur, roman_urdu, or auto")
    session_id: Optional[str] = Field(default=None, description="Session ID for tracking")
    include_explanation: bool = Field(default=True, description="Include agent reasoning")
    user_context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context (age, gender, etc.)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Mujhe 3 din se bukhar hai aur sir mein dard hai",
                "language": "auto",
                "include_explanation": True
            }
        }


class SymptomInfo(BaseModel):
    """Individual symptom information"""
    name: str
    severity: Optional[str] = None
    duration: Optional[str] = None


class RiskInfo(BaseModel):
    """Risk assessment information"""
    condition: str
    type: str
    severity: float
    explanation: Optional[str] = None
    action_needed: Optional[str] = None


class HealthAnalysisResponse(BaseModel):
    """Response model for health analysis"""
    success: bool
    session_id: str
    mode: str  # "full" or "degraded"
    language: str
    
    # Analysis results
    symptoms_identified: List[str]
    health_indicators: Dict[str, Any]
    
    # Risk assessment
    identified_risks: List[Dict[str, Any]]
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    
    # Recommendations
    recommendations: List[str]
    
    # Explainability
    explanation: Optional[Dict[str, Any]] = None
    
    # Safety
    safety_flags: List[str]
    disclaimer: str
    
    # Metadata
    processing_time_seconds: float


class QuickSymptomCheckRequest(BaseModel):
    """Quick symptom check request"""
    symptoms: List[str] = Field(..., description="List of symptoms")
    language: str = Field(default="en")


class QuickSymptomCheckResponse(BaseModel):
    """Quick symptom check response"""
    possible_conditions: List[str]
    risk_level: str
    should_see_doctor: bool
    basic_recommendations: List[str]


# Dependency to get orchestrator
async def get_orchestrator():
    """Get the agent orchestrator instance"""
    from app.main import orchestrator
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="System initializing, please try again")
    return orchestrator


# Endpoints
@router.post("/analyze", response_model=HealthAnalysisResponse)
async def analyze_health_query(
    request: HealthQueryRequest,
    background_tasks: BackgroundTasks,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """
    Analyze health query and provide recommendations
    
    This is the main endpoint for health analysis. It:
    1. Detects language (English, Urdu, Roman Urdu)
    2. Analyzes symptoms using multiple AI agents
    3. Assesses health and nutrition risks
    4. Provides preventive guidance in simple language
    5. Returns explainable AI decisions
    
    Supports degraded mode when cloud services unavailable.
    """
    logger.info("Health analysis request", 
               query_length=len(request.query),
               language=request.language)
    
    try:
        # Process through agent orchestrator
        result = await orchestrator.process_health_query(
            user_input=request.query,
            user_language=request.language,
            session_id=request.session_id
        )
        
        # Build response
        response = HealthAnalysisResponse(
            success=result.get("success", True),
            session_id=result.get("session_id", ""),
            mode=result.get("mode", "full"),
            language=result.get("language", "en"),
            symptoms_identified=result.get("analysis", {}).get("symptoms_identified", []),
            health_indicators=result.get("analysis", {}).get("health_indicators", {}),
            identified_risks=result.get("risks", {}).get("identified_risks", []),
            risk_level=result.get("risks", {}).get("risk_level", "LOW"),
            recommendations=result.get("recommendations", {}).get("preventive_guidance", []),
            explanation=result.get("explanation") if request.include_explanation else None,
            safety_flags=result.get("risks", {}).get("safety_flags", []),
            disclaimer=result.get("disclaimer", MEDICAL_SAFETY_CONFIG["disclaimers"]["en"]),
            processing_time_seconds=result.get("processing_time_seconds", 0)
        )
        
        # Log for analytics (background)
        background_tasks.add_task(
            log_analysis_request,
            session_id=response.session_id,
            symptoms=response.symptoms_identified,
            risk_level=response.risk_level
        )
        
        return response
        
    except Exception as e:
        logger.error("Health analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/quick-check", response_model=QuickSymptomCheckResponse)
async def quick_symptom_check(
    request: QuickSymptomCheckRequest,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """
    Quick symptom check without full analysis
    
    Provides fast preliminary assessment based on symptom patterns.
    Good for mobile/low-bandwidth scenarios.
    """
    try:
        # Use fallback agent for quick check
        from app.agents.fallback_agent import OfflineHelperAgent
        
        fallback = orchestrator.agents.get("offline_helper")
        if not fallback:
            fallback = OfflineHelperAgent()
        
        # Simple pattern matching
        symptoms_text = " ".join(request.symptoms)
        
        # Quick risk assessment
        emergency_keywords = ["chest pain", "can't breathe", "unconscious", "severe bleeding"]
        is_emergency = any(kw in symptoms_text.lower() for kw in emergency_keywords)
        
        if is_emergency:
            return QuickSymptomCheckResponse(
                possible_conditions=["Requires immediate medical attention"],
                risk_level="CRITICAL",
                should_see_doctor=True,
                basic_recommendations=["Call emergency services (1122) immediately"]
            )
        
        # Basic condition matching
        possible_conditions = []
        recommendations = []
        
        symptom_conditions = {
            "fever": ["Viral infection", "Flu", "Typhoid"],
            "headache": ["Tension headache", "Migraine", "Dehydration"],
            "cough": ["Common cold", "Bronchitis", "Allergies"],
            "diarrhea": ["Food poisoning", "Gastroenteritis"],
            "fatigue": ["Anemia", "Vitamin deficiency", "Sleep issues"],
        }
        
        for symptom in request.symptoms:
            symptom_lower = symptom.lower()
            for key, conditions in symptom_conditions.items():
                if key in symptom_lower:
                    possible_conditions.extend(conditions)
        
        possible_conditions = list(set(possible_conditions))[:5]
        
        # Determine risk level
        high_risk_symptoms = ["blood", "severe", "persistent", "chest"]
        has_high_risk = any(kw in symptoms_text.lower() for kw in high_risk_symptoms)
        
        risk_level = "HIGH" if has_high_risk else "MEDIUM" if len(request.symptoms) > 2 else "LOW"
        should_see_doctor = risk_level in ["HIGH", "CRITICAL"]
        
        # Basic recommendations
        recommendations = [
            "Rest and stay hydrated",
            "Monitor your symptoms",
            "Seek medical attention if symptoms worsen"
        ]
        
        return QuickSymptomCheckResponse(
            possible_conditions=possible_conditions or ["General health concern"],
            risk_level=risk_level,
            should_see_doctor=should_see_doctor,
            basic_recommendations=recommendations
        )
        
    except Exception as e:
        logger.error("Quick check failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/symptoms")
async def get_common_symptoms():
    """
    Get list of common symptoms in multiple languages
    
    Useful for building UI symptom selectors
    """
    return {
        "symptoms": [
            {"id": "fever", "en": "Fever", "ur": "بخار", "roman_urdu": "Bukhar"},
            {"id": "headache", "en": "Headache", "ur": "سر درد", "roman_urdu": "Sir Dard"},
            {"id": "cough", "en": "Cough", "ur": "کھانسی", "roman_urdu": "Khansi"},
            {"id": "cold", "en": "Cold/Flu", "ur": "زکام", "roman_urdu": "Zukam"},
            {"id": "stomach_pain", "en": "Stomach Pain", "ur": "پیٹ درد", "roman_urdu": "Pait Dard"},
            {"id": "diarrhea", "en": "Diarrhea", "ur": "دست", "roman_urdu": "Dast"},
            {"id": "vomiting", "en": "Vomiting", "ur": "الٹی", "roman_urdu": "Ulti"},
            {"id": "fatigue", "en": "Fatigue/Weakness", "ur": "کمزوری", "roman_urdu": "Kamzori"},
            {"id": "body_aches", "en": "Body Aches", "ur": "جسم میں درد", "roman_urdu": "Jism mein Dard"},
            {"id": "dizziness", "en": "Dizziness", "ur": "چکر", "roman_urdu": "Chakkar"},
            {"id": "breathing_difficulty", "en": "Breathing Difficulty", "ur": "سانس کی تکلیف", "roman_urdu": "Saans ki Takleef"},
            {"id": "chest_pain", "en": "Chest Pain", "ur": "سینے میں درد", "roman_urdu": "Seene mein Dard"},
        ]
    }


@router.get("/emergency-contacts")
async def get_emergency_contacts():
    """Get emergency contact numbers for Pakistan"""
    return {
        "country": "Pakistan",
        "contacts": [
            {"name": "Emergency (Rescue 1122)", "number": "1122", "description": "Ambulance, Fire, Rescue"},
            {"name": "Edhi Foundation", "number": "115", "description": "Ambulance service"},
            {"name": "Chippa Foundation", "number": "1021", "description": "Ambulance service"},
            {"name": "Police", "number": "15", "description": "Police emergency"},
            {"name": "Fire Brigade", "number": "16", "description": "Fire emergency"},
        ],
        "advice": {
            "en": "In case of emergency, call immediately. Do not delay seeking help.",
            "ur": "ایمرجنسی کی صورت میں فوری کال کریں۔ مدد لینے میں تاخیر نہ کریں۔"
        }
    }


# Background task for logging
async def log_analysis_request(
    session_id: str,
    symptoms: List[str],
    risk_level: str
):
    """Log analysis request for analytics (non-blocking)"""
    logger.info("Analysis logged",
               session_id=session_id,
               symptoms_count=len(symptoms),
               risk_level=risk_level)

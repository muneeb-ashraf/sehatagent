"""
Degraded/Offline Mode API Endpoints
Provides health guidance when cloud services are unavailable
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import structlog

from app.agents.fallback_agent import OfflineHelperAgent, OFFLINE_KNOWLEDGE_BASE
from app.agents.base_agent import AgentContext
from app.config import get_settings, MEDICAL_SAFETY_CONFIG
import uuid

logger = structlog.get_logger()
settings = get_settings()

router = APIRouter()

# Initialize offline agent
offline_agent = OfflineHelperAgent()


class OfflineHealthRequest(BaseModel):
    """Request for offline health analysis"""
    query: str = Field(..., min_length=3, max_length=1000)
    language: str = Field(default="en")
    symptoms: Optional[List[str]] = Field(default=None, description="Pre-identified symptoms")


class OfflineHealthResponse(BaseModel):
    """Response from offline health analysis"""
    success: bool
    mode: str = "offline"
    symptoms_identified: List[str]
    possible_conditions: List[str]
    recommendations: List[str]
    risk_level: str
    disclaimer: str
    limitations: str


class OfflineSymptomLookup(BaseModel):
    """Lookup specific symptom information"""
    symptom: str


@router.post("/analyze", response_model=OfflineHealthResponse)
async def offline_health_analysis(request: OfflineHealthRequest):
    """
    Analyze health query in offline/degraded mode
    
    Uses:
    - Rule-based symptom matching
    - Pre-loaded knowledge base
    - Local FAISS index (if available)
    
    No internet or cloud services required.
    """
    logger.info("Offline analysis request", 
               query_length=len(request.query),
               language=request.language)
    
    try:
        # Create context
        context = AgentContext(
            session_id=str(uuid.uuid4()),
            user_language=request.language,
            user_input=request.query,
            degraded_mode=True
        )
        
        # Process with offline agent
        context = await offline_agent.process(context)
        
        # Extract possible conditions from identified risks
        possible_conditions = []
        for risk in context.identified_risks:
            if "condition" in risk:
                possible_conditions.append(risk["condition"])
        
        # Determine risk level
        if context.is_emergency:
            risk_level = "CRITICAL"
        elif len(context.symptoms) > 3:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        # Get disclaimer
        disclaimer = MEDICAL_SAFETY_CONFIG["disclaimers"].get(
            request.language,
            MEDICAL_SAFETY_CONFIG["disclaimers"]["en"]
        )
        
        limitations_text = {
            "en": "Operating in offline mode with limited analysis capabilities. For comprehensive assessment, please use online mode or visit a healthcare facility.",
            "ur": "آف لائن موڈ میں محدود تجزیہ دستیاب ہے۔ مکمل جائزے کے لیے آن لائن ہوں یا ہسپتال جائیں۔",
            "roman_urdu": "Offline mode mein limited analysis hai. Complete check ke liye online aayein ya hospital jayein."
        }
        
        return OfflineHealthResponse(
            success=True,
            mode="offline",
            symptoms_identified=context.symptoms,
            possible_conditions=possible_conditions[:5],
            recommendations=context.recommendations,
            risk_level=risk_level,
            disclaimer=disclaimer,
            limitations=limitations_text.get(request.language, limitations_text["en"])
        )
        
    except Exception as e:
        logger.error("Offline analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/symptom/{symptom_name}")
async def get_offline_symptom_info(
    symptom_name: str,
    language: str = "en"
):
    """
    Get offline information about a specific symptom
    
    Returns cached knowledge about the symptom including:
    - Possible conditions
    - Basic recommendations
    - When to see a doctor
    """
    symptom_key = symptom_name.lower().replace(" ", "_")
    
    if symptom_key not in OFFLINE_KNOWLEDGE_BASE:
        # Try partial match
        matched_key = None
        for key in OFFLINE_KNOWLEDGE_BASE.keys():
            if symptom_key in key or key in symptom_key:
                matched_key = key
                break
        
        if not matched_key:
            return {
                "found": False,
                "symptom": symptom_name,
                "message": "Symptom not found in offline database",
                "suggestion": "Try common symptoms like: fever, headache, cough, diarrhea"
            }
        
        symptom_key = matched_key
    
    kb_entry = OFFLINE_KNOWLEDGE_BASE[symptom_key]
    
    # Get recommendations in requested language
    recommendations = kb_entry.get("recommendations", {}).get(
        language, 
        kb_entry.get("recommendations", {}).get("en", [])
    )
    
    return {
        "found": True,
        "symptom": symptom_key,
        "possible_conditions": kb_entry.get("possible_conditions", []),
        "recommendations": recommendations,
        "when_to_see_doctor": kb_entry.get("when_to_see_doctor", []),
        "severity_indicators": kb_entry.get("severity_indicators", {}),
        "mode": "offline"
    }


@router.get("/all-symptoms")
async def get_all_offline_symptoms(language: str = "en"):
    """
    Get list of all symptoms available in offline mode
    """
    symptoms = []
    
    for symptom_key, data in OFFLINE_KNOWLEDGE_BASE.items():
        symptoms.append({
            "id": symptom_key,
            "name": symptom_key.replace("_", " ").title(),
            "conditions_count": len(data.get("possible_conditions", [])),
            "has_recommendations": language in data.get("recommendations", {})
        })
    
    return {
        "mode": "offline",
        "symptoms_available": len(symptoms),
        "symptoms": symptoms
    }


@router.get("/emergency-check")
async def check_emergency_offline(query: str):
    """
    Quick emergency check using offline rules
    
    Checks for critical symptoms that require immediate attention
    """
    query_lower = query.lower()
    
    # Emergency keywords
    emergency_keywords = [
        "chest pain", "can't breathe", "breathing difficulty",
        "unconscious", "severe bleeding", "heart attack", "stroke",
        "seene mein dard", "saans nahi", "behosh",
        "سینے میں درد", "سانس نہیں", "بے ہوش"
    ]
    
    is_emergency = any(kw in query_lower for kw in emergency_keywords)
    
    if is_emergency:
        return {
            "is_emergency": True,
            "action": "SEEK_IMMEDIATE_HELP",
            "message": {
                "en": "⚠️ EMERGENCY: Please call 1122 or go to nearest hospital immediately!",
                "ur": "⚠️ ایمرجنسی: فوری 1122 کال کریں یا قریبی ہسپتال جائیں!",
                "roman_urdu": "⚠️ EMERGENCY: Fori 1122 call karein ya hospital jayein!"
            },
            "emergency_numbers": {
                "rescue": "1122",
                "edhi": "115"
            }
        }
    
    return {
        "is_emergency": False,
        "message": "No immediate emergency detected. You can proceed with symptom analysis."
    }


@router.get("/first-aid/{condition}")
async def get_first_aid_info(condition: str, language: str = "en"):
    """
    Get basic first aid information for common conditions
    
    Available offline for emergency reference
    """
    first_aid_db = {
        "fever": {
            "en": [
                "Rest in a cool, comfortable place",
                "Remove excess clothing",
                "Apply cool compress to forehead",
                "Drink plenty of fluids (water, ORS)",
                "Take paracetamol if temperature above 100°F",
                "Seek medical help if fever exceeds 103°F"
            ],
            "ur": [
                "ٹھنڈی آرام دہ جگہ پر لیٹیں",
                "زائد کپڑے اتاریں",
                "ماتھے پر ٹھنڈا کپڑا رکھیں",
                "خوب پانی اور نمکول پیں",
                "100°F سے اوپر ہو تو پیراسیٹامول لیں",
                "103°F سے اوپر ہو تو ڈاکٹر کو دکھائیں"
            ]
        },
        "burns": {
            "en": [
                "Cool the burn under running water for 10-20 minutes",
                "Do NOT apply ice, butter, or toothpaste",
                "Cover with clean, non-fluffy material",
                "Do not break blisters",
                "Seek medical help for severe burns"
            ],
            "ur": [
                "جلے ہوئے حصے کو 10-20 منٹ ٹھنڈے پانی میں رکھیں",
                "برف، مکھن یا ٹوتھ پیسٹ نہ لگائیں",
                "صاف کپڑے سے ڈھانپیں",
                "چھالے نہ پھوڑیں",
                "شدید جلنے پر ڈاکٹر کو دکھائیں"
            ]
        },
        "choking": {
            "en": [
                "Encourage coughing if person can breathe",
                "Give 5 back blows between shoulder blades",
                "Give 5 abdominal thrusts (Heimlich maneuver)",
                "Repeat until object is expelled",
                "Call emergency if person becomes unconscious"
            ]
        },
        "bleeding": {
            "en": [
                "Apply direct pressure with clean cloth",
                "Keep the injured part elevated",
                "Do not remove cloth if blood soaks through - add more",
                "Apply pressure for at least 10 minutes",
                "Seek medical help for severe bleeding"
            ],
            "ur": [
                "صاف کپڑے سے زخم پر دبائیں",
                "زخمی حصے کو اونچا رکھیں",
                "اگر خون رس جائے تو اوپر اور کپڑا رکھیں",
                "کم از کم 10 منٹ دبا کر رکھیں",
                "شدید خون بہنے پر ڈاکٹر کو دکھائیں"
            ]
        }
    }
    
    condition_key = condition.lower().replace(" ", "_")
    
    if condition_key not in first_aid_db:
        return {
            "found": False,
            "condition": condition,
            "available_conditions": list(first_aid_db.keys())
        }
    
    info = first_aid_db[condition_key]
    steps = info.get(language, info.get("en", []))
    
    return {
        "found": True,
        "condition": condition,
        "first_aid_steps": steps,
        "important": "This is basic first aid. Always seek professional medical help for serious conditions.",
        "emergency_number": "1122"
    }


@router.get("/status")
async def get_offline_status():
    """
    Get offline mode status and capabilities
    """
    return {
        "mode": "offline",
        "status": "operational",
        "capabilities": {
            "symptom_analysis": True,
            "emergency_detection": True,
            "first_aid_info": True,
            "basic_recommendations": True,
            "voice_input": False,
            "llm_analysis": False,
            "personalized_recommendations": False
        },
        "knowledge_base": {
            "symptoms": len(OFFLINE_KNOWLEDGE_BASE),
            "languages": ["en", "ur", "roman_urdu"]
        },
        "limitations": [
            "No AI-powered analysis",
            "Limited to pre-defined symptoms",
            "No personalization",
            "No voice input"
        ]
    }

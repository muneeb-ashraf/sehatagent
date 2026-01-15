"""
Healthcare Worker Dashboard API
Endpoints for healthcare professionals to view summarized insights
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import structlog

from app.agents.orchestrator import AgentOrchestrator
from app.database.crud import get_session_insights, get_aggregated_stats
from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

router = APIRouter()


# Models
class PatientSummary(BaseModel):
    """Summary of a patient consultation"""
    session_id: str
    timestamp: datetime
    symptoms: List[str]
    risk_level: str
    primary_concern: str
    recommendations_given: int
    follow_up_needed: bool


class AggregatedInsights(BaseModel):
    """Aggregated health insights for healthcare workers"""
    period: str
    total_consultations: int
    common_symptoms: List[Dict[str, Any]]
    risk_distribution: Dict[str, int]
    urgent_cases: int
    common_conditions: List[Dict[str, Any]]
    nutrition_deficiencies: List[Dict[str, Any]]
    recommendations_summary: Dict[str, Any]


class CommunityHealthReport(BaseModel):
    """Community-level health report"""
    generated_at: datetime
    area: Optional[str]
    total_consultations: int
    top_symptoms: List[Dict[str, Any]]
    disease_trends: List[Dict[str, Any]]
    at_risk_population: Dict[str, Any]
    recommended_interventions: List[str]


class WorkerDashboardResponse(BaseModel):
    """Complete dashboard response for healthcare workers"""
    summary: AggregatedInsights
    recent_consultations: List[PatientSummary]
    alerts: List[Dict[str, Any]]
    action_items: List[str]


async def get_orchestrator():
    """Get agent orchestrator"""
    from app.main import orchestrator
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="System initializing")
    return orchestrator


@router.get("/dashboard", response_model=WorkerDashboardResponse)
async def get_worker_dashboard(
    period: str = Query(default="today", description="Time period: today, week, month"),
    area: Optional[str] = Query(default=None, description="Filter by area/region")
):
    """
    Get healthcare worker dashboard with aggregated insights
    
    Provides:
    - Summary statistics
    - Common symptoms and conditions
    - Risk distribution
    - Urgent cases requiring attention
    - Recommended interventions
    """
    logger.info("Worker dashboard request", period=period, area=area)
    
    try:
        # Calculate date range
        now = datetime.utcnow()
        if period == "today":
            start_date = now.replace(hour=0, minute=0, second=0)
        elif period == "week":
            start_date = now - timedelta(days=7)
        elif period == "month":
            start_date = now - timedelta(days=30)
        else:
            start_date = now - timedelta(days=1)
        
        # Get aggregated insights (mock data for demo)
        # In production, this would query the database
        summary = AggregatedInsights(
            period=period,
            total_consultations=127,
            common_symptoms=[
                {"symptom": "fever", "count": 45, "percentage": 35.4},
                {"symptom": "cough", "count": 38, "percentage": 29.9},
                {"symptom": "headache", "count": 32, "percentage": 25.2},
                {"symptom": "fatigue", "count": 28, "percentage": 22.0},
                {"symptom": "diarrhea", "count": 21, "percentage": 16.5},
            ],
            risk_distribution={
                "LOW": 65,
                "MEDIUM": 42,
                "HIGH": 18,
                "CRITICAL": 2
            },
            urgent_cases=20,
            common_conditions=[
                {"condition": "Viral Fever", "count": 34},
                {"condition": "Respiratory Infection", "count": 28},
                {"condition": "Gastroenteritis", "count": 19},
                {"condition": "Anemia (suspected)", "count": 15},
                {"condition": "Dengue (suspected)", "count": 8},
            ],
            nutrition_deficiencies=[
                {"deficiency": "Iron Deficiency", "count": 23, "at_risk": "Women, Children"},
                {"deficiency": "Vitamin D Deficiency", "count": 18, "at_risk": "Indoor workers"},
                {"deficiency": "Protein Deficiency", "count": 12, "at_risk": "Low-income families"},
            ],
            recommendations_summary={
                "doctor_referrals": 20,
                "self_care_advised": 89,
                "nutrition_guidance": 45,
                "emergency_referrals": 2
            }
        )
        
        # Recent consultations (mock data)
        recent = [
            PatientSummary(
                session_id="sess_001",
                timestamp=datetime.utcnow() - timedelta(hours=1),
                symptoms=["fever", "headache", "body_aches"],
                risk_level="HIGH",
                primary_concern="Suspected Dengue",
                recommendations_given=5,
                follow_up_needed=True
            ),
            PatientSummary(
                session_id="sess_002",
                timestamp=datetime.utcnow() - timedelta(hours=2),
                symptoms=["fatigue", "dizziness"],
                risk_level="MEDIUM",
                primary_concern="Possible Anemia",
                recommendations_given=4,
                follow_up_needed=True
            ),
            PatientSummary(
                session_id="sess_003",
                timestamp=datetime.utcnow() - timedelta(hours=3),
                symptoms=["cough", "cold"],
                risk_level="LOW",
                primary_concern="Common Cold",
                recommendations_given=3,
                follow_up_needed=False
            ),
        ]
        
        # Alerts
        alerts = [
            {
                "type": "outbreak_warning",
                "severity": "high",
                "message": "Increased dengue cases detected in the area",
                "action": "Advise mosquito precautions to all patients"
            },
            {
                "type": "nutrition_alert",
                "severity": "medium", 
                "message": "High prevalence of iron deficiency among women",
                "action": "Recommend iron-rich foods and supplements"
            }
        ]
        
        # Action items
        action_items = [
            "Follow up with 2 high-risk dengue suspected cases",
            "Review 18 cases marked for doctor referral",
            "Community awareness needed for nutrition deficiencies",
            "Check on 5 patients who didn't respond to self-care advice"
        ]
        
        return WorkerDashboardResponse(
            summary=summary,
            recent_consultations=recent,
            alerts=alerts,
            action_items=action_items
        )
        
    except Exception as e:
        logger.error("Dashboard generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights/{session_id}")
async def get_session_details(session_id: str):
    """
    Get detailed insights for a specific consultation session
    
    Includes full agent reasoning and decision trace
    """
    # In production, fetch from database
    return {
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat(),
        "patient_query": "Sample query",
        "detected_language": "ur",
        "symptoms_identified": ["fever", "headache"],
        "agent_decisions": [
            {
                "agent": "SymptomAnalyzer",
                "decision": "Identified 2 symptoms",
                "confidence": 0.85
            },
            {
                "agent": "RiskAssessor",
                "decision": "Medium risk - possible viral infection",
                "confidence": 0.78
            }
        ],
        "recommendations_given": [
            "Rest and hydration",
            "Paracetamol for fever",
            "See doctor if symptoms persist"
        ],
        "risk_level": "MEDIUM",
        "follow_up_status": "pending"
    }


@router.get("/community-report", response_model=CommunityHealthReport)
async def get_community_health_report(
    area: Optional[str] = None,
    days: int = Query(default=7, ge=1, le=30)
):
    """
    Generate community-level health report
    
    Useful for:
    - Lady Health Workers (LHWs)
    - Community health centers
    - Public health planning
    """
    return CommunityHealthReport(
        generated_at=datetime.utcnow(),
        area=area or "All Areas",
        total_consultations=523,
        top_symptoms=[
            {"symptom": "Fever", "count": 156, "trend": "increasing"},
            {"symptom": "Respiratory issues", "count": 134, "trend": "stable"},
            {"symptom": "Gastrointestinal", "count": 98, "trend": "decreasing"},
        ],
        disease_trends=[
            {"disease": "Viral Fever", "cases": 89, "trend": "seasonal_peak"},
            {"disease": "Dengue", "cases": 23, "trend": "increasing"},
            {"disease": "Typhoid", "cases": 15, "trend": "stable"},
        ],
        at_risk_population={
            "children_under_5": {"count": 45, "common_issues": ["fever", "diarrhea"]},
            "pregnant_women": {"count": 28, "common_issues": ["anemia", "fatigue"]},
            "elderly": {"count": 34, "common_issues": ["hypertension", "diabetes"]}
        },
        recommended_interventions=[
            "Dengue awareness campaign needed",
            "Iron supplementation program for women",
            "Clean water access improvement",
            "Vaccination drive for children"
        ]
    )


@router.post("/flag-case")
async def flag_case_for_review(
    session_id: str,
    reason: str,
    priority: str = "normal"
):
    """
    Flag a case for healthcare worker review
    """
    logger.info("Case flagged", session_id=session_id, reason=reason, priority=priority)
    
    return {
        "success": True,
        "message": f"Case {session_id} flagged for review",
        "priority": priority,
        "flagged_at": datetime.utcnow().isoformat()
    }


@router.get("/export")
async def export_insights(
    format: str = Query(default="json", description="Export format: json, csv"),
    period: str = Query(default="week")
):
    """
    Export aggregated insights for reporting
    """
    # Generate export data
    export_data = {
        "export_date": datetime.utcnow().isoformat(),
        "period": period,
        "format": format,
        "data": {
            "total_consultations": 523,
            "risk_summary": {"low": 312, "medium": 156, "high": 48, "critical": 7},
            "top_conditions": ["Viral Fever", "Respiratory Infection", "Gastroenteritis"],
            "referrals_made": 55
        }
    }
    
    return export_data

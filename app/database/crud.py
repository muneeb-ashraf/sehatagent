"""
Database CRUD Operations
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import structlog

from app.database.models import (
    HealthSession, AgentLog, SessionFeedback, 
    CachedResponse, AggregatedStats
)

logger = structlog.get_logger()


# ============ Health Sessions ============

async def create_health_session(
    session: AsyncSession,
    session_id: str,
    language: str,
    mode: str,
    symptoms_count: int,
    symptoms_categories: List[str],
    risk_level: str,
    agents_used: List[str],
    processing_time: float,
    recommendations_count: int,
    doctor_referral: bool,
    is_emergency: bool
) -> HealthSession:
    """Create a new health session record"""
    
    health_session = HealthSession(
        id=session_id,
        language=language,
        mode=mode,
        symptoms_count=symptoms_count,
        symptoms_categories=symptoms_categories,
        risk_level=risk_level,
        agents_used=agents_used,
        processing_time=processing_time,
        recommendations_count=recommendations_count,
        doctor_referral=doctor_referral,
        is_emergency=is_emergency
    )
    
    session.add(health_session)
    await session.commit()
    await session.refresh(health_session)
    
    return health_session


async def get_health_session(
    session: AsyncSession,
    session_id: str
) -> Optional[HealthSession]:
    """Get a health session by ID"""
    
    result = await session.execute(
        select(HealthSession)
        .options(selectinload(HealthSession.agent_logs))
        .where(HealthSession.id == session_id)
    )
    
    return result.scalar_one_or_none()


async def get_recent_sessions(
    session: AsyncSession,
    limit: int = 10,
    offset: int = 0
) -> List[HealthSession]:
    """Get recent health sessions"""
    
    result = await session.execute(
        select(HealthSession)
        .order_by(HealthSession.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    
    return result.scalars().all()


# ============ Agent Logs ============

async def create_agent_log(
    session: AsyncSession,
    session_id: str,
    agent_name: str,
    agent_role: str,
    decision: str,
    reasoning: str,
    confidence: float,
    inputs_summary: List[str]
) -> AgentLog:
    """Create an agent decision log"""
    
    agent_log = AgentLog(
        session_id=session_id,
        agent_name=agent_name,
        agent_role=agent_role,
        decision=decision,
        reasoning=reasoning,
        confidence=confidence,
        inputs_summary=inputs_summary
    )
    
    session.add(agent_log)
    await session.commit()
    
    return agent_log


async def get_session_agent_logs(
    session: AsyncSession,
    session_id: str
) -> List[AgentLog]:
    """Get all agent logs for a session"""
    
    result = await session.execute(
        select(AgentLog)
        .where(AgentLog.session_id == session_id)
        .order_by(AgentLog.created_at)
    )
    
    return result.scalars().all()


# ============ Feedback ============

async def create_feedback(
    session: AsyncSession,
    session_id: str,
    helpful: bool,
    rating: int,
    feedback_text: Optional[str] = None
) -> SessionFeedback:
    """Create feedback for a session"""
    
    feedback = SessionFeedback(
        session_id=session_id,
        helpful=helpful,
        rating=rating,
        feedback_text=feedback_text
    )
    
    session.add(feedback)
    await session.commit()
    
    return feedback


# ============ Cache ============

async def get_cached_response(
    session: AsyncSession,
    cache_key: str
) -> Optional[Dict[str, Any]]:
    """Get cached response if not expired"""
    
    result = await session.execute(
        select(CachedResponse)
        .where(
            and_(
                CachedResponse.cache_key == cache_key,
                CachedResponse.expires_at > datetime.utcnow()
            )
        )
    )
    
    cached = result.scalar_one_or_none()
    
    if cached:
        # Update hit count
        cached.hit_count += 1
        await session.commit()
        return cached.response_data
    
    return None


async def set_cached_response(
    session: AsyncSession,
    cache_key: str,
    query_pattern: str,
    language: str,
    response_data: Dict[str, Any],
    ttl_hours: int = 24
) -> CachedResponse:
    """Cache a response"""
    
    cached = CachedResponse(
        cache_key=cache_key,
        query_pattern=query_pattern,
        language=language,
        response_data=response_data,
        expires_at=datetime.utcnow() + timedelta(hours=ttl_hours)
    )
    
    session.add(cached)
    await session.commit()
    
    return cached


# ============ Statistics ============

async def get_aggregated_stats(
    session: AsyncSession,
    period: str = "daily",
    days: int = 7
) -> List[AggregatedStats]:
    """Get aggregated statistics"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    result = await session.execute(
        select(AggregatedStats)
        .where(
            and_(
                AggregatedStats.period == period,
                AggregatedStats.date >= start_date
            )
        )
        .order_by(AggregatedStats.date.desc())
    )
    
    return result.scalars().all()


async def get_session_insights(
    session: AsyncSession,
    start_date: datetime,
    end_date: datetime
) -> Dict[str, Any]:
    """Get insights for a date range"""
    
    # Total consultations
    total_result = await session.execute(
        select(func.count(HealthSession.id))
        .where(
            and_(
                HealthSession.created_at >= start_date,
                HealthSession.created_at <= end_date
            )
        )
    )
    total = total_result.scalar()
    
    # Risk distribution
    risk_result = await session.execute(
        select(
            HealthSession.risk_level,
            func.count(HealthSession.id)
        )
        .where(
            and_(
                HealthSession.created_at >= start_date,
                HealthSession.created_at <= end_date
            )
        )
        .group_by(HealthSession.risk_level)
    )
    
    risk_distribution = {row[0]: row[1] for row in risk_result}
    
    # Emergency count
    emergency_result = await session.execute(
        select(func.count(HealthSession.id))
        .where(
            and_(
                HealthSession.created_at >= start_date,
                HealthSession.created_at <= end_date,
                HealthSession.is_emergency == True
            )
        )
    )
    emergency_count = emergency_result.scalar()
    
    return {
        "total_consultations": total,
        "risk_distribution": risk_distribution,
        "emergency_count": emergency_count,
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        }
    }

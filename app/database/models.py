"""
Database Models
SQLAlchemy models for PostgreSQL
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database.connection import Base


def generate_uuid():
    return str(uuid.uuid4())


class HealthSession(Base):
    """
    Stores health consultation sessions
    
    Note: Does NOT store raw medical data per competition rules
    Only stores summarized/anonymized information
    """
    __tablename__ = "health_sessions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Session metadata
    language = Column(String(10), default="en")
    mode = Column(String(20), default="full")  # full or degraded
    
    # Summarized analysis (no raw health data)
    symptoms_count = Column(Integer, default=0)
    symptoms_categories = Column(JSON, default=list)  # e.g., ["respiratory", "digestive"]
    risk_level = Column(String(20))
    
    # Agent information
    agents_used = Column(JSON, default=list)
    processing_time = Column(Float)
    
    # Outcome
    recommendations_count = Column(Integer, default=0)
    doctor_referral = Column(Boolean, default=False)
    is_emergency = Column(Boolean, default=False)
    
    # Relationships
    agent_logs = relationship("AgentLog", back_populates="session")
    feedback = relationship("SessionFeedback", back_populates="session", uselist=False)


class AgentLog(Base):
    """
    Stores agent decision logs for explainability
    """
    __tablename__ = "agent_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("health_sessions.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Agent info
    agent_name = Column(String(50))
    agent_role = Column(String(50))
    
    # Decision
    decision = Column(String(500))
    reasoning = Column(Text)
    confidence = Column(Float)
    
    # Inputs used (without actual data)
    inputs_summary = Column(JSON, default=list)
    
    # Relationship
    session = relationship("HealthSession", back_populates="agent_logs")


class SessionFeedback(Base):
    """
    Stores user feedback on consultations
    """
    __tablename__ = "session_feedback"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("health_sessions.id"), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Feedback
    helpful = Column(Boolean)
    rating = Column(Integer)  # 1-5
    feedback_text = Column(Text, nullable=True)
    
    # Outcome tracking
    followed_recommendations = Column(Boolean, nullable=True)
    visited_doctor = Column(Boolean, nullable=True)
    
    # Relationship
    session = relationship("HealthSession", back_populates="feedback")


class CachedResponse(Base):
    """
    Caches common responses for faster serving
    """
    __tablename__ = "cached_responses"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    # Cache key (hashed query pattern)
    cache_key = Column(String(64), unique=True, index=True)
    query_pattern = Column(String(200))
    language = Column(String(10))
    
    # Cached data
    response_data = Column(JSON)
    hit_count = Column(Integer, default=0)


class AggregatedStats(Base):
    """
    Stores aggregated statistics for healthcare worker dashboard
    """
    __tablename__ = "aggregated_stats"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    date = Column(DateTime, index=True)
    period = Column(String(20))  # daily, weekly, monthly
    area = Column(String(100), nullable=True)
    
    # Aggregated counts
    total_consultations = Column(Integer, default=0)
    emergency_count = Column(Integer, default=0)
    doctor_referrals = Column(Integer, default=0)
    
    # Risk distribution
    risk_distribution = Column(JSON, default=dict)
    
    # Common symptoms (anonymized)
    top_symptom_categories = Column(JSON, default=list)
    
    # Common conditions
    top_conditions = Column(JSON, default=list)

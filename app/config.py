"""
SehatAgent Configuration
All configuration settings for the multi-agent health system
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "SehatAgent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # GCP Configuration
    GCP_PROJECT_ID: str = ""
    GCP_REGION: str = "us-central1"
    
    # Vertex AI
    VERTEX_AI_LOCATION: str = "us-central1"
    VERTEX_AI_MODEL: str = "gemini-1.5-pro"  # or gemini-1.5-flash for faster responses
    VERTEX_AI_EMBEDDING_MODEL: str = "textembedding-gecko@003"
    
    # Cloud SQL (PostgreSQL)
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "sehatagent"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_INSTANCE_CONNECTION_NAME: Optional[str] = None  # For Cloud Run
    
    # Speech-to-Text
    SPEECH_LANGUAGE_CODES: list = ["ur-PK", "pa-IN", "en-US", "ur-IN"]
    
    # FAISS Configuration
    FAISS_INDEX_PATH: str = "./data/faiss_index"
    FAISS_DIMENSION: int = 768  # Embedding dimension
    
    # Degraded Mode
    ENABLE_DEGRADED_MODE: bool = True
    DEGRADED_MODE_TIMEOUT: int = 5  # seconds before falling back
    
    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE: int = 60
    
    # Supported Languages
    SUPPORTED_LANGUAGES: list = ["en", "ur", "pa", "roman_urdu"]
    
    @property
    def database_url(self) -> str:
        """Construct database URL"""
        if self.DB_INSTANCE_CONNECTION_NAME:
            # Cloud Run with Unix socket
            return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@/{self.DB_NAME}?host=/cloudsql/{self.DB_INSTANCE_CONNECTION_NAME}"
        else:
            # Direct connection (local development)
            return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def sync_database_url(self) -> str:
        """Construct sync database URL for migrations (using psycopg3)"""
        if self.DB_INSTANCE_CONNECTION_NAME:
            return f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASSWORD}@/{self.DB_NAME}?host=/cloudsql/{self.DB_INSTANCE_CONNECTION_NAME}"
        else:
            return f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Agent Configuration
AGENT_CONFIG = {
    "symptom_agent": {
        "name": "SymptomAnalyzer",
        "description": "Analyzes symptoms and health indicators",
        "temperature": 0.3,  # Lower for more consistent medical analysis
        "max_tokens": 1024,
    },
    "risk_agent": {
        "name": "RiskAssessor",
        "description": "Identifies health and nutrition risks",
        "temperature": 0.2,
        "max_tokens": 1024,
    },
    "recommendation_agent": {
        "name": "HealthAdvisor",
        "description": "Provides preventive guidance in simple language",
        "temperature": 0.4,
        "max_tokens": 2048,
    },
    "safety_agent": {
        "name": "SafetyGuard",
        "description": "Ensures ethical and safe recommendations",
        "temperature": 0.1,
        "max_tokens": 512,
    },
    "fallback_agent": {
        "name": "OfflineHelper",
        "description": "Provides rule-based guidance when AI unavailable",
        "uses_llm": False,
    },
}


# Medical Safety Configuration
MEDICAL_SAFETY_CONFIG = {
    # Symptoms that require immediate medical attention
    "emergency_symptoms": [
        "chest pain", "breathing difficulty", "unconscious",
        "severe bleeding", "stroke symptoms", "heart attack",
        "سینے میں درد", "سانس لینے میں تکلیف", "بےہوشی",
    ],
    
    # Maximum severity level before referring to doctor
    "max_self_care_severity": 5,  # Scale of 1-10
    
    # Disclaimer languages
    "disclaimers": {
        "en": "This is not medical advice. Please consult a healthcare professional for proper diagnosis.",
        "ur": "یہ طبی مشورہ نہیں ہے۔ براہ کرم صحیح تشخیص کے لیے ڈاکٹر سے مشورہ کریں۔",
        "roman_urdu": "Yeh medical advice nahi hai. Doctor se zaroor milein.",
    }
}


# Nutrition Configuration (Pakistan-specific)
NUTRITION_CONFIG = {
    "common_deficiencies_pakistan": [
        "iron", "vitamin_d", "vitamin_b12", "iodine", "zinc"
    ],
    "local_foods": {
        "iron_rich": ["palak", "chana", "gur", "kaleji"],
        "vitamin_d": ["machli", "anda", "doodh"],
        "protein": ["daal", "gosht", "murgi", "machli"],
    }
}

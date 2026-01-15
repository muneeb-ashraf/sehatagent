"""
SehatAgent Tests
Basic tests for the multi-agent health system
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test health analysis endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns system info"""
        # Import here to avoid issues if app isn't fully configured
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "SehatAgent" in data["name"]
    
    def test_health_check(self):
        """Test health check endpoint"""
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/health")
        assert response.status_code == 200


class TestOfflineMode:
    """Test offline/degraded mode functionality"""
    
    def test_offline_symptom_lookup(self):
        """Test offline symptom database"""
        from app.agents.fallback_agent import OFFLINE_KNOWLEDGE_BASE
        
        # Check that knowledge base has essential symptoms
        assert "fever" in OFFLINE_KNOWLEDGE_BASE
        assert "headache" in OFFLINE_KNOWLEDGE_BASE
        assert "diarrhea" in OFFLINE_KNOWLEDGE_BASE
    
    def test_offline_recommendations_multilingual(self):
        """Test that offline recommendations exist in multiple languages"""
        from app.agents.fallback_agent import OFFLINE_KNOWLEDGE_BASE
        
        fever_data = OFFLINE_KNOWLEDGE_BASE["fever"]
        assert "en" in fever_data["recommendations"]
        assert "ur" in fever_data["recommendations"]


class TestLanguageService:
    """Test language detection and processing"""
    
    def test_urdu_detection(self):
        """Test Urdu script detection"""
        from app.services.language_service import LanguageService
        
        service = LanguageService()
        
        # Test Urdu script
        result = service.detect_language("مجھے بخار ہے")
        assert result == "ur"
    
    def test_roman_urdu_detection(self):
        """Test Roman Urdu detection"""
        from app.services.language_service import LanguageService
        
        service = LanguageService()
        
        # Test Roman Urdu
        result = service.detect_language("mujhe bukhar hai aur sir mein dard hai")
        assert result == "roman_urdu"
    
    def test_english_detection(self):
        """Test English detection"""
        from app.services.language_service import LanguageService
        
        service = LanguageService()
        
        result = service.detect_language("I have a headache and fever")
        assert result == "en"


class TestSymptomPatterns:
    """Test symptom pattern matching"""
    
    def test_symptom_patterns_exist(self):
        """Test that symptom patterns are defined"""
        from app.agents.symptom_agent import SYMPTOM_PATTERNS
        
        # Check essential symptoms
        assert "fever" in SYMPTOM_PATTERNS
        assert "headache" in SYMPTOM_PATTERNS
        assert "cough" in SYMPTOM_PATTERNS
    
    def test_multilingual_patterns(self):
        """Test that patterns include Urdu and Roman Urdu"""
        from app.agents.symptom_agent import SYMPTOM_PATTERNS
        
        fever_patterns = SYMPTOM_PATTERNS["fever"]
        
        # Should have English, Urdu, and Roman Urdu
        assert "fever" in fever_patterns
        assert "bukhar" in fever_patterns
        assert "بخار" in fever_patterns


class TestSafetyAgent:
    """Test safety and emergency detection"""
    
    def test_emergency_keywords_exist(self):
        """Test emergency keywords are defined"""
        from app.agents.safety_agent import EMERGENCY_SYMPTOMS
        
        # Check critical symptoms
        assert "chest pain" in EMERGENCY_SYMPTOMS
        assert "unconscious" in EMERGENCY_SYMPTOMS
    
    def test_emergency_keywords_multilingual(self):
        """Test emergency keywords in multiple languages"""
        from app.agents.safety_agent import EMERGENCY_SYMPTOMS
        
        # Urdu emergency keywords
        assert "سینے میں درد" in EMERGENCY_SYMPTOMS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

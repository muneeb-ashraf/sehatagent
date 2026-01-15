"""
Agent Orchestrator
Coordinates all agents in the multi-agent health system
"""

from typing import Dict, List, Optional, Any
import asyncio
import structlog
from datetime import datetime
import uuid

from app.agents.base_agent import (
    BaseAgent, AgentContext, AgentRole, AgentDecision, AgentMessage
)
from app.agents.symptom_agent import SymptomAnalyzerAgent
from app.agents.risk_agent import RiskAssessorAgent
from app.agents.recommendation_agent import HealthAdvisorAgent
from app.agents.safety_agent import SafetyGuardAgent
from app.agents.fallback_agent import OfflineHelperAgent
from app.services.vertex_ai import VertexAIService
from app.services.rag_service import RAGService
from app.services.language_service import LanguageService
from app.config import get_settings, MEDICAL_SAFETY_CONFIG

logger = structlog.get_logger()
settings = get_settings()


class AgentOrchestrator:
    """
    Orchestrates the multi-agent system
    
    Agent Flow:
    1. Language Detection & Translation
    2. Safety Agent (pre-check for emergencies)
    3. Symptom Analyzer (analyze symptoms)
    4. Risk Assessor (identify risks)
    5. Health Advisor (generate recommendations)
    6. Safety Agent (post-check on recommendations)
    
    Falls back to Offline Helper if Vertex AI unavailable
    """
    
    def __init__(self, rag_service: RAGService):
        self.rag = rag_service
        self.vertex_ai: Optional[VertexAIService] = None
        self.language_service = LanguageService()
        self.agents: Dict[AgentRole, BaseAgent] = {}
        self.is_initialized = False
        self.message_queue: List[AgentMessage] = []
        self.logger = logger.bind(component="orchestrator")
    
    async def initialize(self):
        """Initialize all agents and services"""
        self.logger.info("Initializing orchestrator")
        
        # Initialize Vertex AI service
        try:
            self.vertex_ai = VertexAIService()
            await self.vertex_ai.initialize()
            self.logger.info("Vertex AI service initialized")
        except Exception as e:
            self.logger.warning("Vertex AI initialization failed, degraded mode enabled", error=str(e))
            self.vertex_ai = None
        
        # Initialize agents
        self.agents = {
            AgentRole.SYMPTOM_ANALYZER: SymptomAnalyzerAgent(
                vertex_ai_service=self.vertex_ai,
                rag_service=self.rag
            ),
            AgentRole.RISK_ASSESSOR: RiskAssessorAgent(
                vertex_ai_service=self.vertex_ai,
                rag_service=self.rag
            ),
            AgentRole.HEALTH_ADVISOR: HealthAdvisorAgent(
                vertex_ai_service=self.vertex_ai,
                rag_service=self.rag
            ),
            AgentRole.SAFETY_GUARD: SafetyGuardAgent(
                vertex_ai_service=self.vertex_ai,
                rag_service=self.rag
            ),
            AgentRole.OFFLINE_HELPER: OfflineHelperAgent(
                rag_service=self.rag
            ),
        }
        
        # Initialize each agent
        for role, agent in self.agents.items():
            await agent.initialize()
        
        self.is_initialized = True
        self.logger.info("Orchestrator initialization complete", 
                        agents_count=len(self.agents),
                        vertex_ai_available=self.vertex_ai is not None)
    
    async def check_vertex_ai_health(self) -> bool:
        """Check if Vertex AI is available"""
        if self.vertex_ai is None:
            return False
        try:
            return await self.vertex_ai.health_check()
        except:
            return False
    
    async def process_health_query(
        self,
        user_input: str,
        user_language: str = "auto",
        session_id: str = None,
        include_voice: bool = False,
        audio_data: bytes = None
    ) -> Dict[str, Any]:
        """
        Main entry point for processing health queries
        
        Args:
            user_input: User's health query (text)
            user_language: Language code or 'auto' for detection
            session_id: Optional session ID for tracking
            include_voice: Whether input was from voice
            audio_data: Raw audio if voice input
            
        Returns:
            Complete response with analysis, risks, recommendations, and explanations
        """
        start_time = datetime.utcnow()
        session_id = session_id or str(uuid.uuid4())
        
        self.logger.info("Processing health query", 
                        session_id=session_id,
                        input_length=len(user_input),
                        language=user_language)
        
        # Step 1: Detect and process language
        if user_language == "auto":
            detected_lang = self.language_service.detect_language(user_input)
            user_language = detected_lang
        
        # Translate to English for processing if needed
        translated_input = user_input
        if user_language != "en":
            translated_input = await self.language_service.translate_to_english(user_input)
        
        # Create context
        context = AgentContext(
            session_id=session_id,
            user_language=user_language,
            user_input=user_input,
            translated_input=translated_input,
            degraded_mode=self.vertex_ai is None
        )
        
        # Step 2: Check if we need degraded mode
        if context.degraded_mode or not await self.check_vertex_ai_health():
            self.logger.info("Using degraded mode", session_id=session_id)
            return await self._process_degraded(context)
        
        # Step 3: Safety pre-check for emergencies
        safety_agent = self.agents[AgentRole.SAFETY_GUARD]
        context = await safety_agent.process(context)
        
        if context.is_emergency:
            return self._build_emergency_response(context)
        
        # Step 4: Run main agent pipeline
        try:
            # Symptom Analysis
            symptom_agent = self.agents[AgentRole.SYMPTOM_ANALYZER]
            context = await symptom_agent.process(context)
            
            # Risk Assessment
            risk_agent = self.agents[AgentRole.RISK_ASSESSOR]
            context = await risk_agent.process(context)
            
            # Generate Recommendations
            advisor_agent = self.agents[AgentRole.HEALTH_ADVISOR]
            context = await advisor_agent.process(context)
            
            # Safety post-check on recommendations
            context = await safety_agent.validate_recommendations(context)
            
        except Exception as e:
            self.logger.error("Agent pipeline failed, falling back", error=str(e))
            return await self._process_degraded(context)
        
        # Step 5: Build response
        response = self._build_response(context, start_time)
        
        return response
    
    async def _process_degraded(self, context: AgentContext) -> Dict[str, Any]:
        """Process using offline/degraded mode"""
        context.degraded_mode = True
        
        fallback_agent = self.agents[AgentRole.OFFLINE_HELPER]
        context = await fallback_agent.process(context)
        
        return self._build_response(context, datetime.utcnow())
    
    def _build_response(
        self,
        context: AgentContext,
        start_time: datetime
    ) -> Dict[str, Any]:
        """Build the final response object"""
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Generate explanations in user's language
        explanations = self._generate_explanations(context)
        
        # Get disclaimer in user's language
        disclaimer = MEDICAL_SAFETY_CONFIG["disclaimers"].get(
            context.user_language, 
            MEDICAL_SAFETY_CONFIG["disclaimers"]["en"]
        )
        
        response = {
            "success": True,
            "session_id": context.session_id,
            "mode": "degraded" if context.degraded_mode else "full",
            "language": context.user_language,
            
            # Main Results
            "analysis": {
                "symptoms_identified": context.symptoms,
                "health_indicators": context.health_indicators,
                "original_input": context.user_input,
            },
            
            "risks": {
                "identified_risks": context.identified_risks,
                "risk_level": self._calculate_overall_risk(context),
                "safety_flags": context.safety_flags,
            },
            
            "recommendations": {
                "preventive_guidance": context.recommendations,
                "in_simple_language": self._simplify_recommendations(context),
            },
            
            # Explainability
            "explanation": {
                "summary": explanations["summary"],
                "agent_reasoning": explanations["agent_reasoning"],
                "decision_trace": [d.dict() for d in context.decisions],
            },
            
            # Metadata
            "disclaimer": disclaimer,
            "processing_time_seconds": processing_time,
            "agents_used": [d.agent_name for d in context.decisions],
        }
        
        # Add Urdu translation if needed
        if context.user_language in ["ur", "roman_urdu"]:
            response["response_urdu"] = self._translate_response_to_urdu(response)
        
        return response
    
    def _build_emergency_response(self, context: AgentContext) -> Dict[str, Any]:
        """Build emergency response for critical symptoms"""
        emergency_messages = {
            "en": "⚠️ EMERGENCY: Your symptoms may require immediate medical attention. Please call emergency services (1122) or visit the nearest hospital immediately.",
            "ur": "⚠️ ایمرجنسی: آپ کی علامات کو فوری طبی توجہ کی ضرورت ہو سکتی ہے۔ براہ کرم ایمرجنسی سروسز (1122) کو کال کریں یا فوراً قریبی ہسپتال جائیں۔",
            "roman_urdu": "⚠️ EMERGENCY: Aap ki symptoms ko fori medical attention chahiye. 1122 call karein ya hospital jayein."
        }
        
        return {
            "success": True,
            "is_emergency": True,
            "session_id": context.session_id,
            "message": emergency_messages.get(context.user_language, emergency_messages["en"]),
            "action_required": "SEEK_IMMEDIATE_MEDICAL_HELP",
            "emergency_contacts": {
                "pakistan_emergency": "1122",
                "edhi": "115",
            },
            "safety_flags": context.safety_flags,
        }
    
    def _generate_explanations(self, context: AgentContext) -> Dict[str, Any]:
        """Generate human-readable explanations"""
        agent_reasoning = []
        
        for decision in context.decisions:
            agent_reasoning.append({
                "agent": decision.agent_name,
                "decision": decision.decision,
                "reasoning": decision.reasoning,
                "confidence": f"{decision.confidence * 100:.0f}%"
            })
        
        # Generate summary based on language
        if context.user_language == "ur":
            summary = self._generate_urdu_summary(context)
        elif context.user_language == "roman_urdu":
            summary = self._generate_roman_urdu_summary(context)
        else:
            summary = self._generate_english_summary(context)
        
        return {
            "summary": summary,
            "agent_reasoning": agent_reasoning
        }
    
    def _generate_english_summary(self, context: AgentContext) -> str:
        """Generate English summary"""
        symptoms_text = ", ".join(context.symptoms[:3]) if context.symptoms else "general health query"
        risk_count = len(context.identified_risks)
        rec_count = len(context.recommendations)
        
        return f"Based on your {symptoms_text}, we identified {risk_count} potential risk(s) and prepared {rec_count} recommendation(s) for you."
    
    def _generate_urdu_summary(self, context: AgentContext) -> str:
        """Generate Urdu summary"""
        symptoms_text = "، ".join(context.symptoms[:3]) if context.symptoms else "صحت کا سوال"
        risk_count = len(context.identified_risks)
        rec_count = len(context.recommendations)
        
        return f"آپ کی {symptoms_text} کی بنیاد پر، ہم نے {risk_count} ممکنہ خطرات کی نشاندہی کی اور آپ کے لیے {rec_count} سفارشات تیار کیں۔"
    
    def _generate_roman_urdu_summary(self, context: AgentContext) -> str:
        """Generate Roman Urdu summary"""
        symptoms_text = ", ".join(context.symptoms[:3]) if context.symptoms else "sehat ka sawal"
        risk_count = len(context.identified_risks)
        rec_count = len(context.recommendations)
        
        return f"Aap ki {symptoms_text} ki buniyad par, humne {risk_count} mumkina khatre aur {rec_count} recommendations tayyar ki hain."
    
    def _calculate_overall_risk(self, context: AgentContext) -> str:
        """Calculate overall risk level"""
        if context.is_emergency:
            return "CRITICAL"
        
        if not context.identified_risks:
            return "LOW"
        
        high_risks = sum(1 for r in context.identified_risks if r.get("severity", 0) > 7)
        if high_risks > 0:
            return "HIGH"
        
        medium_risks = sum(1 for r in context.identified_risks if r.get("severity", 0) > 4)
        if medium_risks > 1:
            return "MEDIUM"
        
        return "LOW"
    
    def _simplify_recommendations(self, context: AgentContext) -> List[str]:
        """Convert recommendations to simple language"""
        # In degraded mode, recommendations are already simple
        if context.degraded_mode:
            return context.recommendations
        
        # Otherwise, they would be simplified by the HealthAdvisor agent
        return context.recommendations
    
    def _translate_response_to_urdu(self, response: Dict) -> Dict:
        """Add Urdu translations to response"""
        # This would use the language service for full translation
        # For now, return key fields in Urdu
        return {
            "khulaasa": response["explanation"]["summary"],
            "khatraat": f"{len(response['risks']['identified_risks'])} khatre",
            "mashwaray": len(response["recommendations"]["preventive_guidance"]),
        }
    
    async def get_healthcare_worker_insights(
        self,
        patient_sessions: List[str]
    ) -> Dict[str, Any]:
        """
        Generate summarized insights for healthcare workers
        
        Args:
            patient_sessions: List of session IDs to summarize
            
        Returns:
            Aggregated insights and recommendations
        """
        # This would aggregate data from multiple sessions
        # For the hackathon demo, return structured format
        return {
            "total_consultations": len(patient_sessions),
            "common_symptoms": [],
            "risk_patterns": [],
            "recommended_interventions": [],
            "urgent_cases": [],
        }

"""
Base Agent Class
Foundation for all specialized agents in SehatAgent
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import structlog
from pydantic import BaseModel
from enum import Enum

logger = structlog.get_logger()


class AgentRole(str, Enum):
    """Enum for agent roles"""
    SYMPTOM_ANALYZER = "symptom_analyzer"
    RISK_ASSESSOR = "risk_assessor"
    HEALTH_ADVISOR = "health_advisor"
    SAFETY_GUARD = "safety_guard"
    OFFLINE_HELPER = "offline_helper"
    FALLBACK = "fallback"  # Alias for offline_helper


class AgentMessage(BaseModel):
    """Message format for agent communication"""
    sender: str
    recipient: str
    content: Dict[str, Any]
    timestamp: datetime = datetime.utcnow()
    message_type: str = "data"  # data, query, response, alert


class AgentDecision(BaseModel):
    """Record of agent decision for explainability"""
    agent_name: str
    decision: str
    reasoning: str
    confidence: float  # 0-1
    inputs_used: List[str]
    timestamp: datetime = datetime.utcnow()
    language: str = "en"


class AgentContext(BaseModel):
    """Shared context between agents"""
    session_id: str
    user_language: str = "en"
    user_input: str
    translated_input: Optional[str] = None
    symptoms: List[str] = []
    health_indicators: Dict[str, Any] = {}
    identified_risks: List[Dict[str, Any]] = []
    recommendations: List[str] = []
    safety_flags: List[str] = []
    decisions: List[AgentDecision] = []
    is_emergency: bool = False
    degraded_mode: bool = False
    
    class Config:
        arbitrary_types_allowed = True


class BaseAgent(ABC):
    """
    Abstract base class for all agents
    
    Each agent must implement:
    - process(): Main processing logic
    - get_explanation(): Generate human-readable explanation
    """
    
    def __init__(
        self,
        name: str,
        role: AgentRole,
        description: str = "",
        vertex_ai_service=None,
        rag_service=None
    ):
        self.name = name
        self.role = role
        self.description = description
        self.vertex_ai = vertex_ai_service
        self.vertex_service = vertex_ai_service  # Alias for compatibility
        self.rag = rag_service
        self.rag_service = rag_service  # Alias for compatibility
        self.is_initialized = False
        self.logger = logger.bind(agent=name)
    
    async def initialize(self):
        """Initialize agent resources"""
        self.logger.info("Initializing agent", role=self.role)
        await self._setup()
        self.is_initialized = True
        self.logger.info("Agent initialized successfully")
    
    async def _setup(self):
        """Override for custom setup logic"""
        pass
    
    @abstractmethod
    async def process(self, context: AgentContext) -> AgentContext:
        """
        Main processing method
        
        Args:
            context: Shared agent context with all information
            
        Returns:
            Updated context with agent's contributions
        """
        pass
    
    @abstractmethod
    def get_explanation(self, context: AgentContext, language: str = "en") -> str:
        """
        Generate human-readable explanation of agent's decisions
        
        Args:
            context: Agent context with decisions
            language: Output language (en, ur, roman_urdu)
            
        Returns:
            Explanation string in requested language
        """
        pass
    
    def log_decision(
        self,
        context: AgentContext,
        decision: str,
        reasoning: str,
        confidence: float,
        inputs_used: List[str]
    ) -> AgentDecision:
        """Log a decision for explainability"""
        agent_decision = AgentDecision(
            agent_name=self.name,
            decision=decision,
            reasoning=reasoning,
            confidence=confidence,
            inputs_used=inputs_used,
            language=context.user_language
        )
        context.decisions.append(agent_decision)
        
        self.logger.info(
            "Decision logged",
            decision=decision,
            confidence=confidence,
            reasoning=reasoning[:100]  # Truncate for log
        )
        
        return agent_decision
    
    async def send_message(
        self,
        recipient: str,
        content: Dict[str, Any],
        message_type: str = "data"
    ) -> AgentMessage:
        """Send message to another agent (via orchestrator)"""
        message = AgentMessage(
            sender=self.name,
            recipient=recipient,
            content=content,
            message_type=message_type
        )
        self.logger.debug("Message sent", recipient=recipient, type=message_type)
        return message
    
    async def query_knowledge_base(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Query the RAG knowledge base"""
        if self.rag is None:
            self.logger.warning("RAG service not available")
            return []
        
        results = await self.rag.search(query, top_k=top_k)
        return results
    
    async def call_llm(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.3,
        max_tokens: int = 1024
    ) -> Optional[str]:
        """Call Vertex AI LLM"""
        if self.vertex_ai is None:
            self.logger.warning("Vertex AI not available, using fallback")
            return None
        
        try:
            response = await self.vertex_ai.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response
        except Exception as e:
            self.logger.error("LLM call failed", error=str(e))
            return None
    
    def format_for_language(
        self,
        content: Dict[str, str],
        language: str
    ) -> str:
        """Get content in requested language"""
        if language in content:
            return content[language]
        return content.get("en", str(content))

"""
Safety Guard Agent
Ensures ethical, safe, and appropriate health recommendations
"""

from typing import Dict, List, Any, Optional
import structlog

from app.agents.base_agent import BaseAgent, AgentRole, AgentContext
from app.config import MEDICAL_SAFETY_CONFIG

logger = structlog.get_logger()


# Emergency symptoms requiring immediate attention
EMERGENCY_SYMPTOMS = {
    # English
    "chest pain", "chest tightness", "heart attack", "stroke",
    "difficulty breathing", "can't breathe", "choking",
    "unconscious", "unresponsive", "fainted",
    "severe bleeding", "heavy bleeding",
    "seizure", "convulsion",
    "severe allergic reaction", "anaphylaxis",
    "severe head injury", "head trauma",
    "suicidal", "self harm", "want to die",
    
    # Urdu
    "سینے میں درد", "سانس نہیں آ رہی", "بے ہوش",
    "شدید خون بہنا", "دورہ پڑنا", "دل کا دورہ",
    
    # Roman Urdu
    "seene mein dard", "saans nahi aa rahi", "behosh",
    "shadeed khoon", "dil ka daura",
}

# Symptoms requiring doctor visit (not emergency but important)
DOCTOR_REQUIRED_SYMPTOMS = {
    "blood in stool", "blood in urine", "vomiting blood",
    "persistent high fever", "fever over 104",
    "severe abdominal pain", "appendicitis symptoms",
    "pregnancy complications", "heavy period",
    "sudden vision loss", "sudden hearing loss",
    "severe headache worst ever",
    "lump or growth", "unexplained weight loss",
    "jaundice", "yellow eyes",
    
    # Urdu/Roman Urdu
    "خون کی الٹی", "پیشاب میں خون", "پاخانے میں خون",
    "khoon ki ulti", "peshab mein khoon",
}

# Topics that require professional guidance only
SENSITIVE_TOPICS = {
    "pregnancy", "mental health", "suicide", "depression",
    "sexually transmitted", "hiv", "aids",
    "cancer", "tumor", "chemotherapy",
    "prescription medication", "drug interaction",
}

# Unsafe recommendations to filter out
UNSAFE_RECOMMENDATIONS = [
    "take antibiotics without prescription",
    "self-medicate",
    "ignore symptoms",
    "skip doctor",
    "use unprescribed medication",
]


class SafetyGuardAgent(BaseAgent):
    """
    Agent responsible for ensuring safe and ethical health guidance
    
    Capabilities:
    - Detect emergency situations
    - Filter unsafe recommendations
    - Add appropriate disclaimers
    - Ensure ethical compliance
    """
    
    def __init__(self, vertex_ai_service=None, rag_service=None):
        super().__init__(
            name="SafetyGuard",
            role=AgentRole.SAFETY_GUARD,
            description="Ensures ethical and safe recommendations",
            vertex_ai_service=vertex_ai_service,
            rag_service=rag_service
        )
        self.emergency_symptoms = EMERGENCY_SYMPTOMS
        self.doctor_required = DOCTOR_REQUIRED_SYMPTOMS
        self.sensitive_topics = SENSITIVE_TOPICS
    
    async def process(self, context: AgentContext) -> AgentContext:
        """
        Pre-check: Scan for emergency situations
        
        Steps:
        1. Check for emergency symptoms
        2. Check for doctor-required conditions
        3. Flag sensitive topics
        4. Set appropriate safety flags
        """
        self.logger.info("Safety pre-check", session_id=context.session_id)
        
        user_text = (context.user_input + " " + (context.translated_input or "")).lower()
        
        # Step 1: Emergency detection
        is_emergency = self._check_emergency(user_text)
        if is_emergency:
            context.is_emergency = True
            context.safety_flags.append("EMERGENCY_DETECTED")
            
            self.log_decision(
                context=context,
                decision="Emergency situation detected",
                reasoning="User input contains emergency symptoms requiring immediate medical attention",
                confidence=0.95,
                inputs_used=["user_input", "emergency_patterns"]
            )
            
            return context
        
        # Step 2: Doctor required check
        needs_doctor = self._check_doctor_required(user_text)
        if needs_doctor:
            context.safety_flags.append("DOCTOR_RECOMMENDED")
        
        # Step 3: Sensitive topic check
        sensitive = self._check_sensitive_topics(user_text)
        if sensitive:
            context.safety_flags.append(f"SENSITIVE_TOPIC:{sensitive}")
        
        # Log decision
        self.log_decision(
            context=context,
            decision="Safety pre-check passed" if not context.safety_flags else f"Flags: {', '.join(context.safety_flags)}",
            reasoning="Scanned for emergency, doctor-required, and sensitive topics",
            confidence=0.9,
            inputs_used=["user_input", "safety_patterns"]
        )
        
        return context
    
    async def validate_recommendations(self, context: AgentContext) -> AgentContext:
        """
        Post-check: Validate and filter recommendations
        
        Steps:
        1. Filter unsafe recommendations
        2. Add appropriate disclaimers
        3. Ensure severity-appropriate guidance
        """
        self.logger.info("Validating recommendations", 
                        session_id=context.session_id,
                        rec_count=len(context.recommendations))
        
        validated_recommendations = []
        
        for rec in context.recommendations:
            # Check if recommendation is safe
            if self._is_safe_recommendation(rec):
                validated_recommendations.append(rec)
            else:
                self.logger.warning("Filtered unsafe recommendation", rec=rec[:50])
        
        # Add doctor visit recommendation if high-risk
        if context.identified_risks:
            high_severity = any(r.get("severity", 0) > 7 for r in context.identified_risks)
            if high_severity and "DOCTOR_RECOMMENDED" not in context.safety_flags:
                context.safety_flags.append("DOCTOR_RECOMMENDED")
                
                doctor_rec = self._get_doctor_recommendation(context.user_language)
                validated_recommendations.insert(0, doctor_rec)
        
        context.recommendations = validated_recommendations
        
        # Log decision
        self.log_decision(
            context=context,
            decision=f"Validated {len(validated_recommendations)} recommendations",
            reasoning="Filtered unsafe recommendations and added appropriate warnings",
            confidence=0.9,
            inputs_used=["recommendations", "identified_risks", "safety_flags"]
        )
        
        return context
    
    def _check_emergency(self, text: str) -> bool:
        """Check if input contains emergency symptoms"""
        text_lower = text.lower()
        
        for symptom in self.emergency_symptoms:
            if symptom.lower() in text_lower:
                return True
        
        return False
    
    def _check_doctor_required(self, text: str) -> bool:
        """Check if symptoms require doctor visit"""
        text_lower = text.lower()
        
        for symptom in self.doctor_required:
            if symptom.lower() in text_lower:
                return True
        
        return False
    
    def _check_sensitive_topics(self, text: str) -> Optional[str]:
        """Check for sensitive health topics"""
        text_lower = text.lower()
        
        for topic in self.sensitive_topics:
            if topic in text_lower:
                return topic
        
        return None
    
    def _is_safe_recommendation(self, recommendation: str) -> bool:
        """Check if a recommendation is safe"""
        rec_lower = recommendation.lower()
        
        for unsafe in UNSAFE_RECOMMENDATIONS:
            if unsafe in rec_lower:
                return False
        
        return True
    
    def _get_doctor_recommendation(self, language: str) -> str:
        """Get doctor visit recommendation in appropriate language"""
        messages = {
            "en": "⚠️ Based on your symptoms, we strongly recommend consulting a healthcare professional for proper diagnosis and treatment.",
            "ur": "⚠️ آپ کی علامات کی بنیاد پر، ہم تجویز کرتے ہیں کہ صحیح تشخیص کے لیے ڈاکٹر سے ضرور ملیں۔",
            "roman_urdu": "⚠️ Aap ki symptoms ke mutabiq, doctor se milna zaroori hai.",
        }
        
        return messages.get(language, messages["en"])
    
    def get_explanation(self, context: AgentContext, language: str = "en") -> str:
        """Generate safety explanation"""
        flags = context.safety_flags
        
        if "EMERGENCY_DETECTED" in flags:
            explanations = {
                "en": "⚠️ I detected symptoms that require immediate emergency care.",
                "ur": "⚠️ میں نے ایسی علامات کا پتہ لگایا جن کو فوری طبی امداد کی ضرورت ہے۔",
                "roman_urdu": "⚠️ Maine aisi symptoms detect ki hain jo emergency hain.",
            }
        elif "DOCTOR_RECOMMENDED" in flags:
            explanations = {
                "en": "I recommend consulting a doctor for your symptoms.",
                "ur": "میں تجویز کرتا ہوں کہ آپ اپنی علامات کے لیے ڈاکٹر سے ملیں۔",
                "roman_urdu": "Main recommend karta hoon ke aap doctor se milein.",
            }
        else:
            explanations = {
                "en": "Your symptoms appear manageable with self-care, but monitor for changes.",
                "ur": "آپ کی علامات گھر پر سنبھالی جا سکتی ہیں، لیکن تبدیلیوں پر نظر رکھیں۔",
                "roman_urdu": "Aap ki symptoms ghar par sambhali ja sakti hain.",
            }
        
        return explanations.get(language, explanations["en"])

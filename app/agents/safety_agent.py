"""
Safety Guard Agent
Ensures ethical and safe health recommendations

Validates recommendations against safety guidelines and medical ethics.
"""

from typing import List, Dict, Any
from app.agents.base_agent import BaseAgent, AgentRole, AgentContext, AgentDecision


class SafetyGuardAgent(BaseAgent):
    """
    Ensures all recommendations are safe and ethical.
    Checks for emergency conditions and validates advice.
    """
    
    def __init__(self, rag_service=None, vertex_service=None):
        super().__init__(
            name="SafetyGuard",
            role=AgentRole.SAFETY_GUARD,
            description="Ensures recommendations are safe and ethical, validates medical advice",
            rag_service=rag_service,
            vertex_ai_service=vertex_service
        )
        
        # Emergency keywords that require immediate referral
        self.EMERGENCY_KEYWORDS = {
            "en": [
                "chest pain", "heart attack", "can't breathe", "unconscious",
                "severe bleeding", "stroke", "seizure", "convulsion", "suicide",
                "poisoning", "overdose", "choking"
            ],
            "ur": [
                "سینے میں درد", "دل کا دورہ", "سانس نہیں آ رہی", "بے ہوش",
                "شدید خون", "فالج", "مرگی", "خودکشی", "زہر"
            ],
            "roman_urdu": [
                "seene mein dard", "heart attack", "saans nahi aa rahi", "behosh",
                "shadeed khoon", "falij", "mirgi", "khudkushi", "zeher"
            ]
        }
        
        # Dangerous advice that should never be given
        self.PROHIBITED_ADVICE = [
            "stop taking prescribed medication",
            "ignore doctor's advice",
            "self-diagnose",
            "treat serious conditions at home without doctor",
            "take someone else's prescription"
        ]
        
        # Medical disclaimer in multiple languages
        self.DISCLAIMER = {
            "en": "⚕️ DISCLAIMER: This is health information, not medical advice. Always consult a qualified healthcare professional for diagnosis and treatment.",
            "ur": "⚕️ اعلان: یہ صحت کی معلومات ہے، طبی مشورہ نہیں۔ تشخیص اور علاج کے لیے ہمیشہ ڈاکٹر سے ملیں۔",
            "roman_urdu": "⚕️ DISCLAIMER: Yeh health information hai, medical advice nahi. Diagnosis aur treatment ke liye doctor se zaroor milein."
        }
    
    async def process(self, context: AgentContext) -> AgentContext:
        """Validate recommendations for safety"""
        
        user_input = (context.translated_input or context.user_input).lower()
        language = context.user_language
        
        # Check for emergency conditions
        emergency_detected = self._check_emergency(user_input)
        if emergency_detected:
            context.is_emergency = True
            context.safety_flags.append(f"EMERGENCY_DETECTED: {emergency_detected}")
            
            # Prepend emergency message to recommendations
            emergency_msg = {
                "en": "⚠️ EMERGENCY: Please call 1122 (Rescue) or 115 (Edhi) immediately, or go to the nearest hospital!",
                "ur": "⚠️ ایمرجنسی: فوری 1122 (ریسکیو) یا 115 (ایدھی) کال کریں، یا قریبی ہسپتال جائیں!",
                "roman_urdu": "⚠️ EMERGENCY: Fori 1122 (Rescue) ya 115 (Edhi) call karein, ya hospital jayein!"
            }
            
            if context.recommendations:
                context.recommendations.insert(0, emergency_msg.get(language, emergency_msg["en"]))
            else:
                context.recommendations = [emergency_msg.get(language, emergency_msg["en"])]
        
        # Check for high-risk symptoms
        risk_level = context.health_indicators.get("risk_level", "LOW")
        if risk_level in ["HIGH", "CRITICAL"]:
            see_doctor_msg = {
                "en": "⚠️ Your symptoms may indicate a serious condition. Please see a doctor soon.",
                "ur": "⚠️ آپ کی علامات سنگین حالت کی نشاندہی کر سکتی ہیں۔ براہ کرم جلد ڈاکٹر سے ملیں۔",
                "roman_urdu": "⚠️ Aapki symptoms serious condition indicate kar sakti hain. Jald doctor se milein."
            }
            context.safety_flags.append(see_doctor_msg.get(language, see_doctor_msg["en"]))
        
        # Validate recommendations (remove any prohibited advice)
        validated_recommendations = []
        for rec in context.recommendations:
            rec_lower = rec.lower()
            is_safe = True
            
            for prohibited in self.PROHIBITED_ADVICE:
                if prohibited in rec_lower:
                    is_safe = False
                    context.safety_flags.append(f"REMOVED_UNSAFE_ADVICE: {rec[:50]}...")
                    break
            
            if is_safe:
                validated_recommendations.append(rec)
        
        context.recommendations = validated_recommendations
        
        # Always add disclaimer
        disclaimer = self.DISCLAIMER.get(language, self.DISCLAIMER["en"])
        if disclaimer not in context.safety_flags:
            context.safety_flags.append(disclaimer)
        
        # Log decision
        decision = AgentDecision(
            agent_name=self.name,
            decision=f"Safety check: Emergency={context.is_emergency}, RiskLevel={risk_level}, ValidatedRecs={len(validated_recommendations)}",
            reasoning="Checked for emergency keywords, validated recommendations, added medical disclaimer.",
            confidence=0.95,
            inputs_used=["user_input", "recommendations", "risk_level"],
            language=language
        )
        context.decisions.append(decision)
        
        return context
    
    def _check_emergency(self, text: str) -> str:
        """Check if text contains emergency keywords"""
        
        for lang, keywords in self.EMERGENCY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    return keyword
        
        return ""
    
    def get_explanation(self, context: AgentContext, language: str = "en") -> str:
        """Generate human-readable explanation of safety checks"""
        
        is_emergency = context.is_emergency
        risk_level = context.health_indicators.get("risk_level", "LOW")
        flags_count = len(context.safety_flags)
        
        if is_emergency:
            explanations = {
                "en": f"⚠️ EMERGENCY DETECTED! I've flagged this as urgent. Please seek immediate medical help by calling 1122 or 115.",
                "ur": f"⚠️ ایمرجنسی! میں نے اسے فوری قرار دیا ہے۔ براہ کرم 1122 یا 115 کال کریں۔",
                "roman_urdu": f"⚠️ EMERGENCY! Maine isko urgent flag kiya hai. 1122 ya 115 call karein."
            }
        elif risk_level in ["HIGH", "CRITICAL"]:
            explanations = {
                "en": f"I've identified your risk level as {risk_level}. Please consult a doctor soon. I've added {flags_count} safety notes to my recommendations.",
                "ur": f"آپ کی خطرے کی سطح {risk_level} ہے۔ براہ کرم جلد ڈاکٹر سے ملیں۔",
                "roman_urdu": f"Aapka risk level {risk_level} hai. Jald doctor se milein."
            }
        else:
            explanations = {
                "en": f"I've validated all recommendations for safety. Risk level: {risk_level}. Remember: this is health information, not medical advice.",
                "ur": f"میں نے تمام مشوروں کی حفاظت کی تصدیق کی ہے۔ خطرے کی سطح: {risk_level}۔",
                "roman_urdu": f"Maine sab mashwaron ki safety check ki hai. Risk level: {risk_level}."
            }
        
        return explanations.get(language, explanations["en"])

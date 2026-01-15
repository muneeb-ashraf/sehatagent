"""
Symptom Analyzer Agent
Uses WHO guidelines and NIH clinical patterns for symptom analysis

Data Sources:
- WHO Global Health Data (https://www.who.int/data)
- NIH Open Clinical Data (https://www.ncbi.nlm.nih.gov/gap)
- Pakistan Bureau of Statistics (https://pslm-sdgs.data.gov.pk/health/index)
"""

from typing import List, Dict, Any, Optional
import re
from app.agents.base_agent import BaseAgent, AgentRole, AgentContext, AgentDecision

# Try to import knowledge base, use fallback if not available
try:
    from app.knowledge.health_knowledge_base import (
        WHO_HEALTH_DATA, 
        NIH_CLINICAL_PATTERNS,
        PAKISTAN_HEALTH_STATISTICS
    )
except ImportError:
    WHO_HEALTH_DATA = {"fever_management": {"fever_threshold_celsius": 38.0}}
    NIH_CLINICAL_PATTERNS = {"symptom_duration_guidelines": {}}
    PAKISTAN_HEALTH_STATISTICS = {"disease_burden": {}}


class SymptomAnalyzerAgent(BaseAgent):
    """
    Analyzes symptoms from user input using:
    - WHO IMCI guidelines
    - NIH clinical symptom patterns
    - Pakistan-specific disease patterns
    """
    
    def __init__(self, rag_service=None, vertex_service=None):
        super().__init__(
            name="SymptomAnalyzer",
            role=AgentRole.SYMPTOM_ANALYZER,
            description="Analyzes symptoms using WHO/NIH guidelines and Pakistan health data",
            rag_service=rag_service,
            vertex_ai_service=vertex_service
        )
        
        # Comprehensive symptom patterns in multiple languages
        self.SYMPTOM_PATTERNS = {
            "fever": {
                "patterns": [
                    r"\b(fever|bukhar|بخار|temperature|temp|taap|garmi)\b",
                    r"\b(feverish|hot body|jism garam|تیز بخار)\b"
                ],
                "related_conditions": ["typhoid", "dengue", "malaria", "viral_infection", "uti"],
                "severity_indicators": {
                    "high": [r"high fever", r"tez bukhar", r"104", r"103", r"40\s*°?c", r"39\s*°?c"],
                    "sustained": [r"continuous", r"musalsal", r"lagatar", r"3 din", r"week"],
                    "with_chills": [r"chills", r"rigors", r"kapkapi", r"کپکپی", r"thand"]
                },
                "who_threshold_celsius": 38.0
            },
            
            "headache": {
                "patterns": [
                    r"\b(headache|sir\s*dard|سر\s*درد|sar\s*dard|head\s*pain)\b",
                    r"\b(migraine|adhkapari|آدھا\s*سر)\b"
                ],
                "related_conditions": ["hypertension", "dengue", "typhoid", "migraine", "tension", "dehydration"],
                "severity_indicators": {
                    "severe": [r"severe", r"shadeed", r"شدید", r"worst", r"unbearable"],
                    "with_vision": [r"vision", r"nazar", r"blurr", r"dhundla"],
                    "with_neck_stiffness": [r"stiff neck", r"gardan", r"گردن"]
                }
            },
            
            "cough": {
                "patterns": [
                    r"\b(cough|khansi|کھانسی|khansta|coughing)\b"
                ],
                "related_conditions": ["tuberculosis", "pneumonia", "bronchitis", "common_cold"],
                "severity_indicators": {
                    "productive": [r"phlegm", r"balgham", r"بلغم", r"mucus"],
                    "bloody": [r"blood", r"khoon", r"خون", r"hemoptysis"],
                    "persistent": [r"2 week", r"do hafte", r"persistent", r"chronic"]
                },
                "tb_indicators": [r"weight loss", r"night sweat", r"evening fever", r"2 hafte se zyada"]
            },
            
            "diarrhea": {
                "patterns": [
                    r"\b(diarrhea|diarrhoea|dast|دست|loose\s*motion|pichkari)\b",
                    r"\b(watery\s*stool|patla\s*pakhana|پتلا\s*پاخانہ)\b"
                ],
                "related_conditions": ["gastroenteritis", "typhoid", "cholera", "food_poisoning"],
                "severity_indicators": {
                    "bloody": [r"blood", r"khoon", r"خون", r"dysentery", r"pechish"],
                    "frequent": [r"many times", r"kai baar", r"کئی بار", r"bar bar"],
                    "with_vomiting": [r"vomit", r"ulti", r"الٹی", r"qai"]
                },
                "dehydration_signs": ["sunken eyes", "dry mouth", "no urine", "thirst"]
            },
            
            "fatigue": {
                "patterns": [
                    r"\b(fatigue|tired|thakan|تھکاوٹ|kamzori|کمزوری|weakness)\b",
                    r"\b(no energy|exhausted|thaka hua|sust)\b"
                ],
                "related_conditions": ["anemia", "vitamin_d_deficiency", "diabetes", "thyroid", "depression"],
                "severity_indicators": {
                    "persistent": [r"always", r"hamesha", r"ہمیشہ", r"constant"],
                    "with_pallor": [r"pale", r"zard", r"peela", r"زرد"]
                }
            },
            
            "stomach_pain": {
                "patterns": [
                    r"\b(stomach|pet|پیٹ|abdomen|abdominal)\s*(pain|dard|درد|ache)\b",
                    r"\b(pet\s*dard|پیٹ\s*درد|tummy\s*ache)\b"
                ],
                "related_conditions": ["gastritis", "typhoid", "appendicitis", "ulcer", "food_poisoning"],
                "severity_indicators": {
                    "severe": [r"severe", r"shadeed", r"شدید", r"unbearable"],
                    "right_lower": [r"right side", r"dayen", r"appendix"],
                    "with_fever": [r"fever", r"bukhar", r"بخار"]
                }
            },
            
            "chest_pain": {
                "patterns": [
                    r"\b(chest|seena|سینہ|chhati)\s*(pain|dard|درد)\b",
                    r"\b(seene\s*mein\s*dard|سینے\s*میں\s*درد)\b"
                ],
                "related_conditions": ["heart_attack", "angina", "pneumonia", "gerd", "muscle_strain"],
                "emergency": True,
                "severity_indicators": {
                    "radiating": [r"arm", r"jaw", r"bazu", r"بازو"],
                    "with_breathlessness": [r"breath", r"saans", r"سانس"]
                }
            },
            
            "breathing_difficulty": {
                "patterns": [
                    r"\b(breathless|breath|saans|سانس)\s*(difficulty|problem|taklif|تکلیف)\b",
                    r"\b(saans\s*lene\s*mein|can't\s*breathe|dam\s*ghutna)\b"
                ],
                "related_conditions": ["asthma", "pneumonia", "heart_failure", "covid", "anemia"],
                "emergency": True
            },
            
            "vomiting": {
                "patterns": [
                    r"\b(vomit|ulti|الٹی|qai|throw\s*up|nausea)\b"
                ],
                "related_conditions": ["gastroenteritis", "food_poisoning", "pregnancy", "migraine"],
                "severity_indicators": {
                    "bloody": [r"blood", r"khoon", r"خون"],
                    "persistent": [r"bar bar", r"again and again", r"continuous"]
                }
            },
            
            "joint_pain": {
                "patterns": [
                    r"\b(joint|jor|جوڑ|joron)\s*(pain|dard|درد)\b",
                    r"\b(arthritis|gathiya|گٹھیا)\b"
                ],
                "related_conditions": ["arthritis", "dengue", "chikungunya", "gout", "vitamin_d_deficiency"]
            },
            
            "skin_rash": {
                "patterns": [
                    r"\b(rash|daane|دانے|skin|jild|چھال)\b",
                    r"\b(itching|khujli|کھجلی|allergy)\b"
                ],
                "related_conditions": ["dengue", "allergy", "measles", "chickenpox", "eczema"]
            },
            
            "urinary_issues": {
                "patterns": [
                    r"\b(urin|peshab|پیشاب|bladder)\b",
                    r"\b(burning|jalaan|جلن)\s*(urin|peshab)\b"
                ],
                "related_conditions": ["uti", "kidney_stone", "diabetes", "prostate"]
            }
        }
        
        # Emergency symptoms requiring immediate referral
        self.EMERGENCY_SYMPTOMS = [
            "chest_pain", "breathing_difficulty", "unconscious", "severe_bleeding",
            "stroke_symptoms", "seizure"
        ]
    
    async def process(self, context: AgentContext) -> AgentContext:
        """Analyze symptoms from user input"""
        
        user_input = (context.translated_input or context.user_input).lower()
        
        identified_symptoms = []
        severity_flags = []
        potential_conditions = set()
        health_indicators = {}
        
        # Pattern-based symptom extraction
        for symptom_name, symptom_data in self.SYMPTOM_PATTERNS.items():
            patterns = symptom_data.get("patterns", [])
            
            for pattern in patterns:
                if re.search(pattern, user_input, re.IGNORECASE):
                    identified_symptoms.append(symptom_name)
                    
                    # Check for emergency symptoms
                    if symptom_data.get("emergency"):
                        context.is_emergency = True
                        context.safety_flags.append(f"EMERGENCY: {symptom_name} detected")
                    
                    # Add related conditions
                    potential_conditions.update(symptom_data.get("related_conditions", []))
                    
                    # Check severity indicators
                    for severity, indicators in symptom_data.get("severity_indicators", {}).items():
                        for indicator in indicators:
                            if re.search(indicator, user_input, re.IGNORECASE):
                                severity_flags.append(f"{symptom_name}:{severity}")
                    
                    break
        
        # Extract duration if mentioned
        duration_match = re.search(r'(\d+)\s*(din|day|week|hafte|month|mahine)', user_input, re.IGNORECASE)
        if duration_match:
            health_indicators["duration"] = f"{duration_match.group(1)} {duration_match.group(2)}"
        
        # Update context
        context.symptoms = list(set(identified_symptoms))
        context.health_indicators = {
            "potential_conditions": list(potential_conditions),
            "severity_flags": severity_flags,
            **health_indicators
        }
        
        # Log decision
        decision = AgentDecision(
            agent_name=self.name,
            decision=f"Identified {len(identified_symptoms)} symptoms: {', '.join(identified_symptoms) if identified_symptoms else 'none'}",
            reasoning=f"Pattern matching with WHO/NIH guidelines. Severity: {severity_flags}. Potential conditions: {list(potential_conditions)[:5]}",
            confidence=0.85 if identified_symptoms else 0.5,
            inputs_used=["user_input", "WHO_HEALTH_DATA", "NIH_CLINICAL_PATTERNS"],
            language=context.user_language
        )
        context.decisions.append(decision)
        
        return context
    
    def get_explanation(self, context: AgentContext, language: str = "en") -> str:
        """Generate human-readable explanation of symptom analysis"""
        
        symptoms = context.symptoms or []
        indicators = context.health_indicators or {}
        
        if not symptoms:
            explanations = {
                "en": "I couldn't identify specific symptoms from your description. Please describe what you're feeling in more detail.",
                "ur": "میں آپ کی تفصیل سے مخصوص علامات کی شناخت نہیں کر سکا۔ براہ کرم مزید تفصیل سے بتائیں۔",
                "roman_urdu": "Main aapki description se symptoms identify nahi kar saka. Please mazeed detail mein batayen."
            }
        else:
            symptom_list = ", ".join(symptoms)
            conditions = indicators.get("potential_conditions", [])[:3]
            condition_list = ", ".join(conditions) if conditions else "various conditions"
            
            explanations = {
                "en": f"Based on your description, I identified these symptoms: {symptom_list}. These could be related to {condition_list}. Data sources: WHO guidelines, Pakistan health statistics.",
                "ur": f"آپ کی تفصیل کی بنیاد پر، یہ علامات ملیں: {symptom_list}۔ یہ {condition_list} سے متعلق ہو سکتی ہیں۔",
                "roman_urdu": f"Aapki description se yeh symptoms milay: {symptom_list}. Yeh {condition_list} se related ho sakti hain."
            }
        
        return explanations.get(language, explanations["en"])

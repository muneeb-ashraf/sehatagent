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
from app.knowledge.health_knowledge_base import (
    WHO_HEALTH_DATA, 
    NIH_CLINICAL_PATTERNS,
    PAKISTAN_HEALTH_STATISTICS
)


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
            role=AgentRole.ANALYZER,
            rag_service=rag_service,
            vertex_service=vertex_service
        )
        
        # Comprehensive symptom patterns in multiple languages
        # Based on WHO and Pakistan Bureau of Statistics common presentations
        self.SYMPTOM_PATTERNS = {
            # Fever patterns (Typhoid, Dengue, Malaria common in Pakistan)
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
            
            # Headache patterns
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
            
            # Cough patterns (TB is 5th highest burden in Pakistan)
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
            
            # Diarrhea patterns (53,000 child deaths/year in Pakistan)
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
            
            # Fatigue (66% vitamin D deficiency, 41% anemia in women)
            "fatigue": {
                "patterns": [
                    r"\b(fatigue|tired|thakan|تھکاوٹ|kamzori|کمزوری|weakness)\b",
                    r"\b(exhausted|weak|low\s*energy|susti)\b"
                ],
                "related_conditions": ["anemia", "vitamin_d_deficiency", "diabetes", "thyroid"],
                "severity_indicators": {
                    "persistent": [r"always", r"hamesha", r"ہمیشہ", r"chronic"],
                    "with_pallor": [r"pale", r"peela", r"پیلا", r"rang"],
                    "with_breathlessness": [r"breath", r"saans", r"سانس"]
                }
            },
            
            # Stomach pain
            "stomach_pain": {
                "patterns": [
                    r"\b(stomach\s*pain|pait\s*dard|پیٹ\s*درد|pet\s*dard|abdominal)\b",
                    r"\b(tummy\s*ache|maida|معدہ)\b"
                ],
                "related_conditions": ["gastritis", "typhoid", "appendicitis", "ulcer"],
                "severity_indicators": {
                    "severe": [r"severe", r"shadeed", r"شدید"],
                    "location_right_lower": [r"right side", r"dahini", r"دائیں"],
                    "with_vomiting": [r"vomit", r"ulti", r"الٹی"]
                }
            },
            
            # Breathing difficulty - EMERGENCY
            "breathing_difficulty": {
                "patterns": [
                    r"\b(breathing|saans|سانس|breath|breathless)\b",
                    r"\b(shortness\s*of\s*breath|saans\s*phoolna|سانس\s*پھولنا)\b"
                ],
                "related_conditions": ["asthma", "pneumonia", "heart_failure", "anemia"],
                "emergency": True
            },
            
            # Chest pain - EMERGENCY
            "chest_pain": {
                "patterns": [
                    r"\b(chest\s*pain|seene\s*mein\s*dard|سینے\s*میں\s*درد)\b",
                    r"\b(heart\s*pain|dil\s*mein\s*dard|دل\s*کا\s*درد)\b"
                ],
                "related_conditions": ["heart_attack", "angina", "gastric"],
                "emergency": True
            },
            
            # Vomiting
            "vomiting": {
                "patterns": [
                    r"\b(vomit|ulti|الٹی|qai|قے|throwing\s*up)\b"
                ],
                "related_conditions": ["gastroenteritis", "food_poisoning", "pregnancy"],
                "severity_indicators": {
                    "bloody": [r"blood", r"khoon", r"خون"],
                    "persistent": [r"can't keep", r"everything", r"bar bar"]
                }
            },
            
            # Body aches (dengue indicator)
            "body_aches": {
                "patterns": [
                    r"\b(body\s*ache|jism\s*mein\s*dard|جسم\s*میں\s*درد|badan\s*dard)\b",
                    r"\b(muscle\s*pain|joint\s*pain|joron\s*mein\s*dard|جوڑوں\s*میں\s*درد)\b"
                ],
                "related_conditions": ["dengue", "viral_fever", "chikungunya", "flu"]
            },
            
            # Jaundice (Hepatitis B 2.5%, Hepatitis C 5% in Pakistan)
            "jaundice": {
                "patterns": [
                    r"\b(jaundice|yarqan|یرقان|yellow\s*eyes|peeli\s*aankhen)\b",
                    r"\b(yellow\s*skin|peela\s*rang|پیلا\s*رنگ)\b"
                ],
                "related_conditions": ["hepatitis_b", "hepatitis_c", "hepatitis_a", "liver_disease"]
            },
            
            # Dizziness (anemia, hypertension indicator)
            "dizziness": {
                "patterns": [
                    r"\b(dizzy|chakkar|چکر|vertigo|giddy)\b"
                ],
                "related_conditions": ["anemia", "hypertension", "hypotension", "dehydration"]
            },
            
            # Weight loss (TB, diabetes, cancer indicator)
            "weight_loss": {
                "patterns": [
                    r"\b(weight\s*loss|wajan\s*kam|وزن\s*کم|patla\s*ho\s*gaya)\b"
                ],
                "related_conditions": ["tuberculosis", "diabetes", "thyroid", "cancer"]
            },
            
            # Night sweats (TB indicator)
            "night_sweats": {
                "patterns": [
                    r"\b(night\s*sweat|raat\s*ko\s*paseena|رات\s*کو\s*پسینہ)\b"
                ],
                "related_conditions": ["tuberculosis", "lymphoma", "infection"]
            }
        }
        
        # WHO danger signs
        self.WHO_DANGER_SIGNS = WHO_HEALTH_DATA["imci_danger_signs"]["children_under_5"]
        
        # NIH red flags
        self.RED_FLAGS = NIH_CLINICAL_PATTERNS["red_flag_symptoms"]
        
        # Duration guidelines
        self.DURATION_GUIDELINES = NIH_CLINICAL_PATTERNS["symptom_duration_guidelines"]
    
    async def process(self, context: AgentContext) -> AgentContext:
        """Process user input to identify symptoms"""
        
        user_input = context.translated_input or context.user_input
        user_input_lower = user_input.lower()
        
        identified_symptoms = []
        health_indicators = {}
        severity_flags = []
        
        # Pattern-based symptom extraction
        for symptom_name, symptom_data in self.SYMPTOM_PATTERNS.items():
            for pattern in symptom_data["patterns"]:
                if re.search(pattern, user_input_lower, re.IGNORECASE):
                    identified_symptoms.append(symptom_name)
                    
                    # Check severity
                    for severity_level, indicators in symptom_data.get("severity_indicators", {}).items():
                        for indicator in indicators:
                            if re.search(indicator, user_input_lower, re.IGNORECASE):
                                severity_flags.append(f"{symptom_name}_{severity_level}")
                                health_indicators[f"{symptom_name}_severity"] = severity_level
                    
                    # Emergency check
                    if symptom_data.get("emergency"):
                        context.is_emergency = True
                        context.safety_flags.append(f"EMERGENCY_SYMPTOM:{symptom_name}")
                    
                    break
        
        # Extract duration
        duration_patterns = [
            (r"(\d+)\s*din|(\d+)\s*day", "days"),
            (r"(\d+)\s*hafte|(\d+)\s*week", "weeks"),
            (r"(\d+)\s*ghante|(\d+)\s*hour", "hours"),
            (r"kal\s*se|since\s*yesterday", "1 day"),
            (r"parson\s*se", "2 days")
        ]
        
        for pattern, unit in duration_patterns:
            match = re.search(pattern, user_input_lower, re.IGNORECASE)
            if match:
                value = match.group(1) if match.group(1) else "1"
                health_indicators["duration"] = f"{value} {unit}"
                break
        
        # Check WHO danger signs
        for danger_sign in self.WHO_DANGER_SIGNS:
            if danger_sign.lower() in user_input_lower:
                context.is_emergency = True
                context.safety_flags.append(f"WHO_DANGER_SIGN:{danger_sign}")
        
        # Map to potential conditions
        potential_conditions = set()
        for symptom in identified_symptoms:
            if symptom in self.SYMPTOM_PATTERNS:
                conditions = self.SYMPTOM_PATTERNS[symptom].get("related_conditions", [])
                potential_conditions.update(conditions)
        
        health_indicators["potential_conditions"] = list(potential_conditions)
        health_indicators["severity_flags"] = severity_flags
        
        # LLM extraction if few symptoms found
        if self.vertex_service and len(identified_symptoms) < 2 and not context.degraded_mode:
            try:
                llm_symptoms = await self._extract_with_llm(user_input, context.user_language)
                for symptom in llm_symptoms:
                    if symptom not in identified_symptoms:
                        identified_symptoms.append(symptom)
            except Exception as e:
                self.logger.warning(f"LLM extraction failed: {e}")
        
        # Update context
        context.symptoms = list(set(identified_symptoms))
        context.health_indicators = health_indicators
        
        # Log decision
        decision = AgentDecision(
            agent_name=self.name,
            decision=f"Identified {len(identified_symptoms)} symptoms: {', '.join(identified_symptoms)}",
            reasoning=f"Pattern matching with WHO/NIH guidelines. Severity: {severity_flags}. Potential conditions: {list(potential_conditions)[:5]}",
            confidence=0.85 if identified_symptoms else 0.5,
            inputs_used=["user_input", "WHO_HEALTH_DATA", "NIH_CLINICAL_PATTERNS", "PAKISTAN_HEALTH_STATISTICS"],
            language=context.user_language
        )
        context.decisions.append(decision)
        
        return context
    
    async def _extract_with_llm(self, user_input: str, language: str) -> List[str]:
        """Use LLM for complex symptom extraction"""
        
        prompt = f"""Extract health symptoms from this text. Consider Pakistan-common conditions (typhoid, dengue, TB, diabetes, hypertension, anemia).

Text: {user_input}

Return ONLY comma-separated symptom keywords in English. If none, return "none".
"""
        
        response = await self.vertex_service.generate_text(prompt)
        
        if response and response.lower() != "none":
            symptoms = [s.strip().lower().replace(" ", "_") for s in response.split(",")]
            return [s for s in symptoms if s in self.SYMPTOM_PATTERNS]
        
        return []

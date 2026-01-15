"""
Risk Assessor Agent
Identifies health risks using Pakistan Bureau of Statistics health data

Data Sources:
- Pakistan Bureau of Statistics (https://pslm-sdgs.data.gov.pk/health/index)
- WHO Health Data (https://www.who.int/data)
"""

from typing import List, Dict, Any
from app.agents.base_agent import BaseAgent, AgentRole, AgentContext, AgentDecision

# Try to import knowledge base
try:
    from app.knowledge.health_knowledge_base import (
        PAKISTAN_HEALTH_STATISTICS,
        WHO_HEALTH_DATA
    )
except ImportError:
    PAKISTAN_HEALTH_STATISTICS = {"disease_burden": {}}
    WHO_HEALTH_DATA = {}


class RiskAssessorAgent(BaseAgent):
    """
    Assesses health risks based on symptoms using Pakistan health statistics.
    Maps symptoms to potential conditions and their prevalence in Pakistan.
    """
    
    def __init__(self, rag_service=None, vertex_service=None):
        super().__init__(
            name="RiskAssessor",
            role=AgentRole.RISK_ASSESSOR,
            description="Identifies health risks using Pakistan health statistics and WHO data",
            rag_service=rag_service,
            vertex_ai_service=vertex_service
        )
        
        # Risk mapping based on Pakistan Bureau of Statistics data
        self.RISK_MAPPING = {
            "fever": {
                "conditions": [
                    {
                        "name": "Typhoid",
                        "prevalence": "493/100,000 in Pakistan",
                        "severity": "HIGH",
                        "warning": "70% is now drug-resistant (XDR) - complete full antibiotic course!",
                        "source": "Pakistan Health Ministry / WHO"
                    },
                    {
                        "name": "Dengue",
                        "prevalence": "50,000+ cases/year",
                        "severity": "HIGH",
                        "warning": "Do NOT take aspirin! Peak: Aug-Nov",
                        "source": "Pakistan Health Ministry"
                    },
                    {
                        "name": "Malaria",
                        "prevalence": "300,000 cases/year",
                        "severity": "MEDIUM",
                        "source": "WHO Pakistan"
                    }
                ],
                "risk_level": "MEDIUM-HIGH"
            },
            
            "cough": {
                "conditions": [
                    {
                        "name": "Tuberculosis",
                        "prevalence": "259/100,000 - 5th highest globally",
                        "severity": "HIGH",
                        "warning": "If >2 weeks with weight loss, GET TB TEST! TB is CURABLE.",
                        "source": "WHO Global TB Report"
                    },
                    {
                        "name": "Pneumonia",
                        "prevalence": "Common, especially in children",
                        "severity": "MEDIUM-HIGH",
                        "source": "WHO IMCI Guidelines"
                    }
                ],
                "risk_level": "MEDIUM"
            },
            
            "diarrhea": {
                "conditions": [
                    {
                        "name": "Gastroenteritis",
                        "prevalence": "Very common, 53,000 child deaths/year",
                        "severity": "HIGH for children",
                        "warning": "START ORS IMMEDIATELY - saves lives!",
                        "source": "WHO/UNICEF"
                    },
                    {
                        "name": "Typhoid",
                        "prevalence": "493/100,000",
                        "severity": "HIGH",
                        "source": "Pakistan Health Ministry"
                    }
                ],
                "risk_level": "MEDIUM-HIGH"
            },
            
            "fatigue": {
                "conditions": [
                    {
                        "name": "Anemia",
                        "prevalence": "41% women, 62% children in Pakistan",
                        "severity": "MEDIUM",
                        "warning": "Very common! Get tested. Eat kaleji, palak, channay.",
                        "source": "Pakistan Bureau of Statistics / PDHS"
                    },
                    {
                        "name": "Vitamin D Deficiency",
                        "prevalence": "66% of population, 73% women",
                        "severity": "MEDIUM",
                        "warning": "Get 15-20 min morning sunlight daily.",
                        "source": "Pakistan Medical Studies"
                    },
                    {
                        "name": "Diabetes",
                        "prevalence": "26.3% adults (33 million)",
                        "severity": "HIGH",
                        "warning": "50% don't know they have it! Get fasting sugar test.",
                        "source": "IDF Diabetes Atlas / Pakistan"
                    }
                ],
                "risk_level": "MEDIUM"
            },
            
            "headache": {
                "conditions": [
                    {
                        "name": "Hypertension",
                        "prevalence": "33% adults (40 million)",
                        "severity": "HIGH",
                        "warning": "Silent killer - only 6% controlled. CHECK YOUR BP!",
                        "source": "National Health Survey Pakistan"
                    },
                    {
                        "name": "Dehydration",
                        "prevalence": "Common in hot climate",
                        "severity": "LOW-MEDIUM",
                        "source": "WHO Guidelines"
                    },
                    {
                        "name": "Dengue",
                        "prevalence": "Seasonal - Aug-Nov",
                        "severity": "HIGH if with fever",
                        "source": "Pakistan Health Ministry"
                    }
                ],
                "risk_level": "MEDIUM"
            },
            
            "chest_pain": {
                "conditions": [
                    {
                        "name": "Heart Attack",
                        "prevalence": "Leading cause of death",
                        "severity": "CRITICAL",
                        "warning": "EMERGENCY - Call 1122 immediately!",
                        "source": "WHO Cardiovascular"
                    }
                ],
                "risk_level": "CRITICAL"
            },
            
            "breathing_difficulty": {
                "conditions": [
                    {
                        "name": "Pneumonia",
                        "prevalence": "Common",
                        "severity": "HIGH",
                        "source": "WHO IMCI"
                    },
                    {
                        "name": "Asthma",
                        "prevalence": "5-7% population",
                        "severity": "MEDIUM-HIGH",
                        "source": "Pakistan Chest Society"
                    }
                ],
                "risk_level": "HIGH"
            },
            
            "joint_pain": {
                "conditions": [
                    {
                        "name": "Vitamin D Deficiency",
                        "prevalence": "66% population",
                        "severity": "MEDIUM",
                        "source": "Pakistan Medical Studies"
                    },
                    {
                        "name": "Dengue/Chikungunya",
                        "prevalence": "Seasonal",
                        "severity": "HIGH if with fever",
                        "source": "Pakistan Health Ministry"
                    }
                ],
                "risk_level": "MEDIUM"
            },
            
            "skin_rash": {
                "conditions": [
                    {
                        "name": "Dengue",
                        "prevalence": "Seasonal - rash appears day 3-4",
                        "severity": "HIGH",
                        "warning": "If with fever - check platelets!",
                        "source": "WHO Dengue Guidelines"
                    },
                    {
                        "name": "Allergy",
                        "prevalence": "Common",
                        "severity": "LOW-MEDIUM",
                        "source": "General"
                    }
                ],
                "risk_level": "MEDIUM"
            },
            
            "stomach_pain": {
                "conditions": [
                    {
                        "name": "Typhoid",
                        "prevalence": "493/100,000",
                        "severity": "HIGH",
                        "warning": "If with fever - get tested",
                        "source": "Pakistan Health Ministry"
                    },
                    {
                        "name": "Appendicitis",
                        "prevalence": "Common",
                        "severity": "HIGH if right lower pain",
                        "warning": "Right lower pain with fever = EMERGENCY",
                        "source": "NIH Guidelines"
                    }
                ],
                "risk_level": "MEDIUM"
            }
        }
    
    async def process(self, context: AgentContext) -> AgentContext:
        """Assess risks based on identified symptoms"""
        
        symptoms = context.symptoms or []
        identified_risks = []
        overall_risk_level = "LOW"
        
        risk_levels = {"LOW": 1, "MEDIUM": 2, "MEDIUM-HIGH": 3, "HIGH": 4, "CRITICAL": 5}
        max_risk = 1
        
        for symptom in symptoms:
            if symptom in self.RISK_MAPPING:
                risk_data = self.RISK_MAPPING[symptom]
                
                for condition in risk_data.get("conditions", []):
                    risk_entry = {
                        "symptom": symptom,
                        "condition": condition["name"],
                        "prevalence": condition.get("prevalence", "Unknown"),
                        "severity": condition.get("severity", "MEDIUM"),
                        "warning": condition.get("warning", ""),
                        "source": condition.get("source", "")
                    }
                    identified_risks.append(risk_entry)
                    
                    # Track max risk
                    risk_value = risk_levels.get(condition.get("severity", "MEDIUM").split("-")[0], 2)
                    max_risk = max(max_risk, risk_value)
                
                # Check symptom-level risk
                symptom_risk = risk_levels.get(risk_data.get("risk_level", "MEDIUM"), 2)
                max_risk = max(max_risk, symptom_risk)
        
        # Determine overall risk level
        for level, value in risk_levels.items():
            if value == max_risk:
                overall_risk_level = level
                break
        
        # Check for critical combinations
        if "fever" in symptoms and "headache" in symptoms:
            context.safety_flags.append("Fever + headache: Consider dengue or typhoid")
        
        if "cough" in symptoms and any(s in symptoms for s in ["fatigue", "fever"]):
            context.safety_flags.append("Cough + fatigue/fever: TB screening recommended (Pakistan has high TB burden)")
        
        if "chest_pain" in symptoms or "breathing_difficulty" in symptoms:
            overall_risk_level = "CRITICAL"
            context.is_emergency = True
        
        # Update context
        context.identified_risks = identified_risks
        context.health_indicators["risk_level"] = overall_risk_level
        
        # Log decision
        decision = AgentDecision(
            agent_name=self.name,
            decision=f"Risk Level: {overall_risk_level}. Identified {len(identified_risks)} potential conditions.",
            reasoning=f"Mapped {len(symptoms)} symptoms to Pakistan health statistics. High-prevalence conditions prioritized.",
            confidence=0.8,
            inputs_used=["symptoms", "PAKISTAN_HEALTH_STATISTICS", "WHO_HEALTH_DATA"],
            language=context.user_language
        )
        context.decisions.append(decision)
        
        return context
    
    def get_explanation(self, context: AgentContext, language: str = "en") -> str:
        """Generate human-readable explanation of risk assessment"""
        
        risks = context.identified_risks or []
        risk_level = context.health_indicators.get("risk_level", "UNKNOWN")
        
        if not risks:
            explanations = {
                "en": "No specific health risks identified based on your symptoms.",
                "ur": "آپ کی علامات کی بنیاد پر کوئی مخصوص خطرہ نہیں ملا۔",
                "roman_urdu": "Aapki symptoms se koi specific risk nahi mila."
            }
        else:
            top_conditions = list(set([r["condition"] for r in risks[:3]]))
            conditions_str = ", ".join(top_conditions)
            
            explanations = {
                "en": f"Risk Level: {risk_level}. Based on Pakistan health data, your symptoms may indicate: {conditions_str}. Data from Pakistan Bureau of Statistics and WHO.",
                "ur": f"خطرے کی سطح: {risk_level}۔ پاکستان کے صحت کے اعداد و شمار کے مطابق، آپ کی علامات ممکنہ طور پر: {conditions_str}۔",
                "roman_urdu": f"Risk Level: {risk_level}. Pakistan health data ke mutabiq, symptoms indicate kar sakti hain: {conditions_str}."
            }
        
        return explanations.get(language, explanations["en"])

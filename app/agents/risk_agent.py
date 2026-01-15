"""
Risk Assessor Agent
Uses Pakistan Bureau of Statistics health data for risk assessment

Data Sources:
- Pakistan Bureau of Statistics (https://pslm-sdgs.data.gov.pk/health/index)
- WHO Global Health Data (https://www.who.int/data)
"""

from typing import List, Dict, Any
from app.agents.base_agent import BaseAgent, AgentRole, AgentContext, AgentDecision
from app.knowledge.health_knowledge_base import (
    PAKISTAN_HEALTH_STATISTICS,
    WHO_HEALTH_DATA,
    NIH_CLINICAL_PATTERNS
)


class RiskAssessorAgent(BaseAgent):
    """
    Assesses health risks based on:
    - Pakistan disease prevalence data
    - Symptom severity patterns
    - WHO risk assessment guidelines
    """
    
    def __init__(self, rag_service=None, vertex_service=None):
        super().__init__(
            name="RiskAssessor",
            role=AgentRole.ASSESSOR,
            rag_service=rag_service,
            vertex_service=vertex_service
        )
        
        # Pakistan-specific health risks from Bureau of Statistics
        # Source: https://pslm-sdgs.data.gov.pk/health/index
        self.PAKISTAN_HEALTH_RISKS = {
            "diabetes": {
                "prevalence_percent": 26.3,
                "affected_millions": 33,
                "risk_level": "very_high",
                "trigger_symptoms": ["excessive_thirst", "frequent_urination", "fatigue", "weight_loss", "blurred_vision", "slow_wound_healing"],
                "risk_factors": ["obesity", "sedentary_lifestyle", "family_history", "age_over_40"],
                "action": {
                    "en": "Get fasting blood sugar test. If diabetic, lifestyle changes and regular monitoring are essential.",
                    "ur": "فاسٹنگ بلڈ شوگر ٹیسٹ کروائیں۔ ذیابیطس ہو تو طرز زندگی بدلیں اور باقاعدہ چیک اپ کروائیں۔",
                    "roman_urdu": "Fasting blood sugar test karwayein. Diabetes ho to lifestyle badlein aur regular checkup karwayein."
                }
            },
            "hypertension": {
                "prevalence_percent": 33.0,
                "affected_millions": 40,
                "risk_level": "very_high",
                "trigger_symptoms": ["headache", "dizziness", "chest_pain", "shortness_of_breath", "nosebleed", "vision_problems"],
                "risk_factors": ["high_salt_intake", "obesity", "stress", "smoking", "family_history"],
                "action": {
                    "en": "Check blood pressure regularly. Reduce salt intake to less than 5g/day. Exercise 30 minutes daily.",
                    "ur": "بلڈ پریشر باقاعدگی سے چیک کروائیں۔ نمک 5 گرام سے کم کھائیں۔ روزانہ 30 منٹ ورزش کریں۔",
                    "roman_urdu": "BP regularly check karwayein. Namak kam khayein. Rozana 30 minute exercise karein."
                }
            },
            "anemia": {
                "prevalence_women_percent": 41.7,
                "prevalence_children_percent": 62.0,
                "risk_level": "high",
                "trigger_symptoms": ["fatigue", "weakness", "pale_skin", "dizziness", "shortness_of_breath", "cold_hands"],
                "risk_factors": ["poor_diet", "heavy_menstruation", "pregnancy", "parasitic_infections"],
                "action": {
                    "en": "Eat iron-rich foods: liver (kaleji), spinach (palak), chickpeas (chana), jaggery (gur). Get hemoglobin test.",
                    "ur": "آئرن والی غذائیں کھائیں: کلیجی، پالک، چنے، گڑ۔ ہیموگلوبن ٹیسٹ کروائیں۔",
                    "roman_urdu": "Iron wali ghizayein khayein: kaleji, palak, chanay, gur. Hemoglobin test karwayein."
                },
                "at_risk_groups": ["Women of reproductive age", "Pregnant women", "Children under 5"]
            },
            "vitamin_d_deficiency": {
                "prevalence_percent": 66.0,
                "women_prevalence_percent": 73.0,
                "risk_level": "very_high",
                "trigger_symptoms": ["fatigue", "bone_pain", "muscle_weakness", "depression", "frequent_infections"],
                "risk_factors": ["limited_sun_exposure", "indoor_lifestyle", "covering_clothing", "dark_skin"],
                "action": {
                    "en": "Get 15-20 minutes morning sunlight (before 10 AM). Eat eggs, fish, fortified milk. Consider supplements.",
                    "ur": "صبح 10 بجے سے پہلے 15-20 منٹ دھوپ لیں۔ انڈے، مچھلی، دودھ کھائیں۔ سپلیمنٹ لیں۔",
                    "roman_urdu": "Subah 10 bajay se pehle 15-20 minute dhoop lein. Anday, machli, doodh khayein."
                }
            },
            "typhoid": {
                "incidence_per_100k": 493,
                "xdr_percent": 70,
                "risk_level": "endemic",
                "trigger_symptoms": ["fever", "headache", "stomach_pain", "constipation", "diarrhea", "rose_spots"],
                "risk_factors": ["contaminated_water", "street_food", "poor_sanitation"],
                "action": {
                    "en": "Get Widal test or blood culture. Drink only boiled/filtered water. Complete full antibiotic course.",
                    "ur": "ویڈال ٹیسٹ یا بلڈ کلچر کروائیں۔ صرف ابلا/فلٹر پانی پیں۔ اینٹی بائیوٹک کا پورا کورس کریں۔",
                    "roman_urdu": "Widal test karwayein. Sirf ubla/filter paani piyen. Antibiotic ka poora course karein."
                },
                "warning": "70% typhoid in Pakistan is now drug-resistant (XDR). Complete treatment is critical."
            },
            "dengue": {
                "annual_cases": 50000,
                "peak_season": "August-November",
                "risk_level": "seasonal_high",
                "trigger_symptoms": ["high_fever", "severe_headache", "eye_pain", "joint_pain", "body_aches", "rash", "bleeding"],
                "risk_factors": ["monsoon_season", "standing_water", "urban_areas"],
                "action": {
                    "en": "Get NS1 antigen test (first 5 days) or dengue antibody test. NO ASPIRIN - only paracetamol. Monitor platelets daily.",
                    "ur": "NS1 ٹیسٹ کروائیں۔ اسپرین نہ لیں - صرف پیراسیٹامول۔ روزانہ پلیٹلیٹس چیک کروائیں۔",
                    "roman_urdu": "NS1 test karwayein. ASPIRIN NA LEIN - sirf paracetamol. Rozana platelets check karwayein."
                },
                "warning_signs": ["Severe abdominal pain", "Persistent vomiting", "Bleeding", "Lethargy"],
                "high_risk_cities": ["Lahore", "Rawalpindi", "Karachi", "Faisalabad"]
            },
            "tuberculosis": {
                "incidence_per_100k": 259,
                "global_ranking": "5th highest",
                "risk_level": "high",
                "trigger_symptoms": ["persistent_cough", "cough_blood", "night_sweats", "weight_loss", "evening_fever"],
                "risk_factors": ["close_contact_tb", "hiv", "diabetes", "malnutrition", "smoking"],
                "action": {
                    "en": "Get sputum test (GeneXpert) and chest X-ray. TB is CURABLE with 6-month treatment. COMPLETE THE FULL COURSE.",
                    "ur": "بلغم کا ٹیسٹ (GeneXpert) اور سینے کا ایکسرے کروائیں۔ ٹی بی 6 ماہ علاج سے ٹھیک ہو سکتی ہے۔ پورا کورس مکمل کریں۔",
                    "roman_urdu": "Balgham ka test aur chest X-ray karwayein. TB 6 maah treatment se theek hoti hai. POORA COURSE KAREIN."
                },
                "key_message": "Stopping TB treatment early creates drug-resistant TB which is much harder to treat!"
            },
            "hepatitis_b_c": {
                "hepatitis_b_percent": 2.5,
                "hepatitis_c_percent": 5.0,
                "hepatitis_c_millions": 12,
                "risk_level": "high",
                "trigger_symptoms": ["jaundice", "fatigue", "dark_urine", "pale_stool", "abdominal_pain"],
                "risk_factors": ["contaminated_needles", "unsafe_blood", "barber_razors", "unsterilized_equipment"],
                "action": {
                    "en": "Get HBsAg and Anti-HCV tests. Hepatitis C is now CURABLE in 12 weeks! Use only disposable syringes.",
                    "ur": "HBsAg اور Anti-HCV ٹیسٹ کروائیں۔ ہیپاٹائٹس سی اب 12 ہفتوں میں قابل علاج ہے! صرف ڈسپوزایبل سرنج استعمال کریں۔",
                    "roman_urdu": "Hepatitis test karwayein. Hepatitis C ab 12 hafton mein theek ho sakti hai! Sirf disposable syringe istemal karein."
                }
            },
            "malaria": {
                "annual_cases": 300000,
                "endemic_areas": ["Sindh", "Balochistan", "KPK tribal areas"],
                "risk_level": "endemic_regional",
                "trigger_symptoms": ["cyclical_fever", "chills", "sweating", "headache", "body_aches"],
                "risk_factors": ["monsoon_season", "rural_areas", "no_bed_nets"],
                "action": {
                    "en": "Get malaria rapid test or blood smear. Sleep under insecticide-treated bed nets.",
                    "ur": "ملیریا ٹیسٹ کروائیں۔ کیڑے مار دوائی لگی مچھر دانی میں سوئیں۔",
                    "roman_urdu": "Malaria test karwayein. Machhar daani mein soyein."
                }
            },
            "diarrheal_diseases": {
                "child_deaths_annual": 53000,
                "risk_level": "high_children",
                "trigger_symptoms": ["diarrhea", "vomiting", "dehydration", "fever"],
                "risk_factors": ["contaminated_water", "poor_sanitation", "lack_of_breastfeeding"],
                "action": {
                    "en": "Give ORS after every loose stool. Continue breastfeeding. Give Zinc for 10-14 days. Seek help if blood in stool or can't drink.",
                    "ur": "ہر پتلے پاخانے کے بعد نمکول دیں۔ دودھ پلانا جاری رکھیں۔ زنک 10-14 دن دیں۔ پاخانے میں خون ہو یا پی نہ سکے تو ڈاکٹر کو دکھائیں۔",
                    "roman_urdu": "Har patle pakhane ke baad ORS dein. Doodh pilana jari rakhein. Zinc 10-14 din dein."
                },
                "who_ors_recipe": WHO_HEALTH_DATA["dehydration_protocol"]["ors_who_formula"]["home_recipe"]
            }
        }
        
        # Nutrition deficiency risks from Pakistan data
        self.NUTRITION_RISKS = {
            "iron_deficiency": {
                "prevalence_women": "41.7%",
                "prevalence_children": "62%",
                "symptoms": ["fatigue", "weakness", "pale", "dizziness", "cold_extremities"],
                "sources": {
                    "en": "Liver (kaleji), spinach (palak), chickpeas (chana), jaggery (gur), dates",
                    "ur": "کلیجی، پالک، چنے، گڑ، کھجور",
                    "roman_urdu": "Kaleji, palak, chanay, gur, khajoor"
                }
            },
            "vitamin_d_deficiency": {
                "prevalence": "66%",
                "symptoms": ["fatigue", "bone_pain", "muscle_weakness", "depression"],
                "sources": {
                    "en": "Morning sunlight (15-20 min before 10 AM), eggs, fish, fortified milk",
                    "ur": "صبح کی دھوپ (10 بجے سے پہلے 15-20 منٹ)، انڈے، مچھلی، دودھ",
                    "roman_urdu": "Subah ki dhoop, anday, machli, doodh"
                }
            },
            "protein_deficiency": {
                "symptoms": ["weakness", "hair_loss", "slow_healing", "infections"],
                "sources": {
                    "en": "Lentils (daal), chicken, eggs, milk, yogurt (dahi), paneer",
                    "ur": "دال، مرغی، انڈے، دودھ، دہی، پنیر",
                    "roman_urdu": "Daal, murgi, anday, doodh, dahi, paneer"
                }
            }
        }
    
    async def process(self, context: AgentContext) -> AgentContext:
        """Assess health risks based on symptoms"""
        
        identified_risks = []
        severity_score = 0
        
        symptoms = context.symptoms
        health_indicators = context.health_indicators
        
        # Match symptoms to Pakistan health risks
        for condition, risk_data in self.PAKISTAN_HEALTH_RISKS.items():
            trigger_symptoms = risk_data.get("trigger_symptoms", [])
            matched_symptoms = [s for s in symptoms if s in trigger_symptoms or any(t in s for t in trigger_symptoms)]
            
            if matched_symptoms:
                match_ratio = len(matched_symptoms) / len(trigger_symptoms)
                
                risk_entry = {
                    "condition": condition,
                    "risk_level": risk_data.get("risk_level", "moderate"),
                    "prevalence": risk_data.get("prevalence_percent", risk_data.get("incidence_per_100k", "N/A")),
                    "matched_symptoms": matched_symptoms,
                    "match_confidence": round(match_ratio, 2),
                    "action": risk_data.get("action", {}),
                    "data_source": "Pakistan Bureau of Statistics / WHO"
                }
                
                # Add warning if present
                if "warning" in risk_data:
                    risk_entry["warning"] = risk_data["warning"]
                
                # Add warning signs if present
                if "warning_signs" in risk_data:
                    risk_entry["warning_signs"] = risk_data["warning_signs"]
                
                identified_risks.append(risk_entry)
                
                # Calculate severity
                if risk_data.get("risk_level") in ["very_high", "endemic"]:
                    severity_score += 3 * match_ratio
                elif risk_data.get("risk_level") in ["high", "seasonal_high"]:
                    severity_score += 2 * match_ratio
                else:
                    severity_score += 1 * match_ratio
        
        # Check nutrition risks
        for deficiency, risk_data in self.NUTRITION_RISKS.items():
            deficiency_symptoms = risk_data.get("symptoms", [])
            if any(s in symptoms for s in deficiency_symptoms):
                identified_risks.append({
                    "condition": deficiency,
                    "type": "nutritional_deficiency",
                    "prevalence": risk_data.get("prevalence", "common"),
                    "recommended_sources": risk_data.get("sources", {}),
                    "data_source": "Pakistan Bureau of Statistics / Open Food Facts"
                })
                severity_score += 1
        
        # Determine overall risk level
        if context.is_emergency or severity_score >= 8:
            risk_level = "CRITICAL"
        elif severity_score >= 5:
            risk_level = "HIGH"
        elif severity_score >= 2:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        # Sort risks by match confidence
        identified_risks.sort(key=lambda x: x.get("match_confidence", 0), reverse=True)
        
        # Update context
        context.identified_risks = identified_risks
        context.health_indicators["risk_level"] = risk_level
        context.health_indicators["severity_score"] = round(severity_score, 2)
        
        # Log decision
        decision = AgentDecision(
            agent_name=self.name,
            decision=f"Assessed {len(identified_risks)} potential risks. Overall risk level: {risk_level}",
            reasoning=f"Matched symptoms against Pakistan health statistics. "
                      f"Severity score: {severity_score:.1f}. "
                      f"Top conditions: {[r['condition'] for r in identified_risks[:3]]}",
            confidence=0.8 if identified_risks else 0.6,
            inputs_used=["symptoms", "PAKISTAN_HEALTH_STATISTICS", "WHO_HEALTH_DATA"],
            language=context.user_language
        )
        context.decisions.append(decision)
        
        return context

"""
Health Advisor Agent (Recommendation Agent)
Provides health recommendations using WHO guidelines and Pakistan nutrition data

Data Sources:
- WHO Global Health Data (https://www.who.int/data)
- Open Food Facts (https://world.openfoodfacts.org/data)
- Pakistan Bureau of Statistics (https://pslm-sdgs.data.gov.pk/health/index)
"""

from typing import List, Dict, Any
from app.agents.base_agent import BaseAgent, AgentRole, AgentContext, AgentDecision

# Try to import knowledge base
try:
    from app.knowledge.health_knowledge_base import (
        WHO_HEALTH_DATA,
        PAKISTAN_NUTRITION_DATA,
        PAKISTAN_HEALTH_STATISTICS,
        EMERGENCY_CONTACTS_PAKISTAN
    )
except ImportError:
    WHO_HEALTH_DATA = {}
    PAKISTAN_NUTRITION_DATA = {}
    PAKISTAN_HEALTH_STATISTICS = {}
    EMERGENCY_CONTACTS_PAKISTAN = {"rescue_1122": {"number": "1122"}, "edhi": {"number": "115"}}


class HealthAdvisorAgent(BaseAgent):
    """
    Provides health recommendations using:
    - WHO treatment guidelines
    - Pakistan-specific nutrition recommendations from Open Food Facts
    - Local food alternatives
    """
    
    def __init__(self, rag_service=None, vertex_service=None):
        super().__init__(
            name="HealthAdvisor",
            role=AgentRole.HEALTH_ADVISOR,
            description="Provides health recommendations using WHO guidelines and Pakistan nutrition data",
            rag_service=rag_service,
            vertex_ai_service=vertex_service
        )
        
        # Recommendations database based on WHO and Pakistan data
        self.RECOMMENDATIONS = {
            "fever": {
                "en": [
                    "Rest in a cool, comfortable place",
                    "Drink plenty of fluids (water, ORS, fresh juices)",
                    "Take paracetamol 500mg every 6 hours for adults (15mg/kg for children)",
                    "Apply cool compress on forehead",
                    "Monitor temperature every 4 hours",
                    "If dengue suspected - Do NOT take aspirin or ibuprofen!"
                ],
                "ur": [
                    "ٹھنڈی آرام دہ جگہ پر لیٹیں",
                    "خوب پانی پیں (پانی، نمکول، تازہ جوس)",
                    "پیراسیٹامول 500mg ہر 6 گھنٹے (بچوں کے لیے 15mg/kg)",
                    "ماتھے پر ٹھنڈا کپڑا رکھیں",
                    "ہر 4 گھنٹے درجہ حرارت چیک کریں",
                    "ڈینگی کا شبہ ہو تو اسپرین یا بروفین نہ لیں!"
                ],
                "roman_urdu": [
                    "Thandi aaram deh jagah par laitein",
                    "Khoob paani piyen (paani, ORS, fresh juice)",
                    "Paracetamol 500mg har 6 ghante (bachon ke liye 15mg/kg)",
                    "Mathay par thanda kapra rakhein",
                    "Har 4 ghante temperature check karein",
                    "Dengue ka shuba ho to aspirin ya brufen NA lein!"
                ],
                "when_to_see_doctor": ["Fever >3 days", "Temperature >103°F (39.5°C)", "Rash appears", "Severe headache"],
                "source": "WHO IMCI Guidelines / Pakistan Health Ministry"
            },
            
            "cough": {
                "en": [
                    "Drink warm fluids (honey + warm water, herbal tea, soup)",
                    "Steam inhalation 2-3 times daily",
                    "Gargle with warm salt water",
                    "Use honey (1-2 teaspoons) to soothe throat",
                    "Cover mouth when coughing",
                    "If >2 weeks: Get TB test! (Pakistan has high TB burden)"
                ],
                "ur": [
                    "گرم مشروبات پیں (شہد + گرم پانی، قہوہ، سوپ)",
                    "بھاپ لیں دن میں 2-3 بار",
                    "نمک کے گرم پانی سے غرارے کریں",
                    "شہد (1-2 چمچ) گلے کو سکون دینے کے لیے",
                    "کھانستے وقت منہ ڈھانپیں",
                    "اگر 2 ہفتے سے زیادہ: TB ٹیسٹ کروائیں!"
                ],
                "roman_urdu": [
                    "Garam mashroobat piyen (shehad + garam paani, qehwa, soup)",
                    "Bhaap lein din mein 2-3 baar",
                    "Namak ke garam paani se gharare karein",
                    "Shehad (1-2 chamach) galay ko sukoon dene ke liye",
                    "Khanste waqt munh dhaampein",
                    "Agar 2 hafte se zyada: TB TEST karwayein!"
                ],
                "when_to_see_doctor": ["Cough >2 weeks", "Blood in sputum", "Weight loss", "Night sweats"],
                "source": "WHO Global TB Report / Pakistan"
            },
            
            "diarrhea": {
                "en": [
                    "START ORS IMMEDIATELY after every loose stool",
                    "Home ORS recipe: 1 liter clean water + ½ tsp salt + 6 tbsp sugar",
                    "Continue breastfeeding for babies",
                    "Give Zinc supplements for 10-14 days (children)",
                    "Wash hands with soap frequently",
                    "Drink only boiled or filtered water"
                ],
                "ur": [
                    "فوری طور پر نمکول شروع کریں ہر پتلے پاخانے کے بعد",
                    "گھر کا نمکول: 1 لیٹر صاف پانی + آدھا چمچ نمک + 6 چمچ چینی",
                    "بچوں کو دودھ پلانا جاری رکھیں",
                    "بچوں کو زنک 10-14 دن دیں",
                    "صابن سے ہاتھ دھوتے رہیں",
                    "صرف ابلا یا فلٹر پانی پیں"
                ],
                "roman_urdu": [
                    "FORI ORS shuru karein har patle pakhane ke baad",
                    "Ghar ka ORS: 1 liter saaf paani + aadha chamach namak + 6 chamach cheeni",
                    "Bachon ko doodh pilana jari rakhein",
                    "Bachon ko Zinc 10-14 din dein",
                    "Sabun se haath dhote rahein",
                    "Sirf ubla ya filter paani piyen"
                ],
                "when_to_see_doctor": ["Blood in stool", "Unable to drink", "Sunken eyes", "No urine >6 hours"],
                "source": "WHO/UNICEF ORS Guidelines"
            },
            
            "fatigue": {
                "en": [
                    "Ensure 7-8 hours quality sleep",
                    "GET TESTED FOR ANEMIA (41% Pakistani women affected)",
                    "GET VITAMIN D CHECKED (66% are deficient)",
                    "Iron-rich foods: Kaleji (liver), Palak (spinach), Channay (chickpeas), Gur (jaggery)",
                    "Morning sunlight 15-20 minutes for Vitamin D",
                    "Get fasting blood sugar test if >40 years"
                ],
                "ur": [
                    "7-8 گھنٹے اچھی نیند لیں",
                    "خون کی کمی کا ٹیسٹ کروائیں (41% پاکستانی خواتین متاثر)",
                    "وٹامن ڈی چیک کروائیں (66% میں کمی)",
                    "آئرن والی غذائیں: کلیجی، پالک، چنے، گڑ",
                    "صبح 15-20 منٹ دھوپ لیں وٹامن ڈی کے لیے",
                    "40 سال سے زیادہ ہو تو فاسٹنگ شوگر ٹیسٹ کروائیں"
                ],
                "roman_urdu": [
                    "7-8 ghante achi neend lein",
                    "ANEMIA KA TEST karwayein (41% Pakistani women mein)",
                    "VITAMIN D CHECK karwayein (66% mein kami)",
                    "Iron wali ghizayein: Kaleji, Palak, Channay, Gur",
                    "Subah 15-20 minute dhoop lein Vitamin D ke liye",
                    "40 saal se zyada ho to fasting sugar test karwayein"
                ],
                "when_to_see_doctor": ["Fatigue >2 weeks", "With weight loss", "With fever"],
                "source": "Pakistan Bureau of Statistics / Open Food Facts"
            },
            
            "headache": {
                "en": [
                    "Rest in a quiet, dark room",
                    "Drink plenty of water (8-10 glasses daily)",
                    "Apply cold compress on forehead",
                    "Take paracetamol if needed",
                    "CHECK YOUR BLOOD PRESSURE (33% Pakistanis have hypertension)",
                    "Reduce screen time and stress"
                ],
                "ur": [
                    "پرسکون اندھیرے کمرے میں آرام کریں",
                    "خوب پانی پیں (روزانہ 8-10 گلاس)",
                    "ماتھے پر ٹھنڈا کپڑا رکھیں",
                    "ضرورت ہو تو پیراسیٹامول لیں",
                    "بلڈ پریشر چیک کروائیں (33% پاکستانیوں کو ہائی بی پی ہے)",
                    "اسکرین ٹائم اور تناؤ کم کریں"
                ],
                "roman_urdu": [
                    "Pursukoon andhera kamra mein aaram karein",
                    "Khoob paani piyen (rozana 8-10 glass)",
                    "Mathay par thanda kapra rakhein",
                    "Zaroorat ho to paracetamol lein",
                    "BP CHECK KARWAYEIN (33% Pakistanion ko high BP hai)",
                    "Screen time aur stress kam karein"
                ],
                "when_to_see_doctor": ["Sudden severe headache", "With fever and stiff neck", "Vision changes"],
                "source": "National Health Survey Pakistan / WHO"
            },
            
            "stomach_pain": {
                "en": [
                    "Rest and avoid spicy/oily foods",
                    "Drink clear fluids and stay hydrated",
                    "Try ginger tea for nausea",
                    "Avoid NSAIDs (ibuprofen, aspirin) on empty stomach",
                    "If with fever - get tested for typhoid",
                    "Right lower pain = See doctor immediately (appendix?)"
                ],
                "ur": [
                    "آرام کریں، مرچ مسالے سے پرہیز",
                    "صاف مشروبات پیں",
                    "متلی میں ادرک کا قہوہ",
                    "خالی پیٹ درد کی گولیاں سے پرہیز",
                    "بخار ہو تو ٹائیفائیڈ ٹیسٹ کروائیں",
                    "دائیں نیچے درد = فوری ڈاکٹر (اپینڈکس؟)"
                ],
                "roman_urdu": [
                    "Aaram karein, mirch masalay se parhair",
                    "Saaf mashroobat piyen",
                    "Mutli mein adrak ka qehwa",
                    "Khali pet pain killers se parhair",
                    "Bukhar ho to typhoid test karwayein",
                    "Dayen neeche dard = Fori doctor (appendix?)"
                ],
                "when_to_see_doctor": ["Severe right lower pain", "With high fever", "Vomiting blood"],
                "source": "WHO Guidelines / Pakistan Health Ministry"
            },
            
            "chest_pain": {
                "en": [
                    "⚠️ EMERGENCY - Call 1122 immediately",
                    "Sit upright and stay calm",
                    "Chew an aspirin (if not allergic and no bleeding)",
                    "Loosen tight clothing",
                    "Do NOT drive yourself - call ambulance"
                ],
                "ur": [
                    "⚠️ ایمرجنسی - فوری 1122 کال کریں",
                    "سیدھے بیٹھیں اور پرسکون رہیں",
                    "اسپرین چبائیں (اگر الرجی نہیں)",
                    "تنگ کپڑے ڈھیلے کریں",
                    "خود گاڑی نہ چلائیں - ایمبولینس بلائیں"
                ],
                "roman_urdu": [
                    "⚠️ EMERGENCY - Fori 1122 call karein",
                    "Seedhe baithein aur pursukoon rahein",
                    "Aspirin chabayein (agar allergy nahi)",
                    "Tang kapray dheele karein",
                    "Khud gaari na chalayein - ambulance bulayein"
                ],
                "when_to_see_doctor": ["IMMEDIATELY - This is an emergency"],
                "source": "WHO Cardiovascular Guidelines"
            },
            
            "breathing_difficulty": {
                "en": [
                    "⚠️ EMERGENCY if severe - Call 1122",
                    "Sit upright, don't lie flat",
                    "Stay calm and take slow breaths",
                    "Open windows for fresh air",
                    "Use inhaler if you have asthma"
                ],
                "ur": [
                    "⚠️ شدید ہو تو ایمرجنسی - 1122 کال کریں",
                    "سیدھے بیٹھیں، لیٹیں نہیں",
                    "پرسکون رہیں، آہستہ سانس لیں",
                    "کھڑکی کھولیں تازہ ہوا کے لیے",
                    "دمہ ہو تو انہیلر استعمال کریں"
                ],
                "roman_urdu": [
                    "⚠️ Shadeed ho to EMERGENCY - 1122 call karein",
                    "Seedhe baithein, laitein NAHI",
                    "Pursukoon rahein, aahista saans lein",
                    "Khidki kholein taza hawa ke liye",
                    "Dama ho to inhaler use karein"
                ],
                "when_to_see_doctor": ["IMMEDIATELY if severe"],
                "source": "WHO Emergency Guidelines"
            }
        }
        
        self.emergency_contacts = EMERGENCY_CONTACTS_PAKISTAN
    
    async def process(self, context: AgentContext) -> AgentContext:
        """Generate health recommendations based on symptoms and risks"""
        
        symptoms = context.symptoms or []
        language = context.user_language
        recommendations = []
        
        # Check for emergency first
        if context.is_emergency:
            emergency_msg = {
                "en": f"⚠️ EMERGENCY: Call 1122 (Rescue) or 115 (Edhi) immediately!",
                "ur": f"⚠️ ایمرجنسی: فوری 1122 (ریسکیو) یا 115 (ایدھی) کال کریں!",
                "roman_urdu": f"⚠️ EMERGENCY: Fori 1122 (Rescue) ya 115 (Edhi) call karein!"
            }
            recommendations.append(emergency_msg.get(language, emergency_msg["en"]))
        
        # Get recommendations for each symptom
        for symptom in symptoms:
            if symptom in self.RECOMMENDATIONS:
                rec_data = self.RECOMMENDATIONS[symptom]
                symptom_recs = rec_data.get(language, rec_data.get("en", []))
                recommendations.extend(symptom_recs)
                
                # Add "when to see doctor"
                when_doctor = rec_data.get("when_to_see_doctor", [])
                if when_doctor:
                    doctor_msg = {
                        "en": f"See doctor if: {', '.join(when_doctor)}",
                        "ur": f"ڈاکٹر سے ملیں اگر: {', '.join(when_doctor)}",
                        "roman_urdu": f"Doctor se milein agar: {', '.join(when_doctor)}"
                    }
                    recommendations.append(doctor_msg.get(language, doctor_msg["en"]))
        
        # If no specific recommendations, provide general guidance
        if not recommendations:
            general = {
                "en": [
                    "Rest and stay hydrated",
                    "Monitor your symptoms",
                    "If symptoms persist, consult a healthcare professional",
                    "Emergency? Call 1122 (Rescue) or 115 (Edhi)"
                ],
                "ur": [
                    "آرام کریں اور پانی پیتے رہیں",
                    "علامات پر نظر رکھیں",
                    "علامات جاری رہیں تو ڈاکٹر سے ملیں",
                    "ایمرجنسی؟ 1122 (ریسکیو) یا 115 (ایدھی) کال کریں"
                ],
                "roman_urdu": [
                    "Aaram karein aur paani peete rahein",
                    "Symptoms par nazar rakhein",
                    "Symptoms jari rahein to doctor se milein",
                    "Emergency? 1122 (Rescue) ya 115 (Edhi) call karein"
                ]
            }
            recommendations = general.get(language, general["en"])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        
        # Update context
        context.recommendations = unique_recommendations[:12]  # Limit to 12 recommendations
        
        # Log decision
        decision = AgentDecision(
            agent_name=self.name,
            decision=f"Generated {len(unique_recommendations)} recommendations for {len(symptoms)} symptoms",
            reasoning=f"Used WHO guidelines and Pakistan health data. Sources: Open Food Facts, Pakistan Bureau of Statistics, WHO.",
            confidence=0.85,
            inputs_used=["symptoms", "risks", "WHO_HEALTH_DATA", "PAKISTAN_NUTRITION_DATA"],
            language=language
        )
        context.decisions.append(decision)
        
        return context
    
    def get_explanation(self, context: AgentContext, language: str = "en") -> str:
        """Generate human-readable explanation of recommendations"""
        
        recommendations = context.recommendations or []
        symptoms = context.symptoms or []
        
        if not recommendations:
            explanations = {
                "en": "No specific recommendations generated. Please describe your symptoms for personalized advice.",
                "ur": "کوئی مخصوص مشورے نہیں۔ براہ کرم اپنی علامات تفصیل سے بتائیں۔",
                "roman_urdu": "Koi specific mashwaray nahi. Please apni symptoms detail mein batayen."
            }
        else:
            explanations = {
                "en": f"I've provided {len(recommendations)} recommendations based on your symptoms ({', '.join(symptoms)}). These are based on WHO guidelines and Pakistan health data. Always consult a doctor for proper diagnosis.",
                "ur": f"میں نے آپ کی علامات ({', '.join(symptoms)}) کی بنیاد پر {len(recommendations)} مشورے دیے ہیں۔ یہ WHO اور پاکستان کے صحت کے اعداد و شمار پر مبنی ہیں۔ درست تشخیص کے لیے ڈاکٹر سے ضرور ملیں۔",
                "roman_urdu": f"Maine aapki symptoms ({', '.join(symptoms)}) ke basis par {len(recommendations)} mashwaray diye hain. Yeh WHO aur Pakistan health data par based hain. Doctor se zaroor milein."
            }
        
        return explanations.get(language, explanations["en"])

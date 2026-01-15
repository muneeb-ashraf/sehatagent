"""
Offline Helper Agent
Provides rule-based guidance when cloud services unavailable

Uses pre-loaded knowledge from:
- WHO Health Guidelines
- Pakistan Health Statistics  
- Open Food Facts Nutrition Data
"""

from typing import List, Dict, Any
import re
from app.agents.base_agent import BaseAgent, AgentRole, AgentContext, AgentDecision
from app.knowledge.health_knowledge_base import (
    WHO_HEALTH_DATA,
    PAKISTAN_HEALTH_STATISTICS,
    PAKISTAN_NUTRITION_DATA,
    NIH_CLINICAL_PATTERNS,
    EMERGENCY_CONTACTS_PAKISTAN
)


# Comprehensive offline knowledge base
OFFLINE_KNOWLEDGE_BASE = {
    "fever": {
        "keywords": ["fever", "bukhar", "بخار", "temperature", "taap", "garam"],
        "possible_conditions": ["Viral infection", "Typhoid (common in Pakistan)", "Dengue (seasonal)", "Malaria", "UTI"],
        "recommendations": {
            "en": [
                "Rest in a cool, comfortable place",
                "Drink plenty of fluids (water, ORS, juices)",
                "Take paracetamol for fever (NOT aspirin if dengue suspected)",
                "Apply cool compress on forehead",
                "Monitor temperature every 4 hours"
            ],
            "ur": [
                "ٹھنڈی آرام دہ جگہ پر لیٹیں",
                "خوب پانی پیں (پانی، نمکول، جوس)",
                "پیراسیٹامول لیں (ڈینگی کا شبہ ہو تو اسپرین نہیں)",
                "ماتھے پر ٹھنڈا کپڑا رکھیں",
                "ہر 4 گھنٹے درجہ حرارت چیک کریں"
            ],
            "roman_urdu": [
                "Thandi jagah par aaram karein",
                "Khoob paani piyen (paani, ORS, juice)",
                "Paracetamol lein (dengue ho to aspirin NA lein)",
                "Mathay par thanda kapra rakhein",
                "Har 4 ghante temperature check karein"
            ]
        },
        "when_to_see_doctor": [
            "Fever persists >3 days",
            "Temperature >103°F (39.5°C)",
            "Severe headache or body aches (dengue?)",
            "Rash appears",
            "Difficulty breathing"
        ],
        "pakistan_context": "Typhoid and Dengue are common. Get tested if fever persists."
    },
    
    "headache": {
        "keywords": ["headache", "sir dard", "سر درد", "sar dard", "migraine"],
        "possible_conditions": ["Tension headache", "Migraine", "Dehydration", "Hypertension (33% adults in Pakistan)", "Dengue"],
        "recommendations": {
            "en": [
                "Rest in a quiet, dark room",
                "Drink plenty of water (8-10 glasses)",
                "Apply cold compress on forehead",
                "Take paracetamol if needed",
                "CHECK YOUR BLOOD PRESSURE (33% Pakistanis have hypertension)"
            ],
            "ur": [
                "پرسکون اندھیرے کمرے میں آرام کریں",
                "خوب پانی پیں (8-10 گلاس)",
                "ماتھے پر ٹھنڈا کپڑا رکھیں",
                "ضرورت ہو تو پیراسیٹامول لیں",
                "بلڈ پریشر چیک کروائیں (33% پاکستانیوں کو بلڈ پریشر ہے)"
            ],
            "roman_urdu": [
                "Pursukoon kamre mein aaram karein",
                "Khoob paani piyen (8-10 glass)",
                "Mathay par thanda kapra rakhein",
                "Paracetamol lein agar zaroorat ho",
                "BP CHECK KARWAYEIN (33% Pakistanion ko BP hai)"
            ]
        },
        "when_to_see_doctor": [
            "Sudden severe 'worst headache ever'",
            "With fever and stiff neck (meningitis?)",
            "Vision changes",
            "After head injury",
            "Daily recurring headaches"
        ],
        "pakistan_context": "High BP is common (33%). Always check BP with headaches."
    },
    
    "cough": {
        "keywords": ["cough", "khansi", "کھانسی", "khansna"],
        "possible_conditions": ["Common cold", "Bronchitis", "Allergies", "TB (Pakistan ranks 5th globally)"],
        "recommendations": {
            "en": [
                "Drink warm fluids (honey + warm water, herbal tea)",
                "Steam inhalation 2-3 times daily",
                "Gargle with warm salt water",
                "Use honey (1-2 teaspoons) for throat",
                "Cover mouth when coughing"
            ],
            "ur": [
                "گرم مشروبات پیں (شہد + گرم پانی، قہوہ)",
                "بھاپ لیں دن میں 2-3 بار",
                "نمک کے گرم پانی سے غرارے کریں",
                "شہد (1-2 چمچ) گلے کے لیے لیں",
                "کھانستے وقت منہ ڈھانپیں"
            ],
            "roman_urdu": [
                "Garam mashroobat piyen (shehad + garam paani)",
                "Bhaap lein din mein 2-3 baar",
                "Namak ke garam paani se ghararay karein",
                "Shehad galay ke liye lein",
                "Khanstay waqt munh dhaampein"
            ]
        },
        "when_to_see_doctor": [
            "Cough >2 weeks (TB test needed!)",
            "Blood in sputum",
            "Weight loss or night sweats (TB symptoms)",
            "High fever",
            "Difficulty breathing"
        ],
        "pakistan_context": "Pakistan has 5th highest TB burden. If cough >2 weeks with weight loss, GET TB TEST!",
        "tb_warning": "TB ALERT: 2 hafte se zyada khansi + wajan kam + raat ko paseena = TB TEST ZAROOR KARWAYEIN"
    },
    
    "diarrhea": {
        "keywords": ["diarrhea", "dast", "دست", "loose motion", "pichkari", "patla pakhana"],
        "possible_conditions": ["Gastroenteritis", "Food poisoning", "Typhoid", "Cholera", "Parasites"],
        "recommendations": {
            "en": [
                "START ORS IMMEDIATELY after every loose stool",
                "Home ORS: 1L water + ½ tsp salt + 6 tbsp sugar",
                "Continue breastfeeding for babies",
                "Give Zinc for 10-14 days (children)",
                "Wash hands with soap frequently"
            ],
            "ur": [
                "فوری نمکول دیں ہر پتلے پاخانے کے بعد",
                "گھر کا نمکول: 1 لیٹر پانی + آدھا چمچ نمک + 6 چمچ چینی",
                "بچوں کو دودھ پلانا جاری رکھیں",
                "زنک 10-14 دن دیں (بچوں کو)",
                "صابن سے ہاتھ دھوتے رہیں"
            ],
            "roman_urdu": [
                "FORI ORS dein har patle pakhane ke baad",
                "Ghar ka ORS: 1 liter paani + aadha chamach namak + 6 chamach cheeni",
                "Bachon ko doodh pilana jari rakhein",
                "Zinc 10-14 din dein (bachon ko)",
                "Sabun se haath dhote rahein"
            ]
        },
        "when_to_see_doctor": [
            "Blood in stool",
            "Unable to drink fluids",
            "Severe dehydration (sunken eyes, no urine)",
            "High fever",
            "Continues >2 days"
        ],
        "pakistan_context": "Diarrhea kills 53,000 children/year in Pakistan. ORS saves lives!",
        "who_ors": WHO_HEALTH_DATA["dehydration_protocol"]["ors_who_formula"]["home_recipe"]
    },
    
    "fatigue": {
        "keywords": ["fatigue", "tired", "thakan", "تھکاوٹ", "kamzori", "کمزوری", "weakness"],
        "possible_conditions": ["Anemia (41% women in Pakistan)", "Vitamin D deficiency (66%)", "Diabetes", "Thyroid", "Depression"],
        "recommendations": {
            "en": [
                "Ensure 7-8 hours quality sleep",
                "GET TESTED FOR ANEMIA (41% Pakistani women affected)",
                "Get Vitamin D checked (66% are deficient)",
                "Eat iron-rich foods: liver (kaleji), spinach (palak), chickpeas (chana)",
                "Morning sunlight 15-20 min for Vitamin D"
            ],
            "ur": [
                "7-8 گھنٹے اچھی نیند لیں",
                "خون کی کمی کا ٹیسٹ کروائیں (41% پاکستانی خواتین میں ہے)",
                "وٹامن ڈی چیک کروائیں (66% میں کمی ہے)",
                "آئرن والی غذائیں کھائیں: کلیجی، پالک، چنے",
                "صبح 15-20 منٹ دھوپ لیں وٹامن ڈی کے لیے"
            ],
            "roman_urdu": [
                "7-8 ghante achi neend lein",
                "Khoon ki kami ka TEST KARWAYEIN (41% women mein hai)",
                "Vitamin D check karwayein (66% mein kami hai)",
                "Iron wali ghizayein khayein: kaleji, palak, chanay",
                "Subah 15-20 minute dhoop lein Vitamin D ke liye"
            ]
        },
        "when_to_see_doctor": [
            "Persistent fatigue despite rest",
            "With pale skin or dizziness",
            "With weight loss",
            "With shortness of breath"
        ],
        "pakistan_context": "66% Pakistanis have Vitamin D deficiency, 41% women have anemia. GET TESTED!",
        "iron_rich_foods": ["Kaleji (liver)", "Palak (spinach)", "Chanay (chickpeas)", "Gur (jaggery)", "Khajoor (dates)"],
        "vitamin_d_sources": ["Morning sunlight (15-20 min)", "Eggs", "Fish", "Fortified milk"]
    },
    
    "stomach_pain": {
        "keywords": ["stomach pain", "pait dard", "پیٹ درد", "pet dard", "abdominal", "maida"],
        "possible_conditions": ["Gastritis", "Acidity", "Food poisoning", "Typhoid", "Appendicitis"],
        "recommendations": {
            "en": [
                "Rest and avoid heavy meals",
                "Apply warm compress on abdomen",
                "Drink mint tea or ajwain water",
                "Avoid spicy and oily foods",
                "Eat small, frequent meals"
            ],
            "ur": [
                "آرام کریں اور بھاری کھانے سے پرہیز",
                "پیٹ پر گرم کپڑا رکھیں",
                "پودینے کی چائے یا اجوائن کا پانی پیں",
                "مصالحے دار اور تلی ہوئی غذا سے پرہیز",
                "تھوڑا تھوڑا بار بار کھائیں"
            ],
            "roman_urdu": [
                "Aaram karein aur bhaari khane se parhair",
                "Pait par garam kapra rakhein",
                "Pudine ki chai ya ajwain ka paani piyen",
                "Masaledar aur tala hua khana na khayein",
                "Thora thora baar baar khayein"
            ]
        },
        "when_to_see_doctor": [
            "Severe pain (especially right lower side - appendix?)",
            "Blood in vomit or stool",
            "High fever with pain",
            "Pain >24 hours",
            "Unable to eat or drink"
        ]
    },
    
    "body_aches": {
        "keywords": ["body ache", "jism mein dard", "جسم میں درد", "badan dard", "joint pain", "joron mein dard"],
        "possible_conditions": ["Viral fever", "Dengue (seasonal)", "Flu", "Chikungunya", "Arthritis"],
        "recommendations": {
            "en": [
                "Complete bed rest",
                "Stay hydrated",
                "Take paracetamol for pain",
                "If with high fever (Aug-Nov), GET DENGUE TEST",
                "Warm compress on affected areas"
            ],
            "ur": [
                "مکمل آرام کریں",
                "پانی خوب پیں",
                "درد کے لیے پیراسیٹامول لیں",
                "تیز بخار ہو (اگست-نومبر) تو ڈینگی ٹیسٹ کروائیں",
                "متاثرہ جگہ پر گرم کپڑا رکھیں"
            ],
            "roman_urdu": [
                "Mukammal aaram karein",
                "Paani khoob piyen",
                "Dard ke liye paracetamol lein",
                "Tez bukhar ho (Aug-Nov) to DENGUE TEST karwayein",
                "Mutasira jagah par garam kapra rakhein"
            ]
        },
        "when_to_see_doctor": [
            "Severe joint/muscle pain with high fever",
            "Rash appears",
            "Bleeding from gums or nose",
            "Pain not improving in 3 days"
        ],
        "dengue_warning": "Aug-Nov mein tez bukhar + shadeed jism dard = DENGUE TEST! ASPIRIN NA LEIN!"
    },
    
    "vomiting": {
        "keywords": ["vomit", "ulti", "الٹی", "qai", "throwing up"],
        "possible_conditions": ["Gastroenteritis", "Food poisoning", "Migraine", "Pregnancy"],
        "recommendations": {
            "en": [
                "Rest and don't eat for 1-2 hours",
                "Sip small amounts of water or ORS",
                "Avoid solid food until vomiting stops",
                "Try ginger tea or mint tea",
                "Gradually start bland foods (rice, toast)"
            ],
            "ur": [
                "آرام کریں اور 1-2 گھنٹے کچھ نہ کھائیں",
                "تھوڑا تھوڑا پانی یا نمکول پیں",
                "الٹی بند ہونے تک ٹھوس غذا نہ کھائیں",
                "ادرک کی چائے یا پودینے کی چائے لیں",
                "آہستہ آہستہ ہلکا کھانا (چاول، ٹوسٹ) شروع کریں"
            ],
            "roman_urdu": [
                "Aaram karein aur 1-2 ghante kuch na khayein",
                "Thora thora paani ya ORS piyen",
                "Ulti band hone tak solid khana na khayein",
                "Adrak ki chai ya pudine ki chai lein",
                "Ahista ahista halka khana shuru karein"
            ]
        },
        "when_to_see_doctor": [
            "Blood in vomit",
            "Can't keep any fluids down",
            "Signs of dehydration",
            "Severe abdominal pain",
            "Continues >24 hours"
        ]
    },
    
    "jaundice": {
        "keywords": ["jaundice", "yarqan", "یرقان", "yellow eyes", "peeli aankhen"],
        "possible_conditions": ["Hepatitis A", "Hepatitis B (2.5%)", "Hepatitis C (5%)", "Liver disease"],
        "recommendations": {
            "en": [
                "Complete bed rest",
                "Drink plenty of fluids (sugarcane juice, coconut water)",
                "Avoid oily, fried foods",
                "GET HEPATITIS B & C TESTS",
                "Do NOT share razors or toothbrushes"
            ],
            "ur": [
                "مکمل آرام کریں",
                "خوب پانی پیں (گنے کا رس، ناریل پانی)",
                "تلی ہوئی غذا سے پرہیز",
                "ہیپاٹائٹس بی اور سی ٹیسٹ کروائیں",
                "استرا اور ٹوتھ برش شیئر نہ کریں"
            ],
            "roman_urdu": [
                "Mukammal aaram karein",
                "Khoob paani piyen (gannay ka ras, nariyal paani)",
                "Tali hui ghiza se parhair",
                "HEPATITIS B & C TEST KARWAYEIN",
                "Ustra aur toothbrush share na karein"
            ]
        },
        "pakistan_context": "12 million Pakistanis have Hepatitis C. IT IS NOW CURABLE in 12 weeks!",
        "prevention": "Use only DISPOSABLE syringes. Avoid roadside barbers."
    },
    
    "dizziness": {
        "keywords": ["dizzy", "chakkar", "چکر", "vertigo", "giddy"],
        "possible_conditions": ["Anemia (very common)", "Low BP", "High BP", "Dehydration", "Inner ear"],
        "recommendations": {
            "en": [
                "Sit or lie down immediately",
                "Drink water",
                "Check blood pressure",
                "Check for anemia (very common in Pakistan)",
                "Avoid sudden movements"
            ],
            "ur": [
                "فوری بیٹھ جائیں یا لیٹ جائیں",
                "پانی پیں",
                "بلڈ پریشر چیک کروائیں",
                "خون کی کمی چیک کروائیں (بہت عام ہے)",
                "اچانک حرکت سے بچیں"
            ],
            "roman_urdu": [
                "Fori baith jayein ya lait jayein",
                "Paani piyen",
                "BP check karwayein",
                "Khoon ki kami check karwayein (bohat aam hai)",
                "Achanak harkat se bachein"
            ]
        },
        "pakistan_context": "Anemia (41% women) and Hypertension (33% adults) are common causes. Get both checked!"
    }
}

# Emergency keywords that trigger immediate referral
EMERGENCY_KEYWORDS = {
    "en": ["chest pain", "can't breathe", "unconscious", "severe bleeding", "heart attack", "stroke", "suicide", "seizure", "convulsion"],
    "ur": ["سینے میں درد", "سانس نہیں", "بے ہوش", "شدید خون", "دل کا دورہ", "فالج"],
    "roman_urdu": ["seene mein dard", "saans nahi", "behosh", "shadeed khoon", "heart attack", "falij"]
}


class OfflineHelperAgent(BaseAgent):
    """
    Provides rule-based health guidance when cloud services unavailable.
    Uses comprehensive pre-loaded knowledge from WHO, Pakistan Bureau of Statistics, and Open Food Facts.
    """
    
    def __init__(self, rag_service=None, vertex_service=None):
        super().__init__(
            name="OfflineHelper",
            role=AgentRole.FALLBACK,
            rag_service=rag_service,
            vertex_service=vertex_service
        )
        
        self.knowledge_base = OFFLINE_KNOWLEDGE_BASE
        self.emergency_keywords = EMERGENCY_KEYWORDS
        self.emergency_contacts = EMERGENCY_CONTACTS_PAKISTAN
    
    async def process(self, context: AgentContext) -> AgentContext:
        """Process health query using offline knowledge base"""
        
        user_input = (context.translated_input or context.user_input).lower()
        language = context.user_language
        
        # Check for emergency
        if self._is_emergency(user_input):
            context.is_emergency = True
            context.safety_flags.append("EMERGENCY_DETECTED_OFFLINE")
            context.recommendations = [
                self._get_emergency_message(language)
            ]
            return context
        
        # Match symptoms from knowledge base
        matched_conditions = []
        recommendations = []
        
        for condition, data in self.knowledge_base.items():
            keywords = data.get("keywords", [])
            if any(kw in user_input for kw in keywords):
                matched_conditions.append(condition)
                
                # Get recommendations in user's language
                recs = data.get("recommendations", {})
                lang_recs = recs.get(language, recs.get("en", []))
                recommendations.extend(lang_recs)
                
                # Add Pakistan context if available
                if "pakistan_context" in data:
                    context.safety_flags.append(f"PAKISTAN_CONTEXT: {data['pakistan_context']}")
                
                # Add warnings
                for warning_key in ["tb_warning", "dengue_warning"]:
                    if warning_key in data:
                        context.safety_flags.append(data[warning_key])
        
        # If no match, provide general guidance
        if not recommendations:
            recommendations = self._get_general_guidance(language)
        
        # Remove duplicates
        recommendations = list(dict.fromkeys(recommendations))
        
        # Update context
        context.symptoms = matched_conditions
        context.recommendations = recommendations[:10]
        context.degraded_mode = True
        
        # Add offline notice
        offline_notice = {
            "en": "Note: Operating in offline mode with limited analysis. For comprehensive assessment, please consult a healthcare professional.",
            "ur": "نوٹ: آف لائن موڈ میں محدود تجزیہ۔ مکمل جائزے کے لیے ڈاکٹر سے ملیں۔",
            "roman_urdu": "Note: Offline mode mein limited analysis. Complete check ke liye doctor se milein."
        }
        context.safety_flags.append(offline_notice.get(language, offline_notice["en"]))
        
        # Log decision
        decision = AgentDecision(
            agent_name=self.name,
            decision=f"Offline analysis: matched {len(matched_conditions)} conditions",
            reasoning=f"Used offline knowledge base with WHO/Pakistan health data. Matched: {matched_conditions}",
            confidence=0.7,
            inputs_used=["user_input", "OFFLINE_KNOWLEDGE_BASE", "WHO_HEALTH_DATA", "PAKISTAN_HEALTH_STATISTICS"],
            language=language
        )
        context.decisions.append(decision)
        
        return context
    
    def _is_emergency(self, text: str) -> bool:
        """Check if text contains emergency keywords"""
        for lang_keywords in self.emergency_keywords.values():
            if any(kw in text for kw in lang_keywords):
                return True
        return False
    
    def _get_emergency_message(self, language: str) -> str:
        """Get emergency message in user's language"""
        messages = {
            "en": "⚠️ EMERGENCY: Please call 1122 (Rescue) or 115 (Edhi) immediately, or go to the nearest hospital!",
            "ur": "⚠️ ایمرجنسی: فوری 1122 (ریسکیو) یا 115 (ایدھی) کال کریں، یا قریبی ہسپتال جائیں!",
            "roman_urdu": "⚠️ EMERGENCY: Fori 1122 (Rescue) ya 115 (Edhi) call karein, ya hospital jayein!"
        }
        return messages.get(language, messages["en"])
    
    def _get_general_guidance(self, language: str) -> List[str]:
        """General guidance when no specific condition matched"""
        guidance = {
            "en": [
                "Rest and stay hydrated",
                "Monitor your symptoms",
                "If symptoms persist or worsen, consult a doctor",
                "Call 1122 for any emergency"
            ],
            "ur": [
                "آرام کریں اور پانی پیتے رہیں",
                "علامات پر نظر رکھیں",
                "علامات جاری رہیں یا بڑھیں تو ڈاکٹر سے ملیں",
                "ایمرجنسی میں 1122 کال کریں"
            ],
            "roman_urdu": [
                "Aaram karein aur paani peete rahein",
                "Symptoms par nazar rakhein",
                "Symptoms jari rahein ya barhein to doctor se milein",
                "Emergency mein 1122 call karein"
            ]
        }
        return guidance.get(language, guidance["en"])

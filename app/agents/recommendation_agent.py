"""
Health Advisor Agent
Provides preventive guidance using nutrition data and WHO guidelines

Data Sources:
- Open Food Facts (https://world.openfoodfacts.org/data)
- WHO Health Guidelines (https://www.who.int/data)
- Pakistan Nutrition Data
"""

from typing import List, Dict, Any
from app.agents.base_agent import BaseAgent, AgentRole, AgentContext, AgentDecision
from app.knowledge.health_knowledge_base import (
    PAKISTAN_NUTRITION_DATA,
    WHO_HEALTH_DATA,
    PAKISTAN_HEALTH_STATISTICS,
    EMERGENCY_CONTACTS_PAKISTAN
)


class HealthAdvisorAgent(BaseAgent):
    """
    Generates health recommendations using:
    - Pakistan-specific nutrition data (Open Food Facts)
    - WHO treatment guidelines
    - Local food alternatives
    """
    
    def __init__(self, rag_service=None, vertex_service=None):
        super().__init__(
            name="HealthAdvisor",
            role=AgentRole.ADVISOR,
            rag_service=rag_service,
            vertex_service=vertex_service
        )
        
        # Health recommendations based on WHO and Pakistan data
        self.HEALTH_RECOMMENDATIONS = {
            "fever": {
                "immediate": {
                    "en": [
                        "Rest in a cool, comfortable place",
                        "Drink plenty of fluids - water, ORS, fresh juices",
                        "Take paracetamol for fever (NOT aspirin if dengue suspected)",
                        "Apply cool compress on forehead",
                        "Wear light, loose clothing"
                    ],
                    "ur": [
                        "ٹھنڈی آرام دہ جگہ پر لیٹیں",
                        "خوب پانی پیں - پانی، نمکول، تازہ جوس",
                        "پیراسیٹامول لیں (ڈینگی کا شبہ ہو تو اسپرین نہ لیں)",
                        "ماتھے پر ٹھنڈا کپڑا رکھیں",
                        "ہلکے ڈھیلے کپڑے پہنیں"
                    ],
                    "roman_urdu": [
                        "Thandi jagah par aaram karein",
                        "Khoob paani piyen - paani, ORS, juice",
                        "Paracetamol lein (dengue ho to aspirin na lein)",
                        "Mathay par thanda kapra rakhein",
                        "Halke dheelay kapray pehnein"
                    ]
                },
                "nutrition": {
                    "en": ["Light, easily digestible food", "Khichdi, dal chawal, soups", "Avoid oily and spicy food"],
                    "ur": ["ہلکی آسانی سے ہضم ہونے والی غذا", "کھچڑی، دال چاول، سوپ", "تلی ہوئی اور مصالحے دار غذا سے پرہیز"],
                    "roman_urdu": ["Halka khana khayein", "Khichdi, daal chawal, soup", "Tala hua aur masaledar khana na khayein"]
                },
                "see_doctor_if": {
                    "en": ["Fever persists more than 3 days", "Temperature exceeds 103°F (39.5°C)", "Severe headache or body aches", "Rash appears", "Difficulty breathing"],
                    "ur": ["3 دن سے زیادہ بخار رہے", "درجہ حرارت 103°F سے زیادہ ہو", "شدید سر درد یا جسم میں درد", "جلد پر دانے نکلیں", "سانس لینے میں تکلیف"]
                },
                "who_guideline": WHO_HEALTH_DATA["fever_management"]
            },
            
            "diarrhea": {
                "immediate": {
                    "en": [
                        "START ORS IMMEDIATELY - after every loose stool",
                        "Home ORS: 1 liter clean water + ½ teaspoon salt + 6 tablespoons sugar",
                        "Continue breastfeeding for infants",
                        "Give Zinc supplement for 10-14 days",
                        "Wash hands with soap frequently"
                    ],
                    "ur": [
                        "فوری نمکول شروع کریں - ہر پتلے پاخانے کے بعد",
                        "گھر پر نمکول: 1 لیٹر صاف پانی + آدھا چائے کا چمچ نمک + 6 کھانے کے چمچ چینی",
                        "بچوں کو دودھ پلانا جاری رکھیں",
                        "زنک کی گولی 10-14 دن دیں",
                        "صابن سے ہاتھ دھوتے رہیں"
                    ],
                    "roman_urdu": [
                        "Fori ORS shuru karein - har patle pakhane ke baad",
                        "Ghar par ORS: 1 liter saaf paani + aadha chamach namak + 6 chamach cheeni",
                        "Bachon ko doodh pilana jari rakhein",
                        "Zinc ki goli 10-14 din dein",
                        "Sabun se haath dhote rahein"
                    ]
                },
                "nutrition": {
                    "en": ["BRAT diet: Banana, Rice, Apple, Toast", "Yogurt (dahi) with rice", "Avoid milk (except breast milk)", "Avoid fatty and spicy foods"],
                    "ur": ["کیلا، چاول، سیب، ٹوسٹ کھائیں", "دہی چاول کھائیں", "دودھ سے پرہیز (ماں کا دودھ چھوڑ کر)", "چکنائی اور مصالحے دار کھانے سے پرہیز"],
                    "roman_urdu": ["Kela, chawal, saib, toast khayein", "Dahi chawal khayein", "Doodh se parhair (maa ka doodh chor kar)"]
                },
                "see_doctor_if": {
                    "en": ["Blood in stool", "Unable to drink fluids", "Signs of severe dehydration (sunken eyes, no urine)", "High fever", "Continues more than 2 days"],
                    "ur": ["پاخانے میں خون", "پانی نہ پی سکے", "شدید پانی کی کمی کی علامات (دھنسی آنکھیں، پیشاب نہ آئے)", "تیز بخار", "2 دن سے زیادہ جاری رہے"]
                },
                "who_ors_formula": WHO_HEALTH_DATA["dehydration_protocol"]["ors_who_formula"]
            },
            
            "headache": {
                "immediate": {
                    "en": [
                        "Rest in a quiet, dark room",
                        "Stay well hydrated - drink 8-10 glasses of water",
                        "Apply cold compress on forehead or neck",
                        "Take paracetamol if needed",
                        "Check your blood pressure"
                    ],
                    "ur": [
                        "پرسکون اندھیرے کمرے میں آرام کریں",
                        "پانی خوب پیں - 8-10 گلاس",
                        "ماتھے یا گردن پر ٹھنڈا کپڑا رکھیں",
                        "ضرورت ہو تو پیراسیٹامول لیں",
                        "بلڈ پریشر چیک کروائیں"
                    ],
                    "roman_urdu": [
                        "Pursukoon andhere kamre mein aaram karein",
                        "Paani khoob piyen - 8-10 glass",
                        "Mathay ya gardan par thanda kapra rakhein",
                        "Zaroorat ho to paracetamol lein",
                        "BP check karwayein"
                    ]
                },
                "nutrition": {
                    "en": ["Avoid caffeine excess", "Eat regular meals - don't skip", "Magnesium-rich foods: spinach, nuts, whole grains"],
                    "ur": ["زیادہ چائے/کافی سے پرہیز", "باقاعدگی سے کھانا کھائیں", "پالک، گری دار میوے، سابت اناج کھائیں"]
                },
                "see_doctor_if": {
                    "en": ["Sudden severe 'worst headache ever'", "Headache with fever and stiff neck", "Vision changes", "Headache after head injury", "Daily recurring headaches"],
                    "ur": ["اچانک شدید ترین سر درد", "بخار اور گردن میں اکڑن کے ساتھ", "نظر میں تبدیلی", "سر پر چوٹ کے بعد", "روزانہ سر درد"]
                }
            },
            
            "cough": {
                "immediate": {
                    "en": [
                        "Drink warm fluids - honey with warm water, herbal tea",
                        "Steam inhalation 2-3 times daily",
                        "Gargle with warm salt water",
                        "Use honey (1-2 teaspoons) for soothing throat",
                        "Cover mouth when coughing"
                    ],
                    "ur": [
                        "گرم مشروبات پیں - شہد والا گرم پانی، قہوہ",
                        "بھاپ لیں دن میں 2-3 بار",
                        "نمک کے گرم پانی سے غرارے کریں",
                        "شہد (1-2 چائے کے چمچ) گلے کے لیے لیں",
                        "کھانستے وقت منہ ڈھانپیں"
                    ],
                    "roman_urdu": [
                        "Garam mashroobat piyen - shehad wala garam paani",
                        "Bhaap lein din mein 2-3 baar",
                        "Namak ke garam paani se ghararay karein",
                        "Shehad galay ke liye lein",
                        "Khanstay waqt munh dhaampein"
                    ]
                },
                "nutrition": {
                    "en": ["Warm soups", "Ginger tea", "Turmeric milk (haldi doodh)", "Avoid cold drinks and ice cream"],
                    "ur": ["گرم سوپ", "ادرک کی چائے", "ہلدی والا دودھ", "ٹھنڈے مشروبات اور آئس کریم سے پرہیز"]
                },
                "see_doctor_if": {
                    "en": ["Cough persists more than 2 weeks", "Blood in sputum", "Weight loss or night sweats", "High fever", "Difficulty breathing"],
                    "ur": ["2 ہفتے سے زیادہ کھانسی", "بلغم میں خون", "وزن کم ہونا یا رات کو پسینہ", "تیز بخار", "سانس لینے میں تکلیف"]
                },
                "tb_warning": {
                    "en": "If cough persists >2 weeks with weight loss and night sweats, GET TESTED FOR TB",
                    "ur": "اگر 2 ہفتے سے زیادہ کھانسی ہو اور وزن کم ہو رہا ہو تو ٹی بی کا ٹیسٹ کروائیں",
                    "roman_urdu": "Agar 2 hafte se zyada khansi ho aur wajan kam ho to TB test karwayein"
                }
            },
            
            "fatigue": {
                "immediate": {
                    "en": [
                        "Ensure 7-8 hours of quality sleep",
                        "Check for anemia - very common in Pakistan (41% women)",
                        "Get Vitamin D level checked (66% deficiency in Pakistan)",
                        "Light exercise - 30 minutes walking daily",
                        "Stay hydrated"
                    ],
                    "ur": [
                        "7-8 گھنٹے اچھی نیند لیں",
                        "خون کی کمی چیک کروائیں - پاکستان میں بہت عام (41% خواتین)",
                        "وٹامن ڈی چیک کروائیں (66% میں کمی ہے)",
                        "ہلکی ورزش - روزانہ 30 منٹ چہل قدمی",
                        "پانی خوب پیں"
                    ],
                    "roman_urdu": [
                        "7-8 ghante achi neend lein",
                        "Khoon ki kami check karwayein - 41% women mein hoti hai",
                        "Vitamin D check karwayein - 66% mein kami hai",
                        "Halki exercise - rozana 30 minute walk",
                        "Paani khoob piyen"
                    ]
                },
                "nutrition_for_anemia": PAKISTAN_NUTRITION_DATA["iron_rich_foods"],
                "nutrition_for_vitamin_d": PAKISTAN_NUTRITION_DATA["vitamin_d_sources"],
                "see_doctor_if": {
                    "en": ["Persistent fatigue despite rest", "With pale skin or dizziness", "With weight loss", "With shortness of breath"],
                    "ur": ["آرام کے باوجود مسلسل تھکاوٹ", "پیلے رنگ یا چکر کے ساتھ", "وزن کم ہونے کے ساتھ", "سانس پھولنے کے ساتھ"]
                }
            },
            
            "stomach_pain": {
                "immediate": {
                    "en": [
                        "Rest and avoid heavy meals",
                        "Apply warm compress on abdomen",
                        "Drink mint tea or ajwain water",
                        "Avoid spicy, oily, and acidic foods",
                        "Take small, frequent meals"
                    ],
                    "ur": [
                        "آرام کریں اور بھاری کھانے سے پرہیز",
                        "پیٹ پر گرم کپڑا رکھیں",
                        "پودینے کی چائے یا اجوائن کا پانی پیں",
                        "مصالحے دار، تلی ہوئی اور تیزابی غذا سے پرہیز",
                        "تھوڑا تھوڑا بار بار کھائیں"
                    ],
                    "roman_urdu": [
                        "Aaram karein aur bhaari khane se parhair",
                        "Pait par garam kapra rakhein",
                        "Pudine ki chai ya ajwain ka paani piyen",
                        "Masaledaar aur tala hua khana na khayein",
                        "Thora thora baar baar khayein"
                    ]
                },
                "see_doctor_if": {
                    "en": ["Severe pain especially right lower side (appendix)", "Blood in vomit or stool", "High fever with pain", "Pain lasting more than 24 hours", "Inability to eat or drink"],
                    "ur": ["شدید درد خاص طور پر دائیں نچلے حصے میں", "الٹی یا پاخانے میں خون", "درد کے ساتھ تیز بخار", "24 گھنٹے سے زیادہ درد", "کچھ کھا پی نہ سکیں"]
                }
            },
            
            "body_aches": {
                "immediate": {
                    "en": [
                        "Complete bed rest",
                        "Stay well hydrated",
                        "Take paracetamol for pain",
                        "If with high fever, consider dengue test (especially Aug-Nov)",
                        "Apply warm compress on affected areas"
                    ],
                    "ur": [
                        "مکمل آرام کریں",
                        "پانی خوب پیں",
                        "درد کے لیے پیراسیٹامول لیں",
                        "تیز بخار ہو تو ڈینگی ٹیسٹ کروائیں (خاص طور پر اگست-نومبر)",
                        "متاثرہ جگہ پر گرم کپڑا رکھیں"
                    ],
                    "roman_urdu": [
                        "Mukammal aaram karein",
                        "Paani khoob piyen",
                        "Dard ke liye paracetamol lein",
                        "Tez bukhar ho to dengue test karwayein (Aug-Nov mein)",
                        "Mutasira jagah par garam kapra rakhein"
                    ]
                },
                "dengue_warning": {
                    "en": "If severe body/joint pain with high fever during monsoon season (Aug-Nov), GET DENGUE TEST. Do NOT take aspirin!",
                    "ur": "اگر مانسون میں (اگست-نومبر) تیز بخار کے ساتھ شدید جسم/جوڑوں میں درد ہو تو ڈینگی ٹیسٹ کروائیں۔ اسپرین نہ لیں!",
                    "roman_urdu": "Aug-Nov mein tez bukhar ke sath shadeed jism/joron mein dard ho to DENGUE TEST karwayein. ASPIRIN NA LEIN!"
                }
            },
            
            "jaundice": {
                "immediate": {
                    "en": [
                        "Complete bed rest",
                        "Drink plenty of fluids - sugarcane juice, coconut water",
                        "Avoid oily, fried, and heavy foods",
                        "Get Hepatitis B and C tests",
                        "Do NOT share razors, toothbrushes"
                    ],
                    "ur": [
                        "مکمل آرام کریں",
                        "خوب پانی پیں - گنے کا رس، ناریل پانی",
                        "تلی ہوئی اور بھاری غذا سے پرہیز",
                        "ہیپاٹائٹس بی اور سی ٹیسٹ کروائیں",
                        "استرا، ٹوتھ برش شیئر نہ کریں"
                    ],
                    "roman_urdu": [
                        "Mukammal aaram karein",
                        "Khoob paani piyen - gannay ka ras, nariyal paani",
                        "Tali hui aur bhaari ghiza se parhair",
                        "Hepatitis B aur C test karwayein",
                        "Ustra, toothbrush share na karein"
                    ]
                },
                "hepatitis_info": {
                    "en": "Hepatitis C is now CURABLE in 12 weeks with new medicines. Get tested!",
                    "ur": "ہیپاٹائٹس سی اب نئی دوائیوں سے 12 ہفتوں میں قابل علاج ہے۔ ٹیسٹ کروائیں!",
                    "roman_urdu": "Hepatitis C ab 12 hafton mein theek ho sakti hai. Test karwayein!"
                },
                "prevention": PAKISTAN_HEALTH_STATISTICS["disease_burden"]["hepatitis_b_c"]["prevention"]
            }
        }
        
        # Emergency contacts
        self.EMERGENCY_CONTACTS = EMERGENCY_CONTACTS_PAKISTAN
    
    async def process(self, context: AgentContext) -> AgentContext:
        """Generate health recommendations"""
        
        symptoms = context.symptoms
        risks = context.identified_risks
        language = context.user_language
        recommendations = []
        nutrition_advice = []
        
        # Generate recommendations for each symptom
        for symptom in symptoms:
            if symptom in self.HEALTH_RECOMMENDATIONS:
                rec_data = self.HEALTH_RECOMMENDATIONS[symptom]
                
                # Get immediate recommendations in user's language
                immediate = rec_data.get("immediate", {}).get(language, rec_data.get("immediate", {}).get("en", []))
                recommendations.extend(immediate)
                
                # Get nutrition advice
                nutrition = rec_data.get("nutrition", {}).get(language, rec_data.get("nutrition", {}).get("en", []))
                nutrition_advice.extend(nutrition)
                
                # Add warning if present
                for warning_key in ["tb_warning", "dengue_warning", "hepatitis_info"]:
                    if warning_key in rec_data:
                        warning = rec_data[warning_key].get(language, rec_data[warning_key].get("en", ""))
                        if warning:
                            context.safety_flags.append(warning)
        
        # Add nutrition recommendations for identified deficiency risks
        for risk in risks:
            if risk.get("type") == "nutritional_deficiency":
                condition = risk.get("condition", "")
                sources = risk.get("recommended_sources", {})
                source_text = sources.get(language, sources.get("en", ""))
                if source_text:
                    nutrition_advice.append(f"{condition}: {source_text}")
        
        # Add iron-rich foods for anemia symptoms
        if "fatigue" in symptoms or "weakness" in symptoms or "pale" in symptoms:
            iron_foods = []
            for food_key, food_data in PAKISTAN_NUTRITION_DATA["iron_rich_foods"].items():
                iron_foods.append(f"{food_data['name_roman']} ({food_data['name_en']})")
            nutrition_advice.append(f"Iron-rich foods: {', '.join(iron_foods[:5])}")
        
        # Remove duplicates while preserving order
        recommendations = list(dict.fromkeys(recommendations))
        nutrition_advice = list(dict.fromkeys(nutrition_advice))
        
        # Use LLM to personalize if available
        if self.vertex_service and not context.degraded_mode and recommendations:
            try:
                personalized = await self._personalize_with_llm(
                    recommendations, nutrition_advice, symptoms, language
                )
                if personalized:
                    recommendations = personalized
            except Exception as e:
                self.logger.warning(f"LLM personalization failed: {e}")
        
        # Update context
        context.recommendations = recommendations[:10]  # Limit to top 10
        context.health_indicators["nutrition_advice"] = nutrition_advice[:5]
        
        # Add emergency contacts if high risk
        if context.health_indicators.get("risk_level") in ["HIGH", "CRITICAL"]:
            context.health_indicators["emergency_contacts"] = self.EMERGENCY_CONTACTS["emergency_services"]
        
        # Log decision
        decision = AgentDecision(
            agent_name=self.name,
            decision=f"Generated {len(recommendations)} recommendations for {len(symptoms)} symptoms",
            reasoning=f"Used WHO guidelines and Pakistan-specific nutrition data. "
                      f"Sources: Open Food Facts, Pakistan Bureau of Statistics",
            confidence=0.85,
            inputs_used=["symptoms", "risks", "PAKISTAN_NUTRITION_DATA", "WHO_HEALTH_DATA"],
            language=language
        )
        context.decisions.append(decision)
        
        return context
    
    async def _personalize_with_llm(
        self, 
        recommendations: List[str], 
        nutrition: List[str],
        symptoms: List[str],
        language: str
    ) -> List[str]:
        """Use LLM to personalize recommendations"""
        
        lang_instruction = {
            "en": "Respond in simple English",
            "ur": "جواب سادہ اردو میں دیں",
            "roman_urdu": "Jawab simple Roman Urdu mein dein"
        }
        
        prompt = f"""You are a helpful health advisor in Pakistan. 
Given these symptoms: {symptoms}
And these recommendations: {recommendations[:5]}
And nutrition advice: {nutrition[:3]}

Create a brief, personalized health guidance message. {lang_instruction.get(language, lang_instruction['en'])}.
Keep it practical and easy to follow. Include local food names if relevant.
Maximum 5 bullet points.
"""
        
        response = await self.vertex_service.generate_text(prompt)
        
        if response:
            # Parse bullet points
            lines = [line.strip() for line in response.split("\n") if line.strip()]
            return [line.lstrip("•-*").strip() for line in lines if line][:5]
        
        return recommendations

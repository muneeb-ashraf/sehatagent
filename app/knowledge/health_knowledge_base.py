"""
SehatAgent Health Knowledge Base
Comprehensive health data from official sources:
- WHO Global Health Data (https://www.who.int/data)
- Pakistan Bureau of Statistics (https://pslm-sdgs.data.gov.pk/health/index)
- NIH Clinical Data (https://www.ncbi.nlm.nih.gov/gap)
- Open Food Facts (https://world.openfoodfacts.org/data)
"""

# ============================================================
# WHO GLOBAL HEALTH DATA
# Source: https://www.who.int/data
# ============================================================

WHO_HEALTH_DATA = {
    "source": "World Health Organization (WHO)",
    "url": "https://www.who.int/data",
    
    "fever_management": {
        "normal_temp_celsius": 36.1 - 37.2,
        "fever_threshold_celsius": 38.0,
        "high_fever_celsius": 39.5,
        "dangerous_fever_celsius": 41.0,
        "guidelines": {
            "en": {
                "mild": ["Rest in cool environment", "Drink plenty of fluids", "Wear light clothing", "Monitor temperature every 4 hours"],
                "moderate": ["Take paracetamol (15mg/kg for children)", "Tepid sponging", "Increase fluid intake to 2-3 liters/day", "Seek medical advice if persists >48 hours"],
                "high": ["Seek immediate medical attention", "Cool compresses on forehead, armpits, groin", "Continue fluids", "Do not use ice water"],
                "dangerous": ["EMERGENCY - Call ambulance immediately", "Cool the body while waiting", "Do not give oral medication if unconscious"]
            },
            "ur": {
                "mild": ["ٹھنڈی جگہ پر آرام کریں", "خوب پانی پیں", "ہلکے کپڑے پہنیں", "ہر 4 گھنٹے بعد درجہ حرارت چیک کریں"],
                "moderate": ["پیراسیٹامول لیں", "نیم گرم پانی سے جسم صاف کریں", "2-3 لیٹر پانی روزانہ", "48 گھنٹے سے زیادہ ہو تو ڈاکٹر سے ملیں"],
                "high": ["فوری طبی مدد لیں", "ماتھے اور بغلوں پر ٹھنڈا کپڑا رکھیں", "پانی جاری رکھیں"],
                "dangerous": ["ایمرجنسی - فوری 1122 کال کریں", "ایمبولینس کا انتظار کرتے ہوئے جسم ٹھنڈا کریں"]
            },
            "roman_urdu": {
                "mild": ["Thandi jagah par aaram karein", "Khoob paani piyen", "Halke kapre pehnein", "Har 4 ghante temperature check karein"],
                "moderate": ["Paracetamol lein", "Neem garam paani se jism saaf karein", "2-3 liter paani rozana", "48 ghante se zyada ho to doctor se milein"],
                "high": ["Fori medical madad lein", "Mathay aur baghlon par thanda kapra rakhein"],
                "dangerous": ["EMERGENCY - Fori 1122 call karein"]
            }
        }
    },
    
    "dehydration_protocol": {
        "ors_who_formula": {
            "description": "WHO-recommended Oral Rehydration Solution",
            "ingredients": {
                "clean_water_ml": 1000,
                "salt_grams": 2.6,
                "sugar_grams": 13.5,
                "potassium_chloride_grams": 1.5,
                "trisodium_citrate_grams": 2.9
            },
            "home_recipe": {
                "water_liters": 1,
                "salt_teaspoon": 0.5,
                "sugar_tablespoons": 6,
                "note": "Use boiled and cooled water"
            }
        },
        "severity_assessment": {
            "none": {
                "signs": ["Normal eyes", "Drinks normally", "Skin pinch goes back quickly"],
                "treatment": "Give extra fluids, continue feeding"
            },
            "some": {
                "signs": ["Sunken eyes", "Drinks eagerly", "Skin pinch goes back slowly (<2 sec)"],
                "treatment": "Give ORS - 75ml/kg over 4 hours, reassess frequently"
            },
            "severe": {
                "signs": ["Very sunken eyes", "Unable to drink", "Skin pinch goes back very slowly (>2 sec)", "Lethargy"],
                "treatment": "EMERGENCY - IV fluids needed, refer immediately"
            }
        }
    },
    
    "imci_danger_signs": {
        "description": "WHO Integrated Management of Childhood Illness - Danger Signs",
        "children_under_5": [
            "Unable to drink or breastfeed",
            "Vomits everything",
            "Convulsions/fits",
            "Lethargic or unconscious",
            "Chest indrawing",
            "Stridor when calm",
            "Severe malnutrition"
        ],
        "action": "Refer URGENTLY to hospital"
    },
    
    "respiratory_rate_thresholds": {
        "description": "WHO criteria for fast breathing (pneumonia indicator)",
        "age_0_2_months": {"fast_breathing": ">= 60 breaths/min"},
        "age_2_12_months": {"fast_breathing": ">= 50 breaths/min"},
        "age_1_5_years": {"fast_breathing": ">= 40 breaths/min"},
        "age_over_5": {"fast_breathing": ">= 30 breaths/min"}
    }
}


# ============================================================
# PAKISTAN BUREAU OF STATISTICS - HEALTH DATA
# Source: https://pslm-sdgs.data.gov.pk/health/index
# ============================================================

PAKISTAN_HEALTH_STATISTICS = {
    "source": "Pakistan Bureau of Statistics - PSLM & Health Surveys",
    "url": "https://pslm-sdgs.data.gov.pk/health/index",
    
    "disease_burden": {
        "diabetes_mellitus": {
            "prevalence_percent": 26.3,
            "affected_adults_millions": 33,
            "undiagnosed_percent": 50,
            "urban_rural_ratio": 1.4,
            "trend": "Rapidly increasing",
            "risk_factors": {
                "en": ["Obesity", "Sedentary lifestyle", "High carb diet", "Family history", "Age >40"],
                "ur": ["موٹاپا", "بیٹھک زندگی", "زیادہ کاربوہائیڈریٹ والی غذا", "خاندانی تاریخ", "عمر 40 سے زیادہ"]
            },
            "symptoms": {
                "en": ["Excessive thirst (polydipsia)", "Frequent urination (polyuria)", "Unexplained weight loss", "Fatigue", "Blurred vision", "Slow wound healing", "Tingling in hands/feet"],
                "ur": ["بہت زیادہ پیاس", "بار بار پیشاب", "بغیر وجہ وزن کم ہونا", "تھکاوٹ", "دھندلی نظر", "زخم دیر سے بھرنا", "ہاتھوں پیروں میں سنسناہٹ"],
                "roman_urdu": ["Bohat zyada pyaas", "Baar baar peshab", "Wajan kam hona", "Thakawat", "Dhundli nazar", "Zakham der se bharna"]
            },
            "screening_recommendation": "Annual fasting blood glucose after age 40, or earlier if risk factors present"
        },
        
        "hypertension": {
            "prevalence_percent": 33.0,
            "affected_adults_millions": 40,
            "awareness_percent": 33,
            "controlled_percent": 6,
            "trend": "Increasing",
            "classification": {
                "normal": "<120/80 mmHg",
                "elevated": "120-129/<80 mmHg",
                "stage_1": "130-139/80-89 mmHg",
                "stage_2": ">=140/90 mmHg",
                "crisis": ">180/120 mmHg"
            },
            "risk_factors": {
                "en": ["High salt intake (>5g/day)", "Obesity", "Lack of exercise", "Smoking", "Stress", "Family history", "Age"],
                "ur": ["زیادہ نمک", "موٹاپا", "ورزش کی کمی", "سگریٹ نوشی", "ذہنی تناؤ", "خاندانی تاریخ"]
            },
            "symptoms": {
                "en": ["Often asymptomatic (silent killer)", "Headache (especially morning)", "Dizziness", "Blurred vision", "Chest pain", "Shortness of breath", "Nosebleeds"],
                "ur": ["اکثر علامات نہیں ہوتیں (خاموش قاتل)", "سر درد (خاص طور پر صبح)", "چکر", "دھندلی نظر", "سینے میں درد", "سانس کی تکلیف"],
                "roman_urdu": ["Aksar alamaat nahi hotein", "Subah sir dard", "Chakkar", "Seene mein dard", "Saans ki takleef"]
            },
            "prevention": {
                "en": ["Reduce salt to <5g/day", "Exercise 30 min daily", "Maintain healthy weight", "Quit smoking", "Limit alcohol", "Manage stress"],
                "ur": ["نمک کم کریں", "روزانہ 30 منٹ ورزش", "وزن کنٹرول کریں", "سگریٹ چھوڑیں", "تناؤ کم کریں"]
            }
        },
        
        "anemia": {
            "women_prevalence_percent": 41.7,
            "children_prevalence_percent": 62.0,
            "pregnant_women_percent": 50.4,
            "trend": "High but stable",
            "types_common": ["Iron deficiency (most common)", "Vitamin B12 deficiency", "Folate deficiency", "Thalassemia"],
            "hemoglobin_cutoffs": {
                "men": "<13 g/dL",
                "women_non_pregnant": "<12 g/dL",
                "women_pregnant": "<11 g/dL",
                "children_6_59_months": "<11 g/dL",
                "children_5_11_years": "<11.5 g/dL"
            },
            "symptoms": {
                "en": ["Fatigue/weakness", "Pale skin, nails, inner eyelids", "Shortness of breath", "Dizziness", "Cold hands and feet", "Brittle nails", "Craving for ice/dirt (pica)", "Rapid heartbeat"],
                "ur": ["تھکاوٹ/کمزوری", "جلد، ناخن، پلکوں کا پیلا ہونا", "سانس پھولنا", "چکر آنا", "ہاتھ پاؤں ٹھنڈے", "ناخن ٹوٹنا", "برف/مٹی کھانے کی خواہش"],
                "roman_urdu": ["Thakawat/kamzori", "Rang peela", "Saans phoolna", "Chakkar aana", "Haath paon thandey"]
            },
            "causes_pakistan": ["Poor dietary iron intake", "Parasitic infections (hookworm)", "Frequent pregnancies", "Heavy menstruation", "Chronic diseases"],
            "prevention": {
                "en": ["Eat iron-rich foods (liver, spinach, chickpeas)", "Take Vitamin C with iron foods", "Deworming every 6 months", "Iron supplements during pregnancy"],
                "ur": ["آئرن والی غذائیں کھائیں (کلیجی، پالک، چنے)", "آئرن کے ساتھ وٹامن سی لیں", "ہر 6 ماہ بعد پیٹ کے کیڑوں کی دوائی"]
            }
        },
        
        "vitamin_d_deficiency": {
            "prevalence_percent": 66.0,
            "women_prevalence_percent": 73.0,
            "trend": "Very high, increasing",
            "reasons_pakistan": ["Limited sun exposure", "Covering clothing/purdah", "Indoor lifestyle", "Dark skin", "Limited dietary sources"],
            "deficiency_levels": {
                "severe_deficiency": "<10 ng/mL",
                "deficiency": "<20 ng/mL",
                "insufficiency": "20-29 ng/mL",
                "sufficient": "30-100 ng/mL"
            },
            "symptoms": {
                "en": ["Bone pain", "Muscle weakness", "Fatigue", "Depression", "Frequent infections", "Slow wound healing", "Hair loss"],
                "ur": ["ہڈیوں میں درد", "پٹھوں کی کمزوری", "تھکاوٹ", "اداسی", "بار بار انفیکشن", "زخم دیر سے بھرنا"],
                "roman_urdu": ["Haddiyon mein dard", "Pathon ki kamzori", "Thakawat", "Udasi", "Baar baar infection"]
            },
            "recommendations": {
                "en": ["Morning sunlight 15-20 min (before 10 AM)", "Eat fatty fish, eggs, fortified milk", "Supplements: 1000-2000 IU daily for adults", "Mushrooms exposed to sunlight"],
                "ur": ["صبح کی دھوپ 15-20 منٹ (10 بجے سے پہلے)", "مچھلی، انڈے، دودھ کھائیں", "سپلیمنٹ: روزانہ 1000-2000 IU"]
            }
        },
        
        "typhoid_fever": {
            "annual_incidence": "493 per 100,000",
            "total_cases_annual": "Over 100,000",
            "xdr_typhoid_percent": 70,  # Extensively Drug Resistant
            "mortality_untreated_percent": 12,
            "mortality_treated_percent": 1,
            "endemic_areas": ["Sindh (especially Karachi, Hyderabad)", "Southern Punjab"],
            "transmission": "Fecal-oral route via contaminated water/food",
            "incubation_days": "7-14",
            "symptoms_by_week": {
                "week_1": {
                    "en": ["Gradual onset fever (stepladder pattern)", "Headache", "Malaise", "Abdominal discomfort"],
                    "ur": ["آہستہ آہستہ بڑھتا بخار", "سر درد", "بے چینی", "پیٹ میں تکلیف"]
                },
                "week_2": {
                    "en": ["High sustained fever (39-40°C)", "Rose spots on chest/abdomen", "Abdominal distension", "Diarrhea or constipation", "Hepatosplenomegaly"],
                    "ur": ["تیز مسلسل بخار", "سینے پر گلابی دھبے", "پیٹ پھولنا", "دست یا قبض", "جگر/تلی بڑھنا"]
                },
                "week_3": {
                    "en": ["Complications may occur", "Intestinal bleeding", "Perforation", "Confusion"],
                    "ur": ["پیچیدگیاں ہو سکتی ہیں", "آنتوں سے خون", "آنت پھٹنا", "ذہنی الجھن"]
                }
            },
            "diagnosis": ["Blood culture (gold standard)", "Widal test (less accurate)", "Typhidot"],
            "prevention": {
                "en": ["Drink boiled/filtered water only", "Wash hands with soap before eating", "Eat freshly cooked hot food", "Avoid raw vegetables/salads outside", "Typhoid vaccination (TCV)"],
                "ur": ["صرف ابلا/فلٹر پانی پیں", "کھانے سے پہلے صابن سے ہاتھ دھوئیں", "تازہ پکا ہوا کھانا کھائیں", "باہر کچی سبزیاں/سلاد نہ کھائیں", "ٹائیفائیڈ ویکسین لگوائیں"],
                "roman_urdu": ["Sirf ubla/filter paani piyen", "Khaane se pehle sabun se haath dhoyein", "Taaza paka hua khana khayein", "Bahar kachi sabzi na khayein"]
            }
        },
        
        "dengue_fever": {
            "annual_cases_average": "50,000+",
            "epidemic_years": ["2011 (Lahore)", "2019 (nationwide)", "2022 (major outbreak)"],
            "peak_season": "Post-monsoon (August-November)",
            "vector": "Aedes aegypti and Aedes albopictus mosquito",
            "high_risk_cities": ["Lahore", "Rawalpindi", "Islamabad", "Karachi", "Faisalabad", "Multan"],
            "transmission_time": "Early morning and late afternoon (daytime biters)",
            "symptoms": {
                "dengue_fever": {
                    "en": ["Sudden high fever (40°C/104°F)", "Severe headache", "Pain behind eyes", "Muscle and joint pain (breakbone fever)", "Nausea/vomiting", "Skin rash (appears day 3-4)", "Mild bleeding (nose, gums)"],
                    "ur": ["اچانک تیز بخار", "شدید سر درد", "آنکھوں کے پیچھے درد", "جوڑوں اور پٹھوں میں شدید درد", "متلی/الٹی", "جلد پر دانے", "ہلکا خون بہنا"],
                    "roman_urdu": ["Achanak tez bukhar", "Shadeed sir dard", "Aankhon ke peechey dard", "Joron mein dard", "Matli/ulti", "Jild par danay"]
                },
                "warning_signs_severe": {
                    "en": ["Severe abdominal pain", "Persistent vomiting", "Bleeding gums/nose", "Blood in vomit/stool", "Rapid breathing", "Fatigue/restlessness", "Liver enlargement"],
                    "ur": ["شدید پیٹ درد", "مسلسل الٹی", "مسوڑھوں/ناک سے خون", "الٹی/پاخانے میں خون", "تیز سانس", "بے چینی"],
                    "roman_urdu": ["Shadeed pait dard", "Musalsal ulti", "Masorhon/naak se khoon", "Ulti mein khoon"]
                }
            },
            "management": {
                "en": ["NO ASPIRIN or NSAIDs (increases bleeding)", "Paracetamol only for fever", "Drink plenty of fluids (ORS, juices, coconut water)", "Complete bed rest", "Monitor platelet count daily", "Hospital admission if warning signs"],
                "ur": ["اسپرین یا درد کی گولیاں نہ لیں", "صرف پیراسیٹامول لیں", "خوب پانی پیں (نمکول، جوس)", "مکمل آرام", "روزانہ پلیٹلیٹس چیک کروائیں", "خطرے کی علامات پر ہسپتال جائیں"],
                "roman_urdu": ["Aspirin ya dard ki goliyan na lein", "Sirf paracetamol", "Khoob paani piyen", "Mukammal aaram"]
            },
            "prevention": {
                "en": ["Remove standing water (coolers, pots, tires)", "Use mosquito repellents", "Wear long sleeves and pants", "Use bed nets", "Window/door screens", "Fogging in endemic areas"],
                "ur": ["کھڑا پانی ختم کریں (کولر، گملے، ٹائر)", "مچھر مار لوشن لگائیں", "لمبی آستین والے کپڑے پہنیں", "مچھر دانی استعمال کریں"],
                "roman_surdu": ["Khara paani khatam karein", "Machhar maar lotion lagayein", "Lambi aasteen walay kapray pehnein", "Machhar daani istemal karein"]
            }
        },
        
        "tuberculosis": {
            "incidence_per_100k": 259,
            "total_cases_annual": 510000,
            "mdr_tb_cases": 27000,
            "ranking": "5th highest TB burden globally",
            "mortality_per_100k": 23,
            "notification_rate_percent": 67,
            "treatment_success_rate_percent": 93,
            "risk_groups": ["HIV positive", "Diabetes patients", "Malnutrition", "Smokers", "Close contacts of TB patients", "Healthcare workers", "Prisoners"],
            "symptoms": {
                "en": ["Persistent cough >2 weeks", "Coughing blood (hemoptysis)", "Night sweats", "Unexplained weight loss", "Loss of appetite", "Fever (especially evening)", "Fatigue", "Chest pain"],
                "ur": ["2 ہفتے سے زیادہ کھانسی", "کھانسی میں خون", "رات کو پسینہ", "بغیر وجہ وزن کم ہونا", "بھوک نہ لگنا", "شام کو بخار", "تھکاوٹ", "سینے میں درد"],
                "roman_urdu": ["2 hafte se zyada khansi", "Khansi mein khoon", "Raat ko paseena", "Wajan kam hona", "Bhook na lagna", "Shaam ko bukhar"]
            },
            "diagnosis": ["Sputum test (GeneXpert/AFB smear)", "Chest X-ray", "Mantoux test/TST", "TB blood test (IGRA)"],
            "treatment": {
                "duration_months": 6,
                "dots_strategy": "Directly Observed Treatment, Short-course",
                "first_line_drugs": ["Isoniazid (H)", "Rifampicin (R)", "Pyrazinamide (Z)", "Ethambutol (E)"],
                "key_message": {
                    "en": "COMPLETE THE FULL 6-MONTH COURSE even if you feel better. Stopping early creates drug-resistant TB!",
                    "ur": "پورے 6 ماہ کا کورس مکمل کریں چاہے طبیعت ٹھیک ہو جائے۔ بیچ میں چھوڑنے سے دوائی اثر نہیں کرتی!",
                    "roman_urdu": "Pooray 6 maah ka course mukammal karein chahe tabiyat theek ho jaye!"
                }
            },
            "prevention": {
                "en": ["BCG vaccination at birth", "Good ventilation", "Cover mouth when coughing", "Early detection and treatment", "Contact tracing"],
                "ur": ["پیدائش پر بی سی جی ٹیکہ", "کمرے میں ہوا کا گزر", "کھانستے وقت منہ ڈھانپیں", "جلد تشخیص اور علاج"]
            }
        },
        
        "hepatitis_b_c": {
            "hepatitis_b_prevalence_percent": 2.5,
            "hepatitis_c_prevalence_percent": 5.0,
            "hepatitis_c_affected_millions": 12,
            "main_transmission_routes": ["Contaminated syringes/needles (biggest cause)", "Unsafe blood transfusion", "Unsterilized medical/dental equipment", "Barber razors", "Mother to child (Hep B)"],
            "high_risk_groups": ["Injection drug users", "Patients on dialysis", "Healthcare workers", "Recipients of blood products", "People with multiple sexual partners"],
            "symptoms": {
                "acute": {
                    "en": ["Jaundice (yellow eyes/skin)", "Dark urine", "Pale stools", "Fatigue", "Nausea", "Abdominal pain (right upper)", "Loss of appetite"],
                    "ur": ["یرقان (آنکھوں/جلد کا پیلا ہونا)", "گہرے رنگ کا پیشاب", "سفید پاخانہ", "تھکاوٹ", "متلی", "پیٹ کے اوپری دائیں حصے میں درد"],
                    "roman_urdu": ["Yarqan (aankhon ka peela hona)", "Gehre rang ka peshab", "Safed pakhana", "Thakawat", "Matli"]
                },
                "chronic": {
                    "en": ["Often asymptomatic for years", "Fatigue", "Can progress to cirrhosis and liver cancer"],
                    "ur": ["اکثر سالوں تک علامات نہیں", "تھکاوٹ", "جگر کی سختی اور کینسر کا خطرہ"]
                }
            },
            "prevention": {
                "en": ["Use disposable syringes only", "Screen all blood before transfusion", "Hepatitis B vaccination (3 doses)", "Don't share razors/toothbrushes", "Use sterilized equipment", "Avoid roadside barbers/dentists"],
                "ur": ["صرف ڈسپوزایبل سرنج استعمال کریں", "خون لینے سے پہلے ٹیسٹ", "ہیپاٹائٹس بی کے 3 ٹیکے لگوائیں", "استرا/ٹوتھ برش شیئر نہ کریں", "نائی کی دکان سے بچیں"],
                "roman_urdu": ["Sirf disposable syringe istemal karein", "Khoon lene se pehle test", "Hepatitis B ke 3 teekay lagwayein", "Naai ki dukaan se bachein"]
            },
            "treatment_available": "Hepatitis C is now CURABLE with DAAs (Direct Acting Antivirals) in 12 weeks"
        },
        
        "malaria": {
            "annual_cases": 300000,
            "endemic_areas": ["Sindh (especially rural)", "Balochistan", "KPK (tribal districts)", "Southern Punjab"],
            "peak_season": "Post-monsoon (September-November)",
            "types_in_pakistan": ["Plasmodium vivax (70%)", "Plasmodium falciparum (30%)"],
            "transmission": "Female Anopheles mosquito bite (night biter)",
            "symptoms": {
                "en": ["Cyclical fever (every 48-72 hours)", "Severe chills and shaking", "Sweating", "Headache", "Muscle pain", "Nausea/vomiting", "Fatigue"],
                "ur": ["وقفے وقفے سے بخار", "شدید کپکپی اور لرزہ", "پسینہ", "سر درد", "جسم میں درد", "متلی/الٹی"],
                "roman_urdu": ["Waqfay waqfay se bukhar", "Shadeed kapkapi", "Paseena", "Sir dard", "Jism mein dard"]
            },
            "severe_malaria_signs": ["Impaired consciousness", "Respiratory distress", "Multiple convulsions", "Jaundice", "Dark urine", "Severe anemia"],
            "prevention": {
                "en": ["Sleep under insecticide-treated bed nets", "Use mosquito repellents", "Wear long sleeves at night", "Indoor residual spraying", "Antimalarial prophylaxis for travelers"],
                "ur": ["کیڑے مار دوائی لگی مچھر دانی میں سوئیں", "مچھر مار لوشن لگائیں", "رات کو لمبی آستین پہنیں", "گھر میں سپرے کروائیں"],
                "roman_urdu": ["Machhar daani mein soyein", "Machhar maar lotion lagayein", "Raat ko lambi aasteen pehnein"]
            }
        },
        
        "diarrheal_diseases": {
            "under_5_deaths_annual": 53000,
            "episodes_per_child_year": 2.5,
            "main_causes": ["Rotavirus", "E. coli", "Cholera", "Shigella", "Parasites (Giardia, Amoeba)"],
            "dehydration_deaths_percent": 70,
            "risk_factors": ["Contaminated water", "Poor sanitation", "Lack of handwashing", "Malnutrition", "Lack of breastfeeding"],
            "symptoms": {
                "en": ["Loose/watery stools 3+ times/day", "Abdominal cramps", "Nausea/vomiting", "Fever", "Blood/mucus in stool (dysentery)"],
                "ur": ["دن میں 3 یا زیادہ بار پتلا پاخانہ", "پیٹ میں مروڑ", "متلی/الٹی", "بخار", "پاخانے میں خون/آنو (پیچش)"],
                "roman_urdu": ["Din mein 3 ya zyada baar patla pakhana", "Pait mein maror", "Bukhar", "Pakhane mein khoon"]
            },
            "treatment": {
                "primary": {
                    "en": ["ORS after every loose stool", "Continue breastfeeding", "Zinc supplements (20mg for 10-14 days)", "Continue feeding"],
                    "ur": ["ہر پتلے پاخانے کے بعد نمکول دیں", "دودھ پلانا جاری رکھیں", "زنک کی گولی 10-14 دن", "کھانا جاری رکھیں"],
                    "roman_urdu": ["Har patle pakhane ke baad namkol dein", "Doodh pilana jari rakhein", "Zinc ki goli 10-14 din"]
                },
                "seek_help_if": {
                    "en": ["Blood in stool", "Unable to drink", "Very thirsty", "Sunken eyes", "Fever >38.5°C", "Not improved in 3 days"],
                    "ur": ["پاخانے میں خون", "پی نہ سکے", "بہت پیاس", "آنکھیں دھنسی ہوئی", "تیز بخار", "3 دن میں بہتری نہ ہو"]
                }
            },
            "prevention": {
                "en": ["Wash hands with soap (before eating, after toilet)", "Drink safe/boiled water", "Exclusive breastfeeding for 6 months", "Rotavirus vaccination", "Safe food handling"],
                "ur": ["صابن سے ہاتھ دھوئیں", "صاف/ابلا پانی پیں", "6 ماہ تک صرف ماں کا دودھ", "روٹا وائرس ویکسین", "کھانا صاف رکھیں"]
            }
        }
    },
    
    "maternal_child_health": {
        "maternal_mortality_ratio": 186,  # per 100,000 live births
        "infant_mortality_rate": 56,  # per 1,000 live births
        "neonatal_mortality_rate": 42,  # per 1,000 live births
        "under_5_mortality_rate": 67,  # per 1,000 live births
        "skilled_birth_attendance_percent": 69,
        "institutional_delivery_percent": 66,
        "antenatal_care_4plus_visits_percent": 51,
        "postnatal_care_percent": 60,
        "contraceptive_prevalence_percent": 34,
        "unmet_need_family_planning_percent": 17,
        
        "child_nutrition": {
            "exclusive_breastfeeding_percent": 48,
            "stunting_percent": 40.2,
            "wasting_percent": 17.7,
            "underweight_percent": 28.9,
            "overweight_percent": 2.5
        },
        
        "immunization_coverage": {
            "bcg_percent": 92,
            "dpt3_percent": 85,
            "polio3_percent": 86,
            "measles1_percent": 80,
            "fully_immunized_percent": 66
        },
        
        "danger_signs_pregnancy": {
            "en": ["Vaginal bleeding", "Severe headache with blurred vision", "High fever", "Severe abdominal pain", "Reduced fetal movement", "Water breaking early", "Convulsions", "Swelling of face/hands"],
            "ur": ["خون آنا", "شدید سر درد اور دھندلی نظر", "تیز بخار", "شدید پیٹ درد", "بچے کی حرکت کم ہونا", "پانی بہنا", "دورے پڑنا", "چہرے/ہاتھوں پر سوجن"],
            "roman_urdu": ["Khoon aana", "Shadeed sir dard aur dhundli nazar", "Tez bukhar", "Shadeed pait dard", "Bachay ki harkat kam hona"]
        },
        
        "danger_signs_newborn": {
            "en": ["Not feeding well", "Convulsions", "Fast breathing (>60/min)", "Severe chest indrawing", "No movement/lethargy", "Fever or feels cold", "Umbilical redness/pus"],
            "ur": ["دودھ نہ پینا", "دورے", "تیز سانس", "سینہ اندر دھنسنا", "حرکت نہ کرنا", "بخار یا جسم ٹھنڈا", "ناف میں سرخی/پیپ"],
            "roman_urdu": ["Doodh na peena", "Dauray", "Tez saans", "Seena andar dhansna", "Harkat na karna"]
        }
    },
    
    "health_infrastructure": {
        "doctors_per_10000": 11.1,
        "nurses_per_10000": 5.0,
        "dentists_per_10000": 0.9,
        "hospital_beds_per_10000": 6.0,
        "lady_health_workers": 110000,
        "basic_health_units": 5527,
        "rural_health_centers": 686,
        "tehsil_hospitals": 598,
        "district_hospitals": 127
    }
}


# ============================================================
# OPEN FOOD FACTS - NUTRITION DATA FOR PAKISTAN
# Source: https://world.openfoodfacts.org/data
# ============================================================

PAKISTAN_NUTRITION_DATA = {
    "source": "Open Food Facts + Pakistan Food Composition Tables",
    "url": "https://world.openfoodfacts.org/data",
    
    "iron_rich_foods": {
        "kaleji_mutton_liver": {
            "name_en": "Mutton Liver",
            "name_ur": "کلیجی",
            "name_roman": "Kaleji",
            "iron_mg_per_100g": 6.5,
            "serving_size": "100g (1 serving)",
            "other_nutrients": ["Vitamin A", "Vitamin B12", "Folate", "Protein"],
            "preparation_tip": {
                "en": "Cook thoroughly. Eat 1-2 times per week.",
                "ur": "اچھی طرح پکائیں۔ ہفتے میں 1-2 بار کھائیں۔"
            },
            "availability": "Common in all markets",
            "cost": "Affordable"
        },
        "palak_spinach": {
            "name_en": "Spinach",
            "name_ur": "پالک",
            "name_roman": "Palak",
            "iron_mg_per_100g": 2.7,
            "serving_size": "1 cup cooked (180g)",
            "other_nutrients": ["Vitamin A", "Vitamin C", "Vitamin K", "Folate", "Calcium"],
            "preparation_tip": {
                "en": "Cook lightly. Add lemon juice for better iron absorption.",
                "ur": "ہلکا پکائیں۔ لوہے کے جذب کے لیے لیموں ڈالیں۔"
            },
            "availability": "Widely available, seasonal peak in winter",
            "cost": "Very affordable"
        },
        "channay_chickpeas": {
            "name_en": "Chickpeas (Chana)",
            "name_ur": "چنے",
            "name_roman": "Channay",
            "iron_mg_per_100g": 4.3,
            "serving_size": "1 cup cooked (164g)",
            "other_nutrients": ["Protein", "Fiber", "Folate", "Phosphorus"],
            "preparation_tip": {
                "en": "Soak overnight before cooking. Great as chana chaat.",
                "ur": "رات بھر بھگو کر پکائیں۔ چنا چاٹ بنائیں۔"
            },
            "varieties": ["Kala chana (black)", "Kabuli chana (white)", "Chana daal"],
            "availability": "Year-round",
            "cost": "Affordable"
        },
        "gur_jaggery": {
            "name_en": "Jaggery",
            "name_ur": "گڑ",
            "name_roman": "Gur",
            "iron_mg_per_100g": 11.0,
            "serving_size": "20g (small piece)",
            "other_nutrients": ["Calcium", "Magnesium", "Potassium"],
            "preparation_tip": {
                "en": "Use instead of sugar. Add to milk or eat after meals.",
                "ur": "چینی کی جگہ استعمال کریں۔ دودھ میں ڈالیں یا کھانے کے بعد کھائیں۔"
            },
            "availability": "Common, especially in winter",
            "cost": "Affordable"
        },
        "dates_khajoor": {
            "name_en": "Dates",
            "name_ur": "کھجور",
            "name_roman": "Khajoor",
            "iron_mg_per_100g": 1.0,
            "serving_size": "3-4 dates (30g)",
            "other_nutrients": ["Fiber", "Potassium", "Natural sugars", "Antioxidants"],
            "preparation_tip": {
                "en": "Eat 2-3 dates daily. Soak in milk overnight.",
                "ur": "روزانہ 2-3 کھجور کھائیں۔ دودھ میں بھگو کر کھائیں۔"
            },
            "best_varieties": ["Ajwa", "Medjool", "Aseel"],
            "availability": "Year-round, peak in Ramadan",
            "cost": "Moderate to expensive depending on variety"
        },
        "beef_gosht": {
            "name_en": "Beef",
            "name_ur": "گائے کا گوشت",
            "name_roman": "Beef/Gosht",
            "iron_mg_per_100g": 2.6,
            "serving_size": "100g cooked",
            "other_nutrients": ["Protein", "Vitamin B12", "Zinc"],
            "preparation_tip": {
                "en": "Lean cuts are healthier. Remove visible fat.",
                "ur": "کم چربی والے ٹکڑے صحت مند ہیں۔"
            },
            "availability": "Common",
            "cost": "Moderate"
        }
    },
    
    "vitamin_d_sources": {
        "eggs_anda": {
            "name_en": "Eggs",
            "name_ur": "انڈے",
            "name_roman": "Anday",
            "vitamin_d_iu_per_serving": 44,
            "serving_size": "1 large egg",
            "other_nutrients": ["Protein", "Vitamin B12", "Selenium", "Choline"],
            "tip": {
                "en": "Egg yolk contains the Vitamin D. Eat whole egg.",
                "ur": "زردی میں وٹامن ڈی ہوتا ہے۔ پورا انڈا کھائیں۔"
            },
            "availability": "Very common",
            "cost": "Affordable"
        },
        "fish_machli": {
            "name_en": "Fish (fatty varieties)",
            "name_ur": "مچھلی",
            "name_roman": "Machli",
            "vitamin_d_iu_per_100g": {
                "salmon": 526,
                "sardines": 272,
                "mackerel": 360,
                "rohu": 150
            },
            "serving_size": "100g cooked",
            "other_nutrients": ["Omega-3", "Protein", "Iodine"],
            "local_varieties": ["Rohu", "Singhari", "Palla", "Sole"],
            "tip": {
                "en": "Eat fish 2 times per week.",
                "ur": "ہفتے میں 2 بار مچھلی کھائیں۔"
            },
            "availability": "Coastal areas common, inland seasonal",
            "cost": "Moderate"
        },
        "fortified_milk_doodh": {
            "name_en": "Fortified Milk",
            "name_ur": "دودھ",
            "name_roman": "Doodh",
            "vitamin_d_iu_per_cup": 120,
            "serving_size": "1 cup (240ml)",
            "other_nutrients": ["Calcium", "Protein", "Vitamin B12"],
            "brands_fortified": ["Olpers", "Milk Pak", "Nurpur"],
            "tip": {
                "en": "Check label for 'fortified with Vitamin D'",
                "ur": "لیبل پر 'وٹامن ڈی سے بھرپور' دیکھیں"
            },
            "availability": "Urban areas common",
            "cost": "Moderate"
        },
        "sunlight": {
            "name_en": "Sunlight exposure",
            "name_ur": "دھوپ",
            "name_roman": "Dhoop",
            "recommendation": {
                "en": "15-20 minutes of morning sun (before 10 AM) on arms and face",
                "ur": "صبح 10 بجے سے پہلے 15-20 منٹ دھوپ لیں (بازو اور چہرے پر)"
            },
            "best_time": "7 AM - 10 AM",
            "avoid": "Midday sun (10 AM - 4 PM) to prevent skin damage",
            "note": "Darker skin needs more sun exposure"
        }
    },
    
    "protein_sources": {
        "daal_lentils": {
            "name_en": "Lentils (Daal)",
            "name_ur": "دال",
            "name_roman": "Daal",
            "protein_g_per_100g": 9,
            "varieties": {
                "masoor": {"en": "Red lentils", "ur": "مسور کی دال", "protein": 9},
                "moong": {"en": "Mung beans", "ur": "مونگ کی دال", "protein": 7},
                "chana": {"en": "Split chickpeas", "ur": "چنے کی دال", "protein": 8},
                "urad": {"en": "Black gram", "ur": "اڑد کی دال", "protein": 8},
                "mash": {"en": "White urad", "ur": "ماش کی دال", "protein": 8}
            },
            "other_nutrients": ["Fiber", "Iron", "Folate", "Complex carbs"],
            "tip": {
                "en": "Combine with rice for complete protein. Add lemon for iron absorption.",
                "ur": "چاول کے ساتھ کھائیں تو مکمل پروٹین ملتی ہے۔ لیموں ڈالیں۔"
            },
            "availability": "Very common, staple food",
            "cost": "Very affordable"
        },
        "chicken_murgi": {
            "name_en": "Chicken",
            "name_ur": "مرغی",
            "name_roman": "Murgi",
            "protein_g_per_100g": 27,
            "serving_size": "100g cooked",
            "other_nutrients": ["Vitamin B6", "Niacin", "Phosphorus"],
            "healthiest_parts": ["Breast (lean)", "Thigh (more flavor)"],
            "tip": {
                "en": "Remove skin to reduce fat. Grill or bake instead of frying.",
                "ur": "جلد اتار دیں۔ تلنے کی بجائے گرل یا بیک کریں۔"
            },
            "availability": "Very common",
            "cost": "Moderate"
        },
        "mutton_gosht": {
            "name_en": "Mutton/Goat meat",
            "name_ur": "بکرے کا گوشت",
            "name_roman": "Bakray ka Gosht",
            "protein_g_per_100g": 25,
            "serving_size": "100g cooked",
            "other_nutrients": ["Iron", "Vitamin B12", "Zinc"],
            "tip": {
                "en": "High in saturated fat. Eat in moderation (1-2 times/week).",
                "ur": "چربی زیادہ ہوتی ہے۔ ہفتے میں 1-2 بار کھائیں۔"
            },
            "availability": "Common",
            "cost": "Expensive"
        },
        "yogurt_dahi": {
            "name_en": "Yogurt",
            "name_ur": "دہی",
            "name_roman": "Dahi",
            "protein_g_per_100g": 3.5,
            "serving_size": "1 cup (245g)",
            "other_nutrients": ["Calcium", "Probiotics", "Vitamin B12"],
            "benefits": ["Gut health", "Digestion", "Cooling effect"],
            "tip": {
                "en": "Homemade is healthier. Have daily with meals.",
                "ur": "گھر کا بنا ہوا زیادہ صحت مند ہے۔ روزانہ کھانے کے ساتھ کھائیں۔"
            },
            "availability": "Very common",
            "cost": "Affordable"
        },
        "paneer": {
            "name_en": "Cottage Cheese",
            "name_ur": "پنیر",
            "name_roman": "Paneer",
            "protein_g_per_100g": 18,
            "serving_size": "100g",
            "other_nutrients": ["Calcium", "Phosphorus", "Vitamin B12"],
            "tip": {
                "en": "Good vegetarian protein source. Make at home from milk.",
                "ur": "سبزی خوروں کے لیے اچھی پروٹین۔ گھر پر دودھ سے بنائیں۔"
            },
            "availability": "Common",
            "cost": "Moderate"
        }
    },
    
    "foods_to_limit": {
        "processed_foods": {
            "examples": ["Chips", "Biscuits", "Instant noodles", "Packaged snacks"],
            "concerns": ["High sodium", "Trans fats", "Added sugars", "Low nutrients"],
            "recommendation": {
                "en": "Limit to occasional treats. Read nutrition labels.",
                "ur": "کبھی کبھار کھائیں۔ لیبل پڑھیں۔"
            }
        },
        "sugary_drinks": {
            "examples": ["Soft drinks", "Packaged juices", "Energy drinks", "Sweetened tea"],
            "concerns": ["Empty calories", "Diabetes risk", "Obesity", "Dental problems"],
            "recommendation": {
                "en": "Replace with water, lassi, or fresh lime water (nimbu pani).",
                "ur": "پانی، لسی، یا تازہ نمبو پانی پیں۔"
            }
        },
        "high_salt_foods": {
            "examples": ["Pickles (achaar)", "Papad", "Namkeen", "Processed meats"],
            "concerns": ["Hypertension risk", "Kidney strain", "Water retention"],
            "recommendation": {
                "en": "Limit salt to <5g (1 teaspoon) per day.",
                "ur": "نمک روزانہ 5 گرام (1 چائے کا چمچ) سے کم رکھیں۔"
            }
        },
        "fried_foods": {
            "examples": ["Samosa", "Pakora", "Paratha (fried)", "Fried fish"],
            "concerns": ["High calories", "Bad cholesterol (LDL)", "Heart disease risk"],
            "recommendation": {
                "en": "Limit deep-fried foods. Use air fryer or bake instead.",
                "ur": "تلی ہوئی چیزیں کم کھائیں۔ ایئر فرائر استعمال کریں۔"
            }
        }
    },
    
    "daily_recommendations_pakistan": {
        "description": "Based on Pakistani dietary patterns and nutritional needs",
        "balanced_plate": {
            "grains": {"portion": "25%", "examples": ["Roti (preferably whole wheat)", "Rice", "Chapati"]},
            "vegetables": {"portion": "25%", "examples": ["Seasonal sabzi", "Salad", "Raita"]},
            "protein": {"portion": "25%", "examples": ["Daal", "Meat/chicken (small portion)", "Eggs"]},
            "dairy": {"portion": "25%", "examples": ["Dahi", "Lassi", "Milk"]}
        },
        "water_intake": {
            "general": "8-10 glasses (2-2.5 liters) per day",
            "summer": "10-12 glasses (2.5-3 liters) per day",
            "tip": {
                "en": "Drink water before meals, not during. Start day with warm water.",
                "ur": "کھانے سے پہلے پانی پیں، درمیان میں نہیں۔ صبح گرم پانی سے شروع کریں۔"
            }
        }
    }
}


# ============================================================
# NIH CLINICAL DATA - SYMPTOM PATTERNS
# Source: https://www.ncbi.nlm.nih.gov/gap
# ============================================================

NIH_CLINICAL_PATTERNS = {
    "source": "NIH Open Clinical Data / PubMed Evidence",
    "url": "https://www.ncbi.nlm.nih.gov/gap",
    
    "symptom_duration_guidelines": {
        "fever": {
            "self_care_ok": "Up to 3 days if mild and no danger signs",
            "seek_doctor": "More than 3 days, or high fever >39°C, or with other symptoms",
            "emergency": "Fever with stiff neck, severe headache, confusion, rash, difficulty breathing"
        },
        "cough": {
            "self_care_ok": "Up to 2 weeks if dry cough without other symptoms",
            "seek_doctor": "More than 2 weeks, or with blood, or with weight loss, or with fever",
            "emergency": "Cough with blood, severe breathing difficulty, bluish lips"
        },
        "diarrhea": {
            "self_care_ok": "Up to 2 days if able to drink fluids",
            "seek_doctor": "More than 2 days, or with blood, or signs of dehydration",
            "emergency": "Unable to keep fluids down, blood in stool, severe abdominal pain, signs of severe dehydration"
        },
        "headache": {
            "self_care_ok": "Occasional mild headaches relieved by rest/hydration",
            "seek_doctor": "Daily headaches, progressively worsening, or with vision changes",
            "emergency": "Sudden severe 'worst headache of life', with fever and stiff neck, after head injury"
        }
    },
    
    "red_flag_symptoms": {
        "description": "Symptoms requiring immediate medical evaluation",
        "neurological": ["Sudden severe headache", "Confusion", "Seizures", "Weakness on one side", "Slurred speech", "Vision loss"],
        "cardiovascular": ["Chest pain/pressure", "Shortness of breath at rest", "Irregular heartbeat", "Leg swelling with breathlessness"],
        "gastrointestinal": ["Vomiting blood", "Black tarry stools", "Severe abdominal pain", "Jaundice"],
        "respiratory": ["Difficulty breathing", "Bluish lips/fingers", "Coughing blood"],
        "general": ["High fever not responding to medication", "Severe allergic reaction", "Signs of severe dehydration"]
    },
    
    "age_specific_considerations": {
        "infants_0_1_year": {
            "fever_threshold": "38°C - always consult doctor",
            "danger_signs": ["Not feeding", "Excessive crying", "Lethargy", "Bulging fontanelle"],
            "note": "Infants can deteriorate quickly - low threshold for seeking help"
        },
        "children_1_5_years": {
            "fever_threshold": "39°C - consult if persists >24 hours",
            "danger_signs": ["Not drinking", "Drowsiness", "Rapid breathing", "Rash"],
            "note": "Watch for dehydration signs carefully"
        },
        "elderly_over_65": {
            "considerations": ["May not show typical symptoms", "Confusion can be sign of infection", "Higher risk of complications"],
            "lower_threshold": "Seek help earlier than for younger adults",
            "note": "Fever may be absent even with serious infection"
        },
        "pregnant_women": {
            "always_consult": ["Any fever", "Vaginal bleeding", "Severe headache", "Abdominal pain", "Reduced fetal movement"],
            "avoid_self_medication": "Many medications unsafe in pregnancy"
        }
    }
}


# ============================================================
# EMERGENCY CONTACTS - PAKISTAN
# ============================================================

EMERGENCY_CONTACTS_PAKISTAN = {
    "emergency_services": {
        "rescue_1122": {
            "number": "1122",
            "services": ["Ambulance", "Fire", "Rescue"],
            "coverage": ["Punjab", "KPK", "Islamabad", "AJK", "GB"],
            "response_time": "7-10 minutes urban"
        },
        "edhi_foundation": {
            "number": "115",
            "services": ["Ambulance", "Burial services"],
            "coverage": "Nationwide",
            "note": "Largest ambulance network in Pakistan"
        },
        "chippa_foundation": {
            "number": "1021",
            "services": ["Ambulance"],
            "coverage": "Sindh, parts of other provinces"
        },
        "aman_foundation": {
            "number": "1021",
            "services": ["Ambulance", "Emergency care"],
            "coverage": "Karachi"
        }
    },
    "other_emergency": {
        "police": "15",
        "fire_brigade": "16",
        "motorway_police": "130",
        "citizen_portal": "8090"
    },
    "health_helplines": {
        "covid_helpline": "1166",
        "sehat_sahulat": "0800-00-440",
        "polio_helpline": "0800-22-111",
        "mental_health_umang": "0311-7786264"
    }
}


def get_all_knowledge():
    """Return all health knowledge as a single dictionary"""
    return {
        "who_data": WHO_HEALTH_DATA,
        "pakistan_health": PAKISTAN_HEALTH_STATISTICS,
        "nutrition_data": PAKISTAN_NUTRITION_DATA,
        "clinical_patterns": NIH_CLINICAL_PATTERNS,
        "emergency_contacts": EMERGENCY_CONTACTS_PAKISTAN
    }


# Export for use in agents
__all__ = [
    "WHO_HEALTH_DATA",
    "PAKISTAN_HEALTH_STATISTICS", 
    "PAKISTAN_NUTRITION_DATA",
    "NIH_CLINICAL_PATTERNS",
    "EMERGENCY_CONTACTS_PAKISTAN",
    "get_all_knowledge"
]

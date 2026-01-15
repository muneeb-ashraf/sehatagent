#!/usr/bin/env python3
"""
Build FAISS Index Script - FIXED VERSION
Creates the vector index for RAG from health knowledge base using Vertex AI

Run: python scripts/build_faiss_index.py
"""

import os
import sys
import json
import pickle
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# CRITICAL: Load .env file FIRST
from dotenv import load_dotenv
load_dotenv()

import numpy as np
import faiss

# Configuration from .env
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "idea92")
LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-central1")
CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "./idea92-1ad53bd857ae.json")
EMBEDDING_MODEL = os.getenv("VERTEX_AI_EMBEDDING_MODEL", "text-embedding-005")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "faiss_index")
EMBEDDING_DIMENSION = 768


def get_health_knowledge_base():
    """Load comprehensive health knowledge base"""
    
    # Try to load from knowledge module
    try:
        from app.knowledge.health_knowledge_base import (
            WHO_HEALTH_DATA,
            PAKISTAN_HEALTH_STATISTICS,
            PAKISTAN_NUTRITION_DATA
        )
        print("   ✅ Loaded knowledge from app.knowledge module")
        use_module = True
    except ImportError:
        print("   ⚠️ Could not load knowledge module, using built-in data")
        use_module = False
    
    knowledge_base = []
    
    # === SYMPTOMS ===
    knowledge_base.extend([
        {
            "id": "symptom_fever",
            "category": "symptom",
            "condition": "fever",
            "content": "Fever (Bukhar/بخار) is elevated body temperature above 38°C (100.4°F). Common in Pakistan due to typhoid, dengue, and malaria. WHO recommends paracetamol 15mg/kg for fever. Seek help if fever >3 days or >39.5°C. Home care: rest, fluids, light clothing. Danger signs: stiff neck, confusion, rash, difficulty breathing.",
            "keywords": ["fever", "bukhar", "بخار", "temperature", "typhoid", "dengue", "malaria", "paracetamol"],
            "source": "WHO IMCI Guidelines"
        },
        {
            "id": "symptom_headache",
            "category": "symptom", 
            "condition": "headache",
            "content": "Headache (Sir Dard/سر درد) causes include tension, migraine, dehydration, hypertension (33% of Pakistani adults). Red flags: worst headache ever, fever with stiff neck, after head injury. Check BP - hypertension is 'silent killer'. Drink 8-10 glasses water daily. Rest in dark room.",
            "keywords": ["headache", "sir dard", "سر درد", "migraine", "hypertension", "BP", "blood pressure"],
            "source": "Pakistan Bureau of Statistics Health Data"
        },
        {
            "id": "symptom_cough",
            "category": "symptom",
            "condition": "cough",
            "content": "Cough (Khansi/کھانسی) persisting >2 weeks needs TB test - Pakistan has 5th highest TB burden globally (259/100,000). Symptoms with TB: weight loss, night sweats, evening fever, blood in sputum. TB is CURABLE with 6-month treatment. Warm fluids, honey, steam help. Cover mouth when coughing.",
            "keywords": ["cough", "khansi", "کھانسی", "TB", "tuberculosis", "sputum", "weight loss"],
            "source": "WHO Global TB Report / Pakistan"
        },
        {
            "id": "symptom_diarrhea",
            "category": "symptom",
            "condition": "diarrhea",
            "content": "Diarrhea (Dast/دست) kills 53,000 Pakistani children annually. WHO ORS recipe: 1 liter water + ½ teaspoon salt + 6 tablespoons sugar. Give after EVERY loose stool. Continue breastfeeding. Give Zinc 10-14 days. Danger signs: blood in stool, unable to drink, sunken eyes, no urine.",
            "keywords": ["diarrhea", "dast", "دست", "ORS", "dehydration", "zinc", "loose motion"],
            "source": "WHO/UNICEF ORS Guidelines"
        },
        {
            "id": "symptom_fatigue",
            "category": "symptom",
            "condition": "fatigue",
            "content": "Fatigue (Thakan/تھکاوٹ, Kamzori/کمزوری) very common due to: Anemia (41% women, 62% children), Vitamin D deficiency (66% population). Get tested! Iron foods: kaleji (liver), palak (spinach), channay (chickpeas), gur (jaggery). Morning sunlight 15-20 min for Vitamin D.",
            "keywords": ["fatigue", "thakan", "تھکاوٹ", "kamzori", "کمزوری", "weakness", "anemia", "vitamin D"],
            "source": "Pakistan Bureau of Statistics / PDHS"
        },
    ])
    
    # === NUTRITION ===
    knowledge_base.extend([
        {
            "id": "nutrition_iron",
            "category": "nutrition",
            "condition": "iron_deficiency",
            "content": "Iron deficiency (Khoon ki Kami) affects 41% Pakistani women, 62% children. Iron-rich foods: Kaleji/کلیجی (liver) 6.5mg/100g, Palak/پالک (spinach) 2.7mg, Channay/چنے (chickpeas) 4.3mg, Gur/گڑ (jaggery) 11mg, Khajoor/کھجور (dates). Add lemon/vitamin C for better absorption.",
            "keywords": ["iron", "anemia", "khoon ki kami", "kaleji", "palak", "channay", "gur"],
            "source": "Open Food Facts / Pakistan Nutrition Data"
        },
        {
            "id": "nutrition_vitamin_d",
            "category": "nutrition",
            "condition": "vitamin_d_deficiency",
            "content": "Vitamin D deficiency affects 66% Pakistanis, 73% women. Causes: limited sun exposure, indoor lifestyle, covering clothing. Get 15-20 min morning sunlight before 10 AM. Food sources: eggs (44 IU), fish (150-500 IU), fortified milk. Most need supplements.",
            "keywords": ["vitamin D", "sunlight", "dhoop", "دھوپ", "bones", "eggs", "fish"],
            "source": "Pakistan Medical Studies"
        },
        {
            "id": "nutrition_protein",
            "category": "nutrition",
            "condition": "protein",
            "content": "Protein sources in Pakistan: Daal/دال (lentils) 7-9g/100g - combine with rice for complete protein. Chicken (murgi) 27g, Eggs (anda) 13g, Yogurt (dahi) 3.5g, Paneer 18g. Affordable options: daal, eggs, dahi, milk.",
            "keywords": ["protein", "daal", "دال", "chicken", "eggs", "milk", "dahi"],
            "source": "Open Food Facts / Pakistan Nutrition Data"
        },
    ])
    
    # === DISEASES ===
    knowledge_base.extend([
        {
            "id": "disease_diabetes",
            "category": "disease",
            "condition": "diabetes",
            "content": "Diabetes (Sugar ki Bimari) affects 26.3% Pakistani adults (33 million). 50% undiagnosed! Symptoms: excessive thirst, frequent urination, fatigue, blurred vision, slow wound healing. Get fasting blood sugar test after age 40. Control: reduce sugar/carbs, exercise 30 min daily, medication.",
            "keywords": ["diabetes", "sugar", "blood glucose", "thirst", "urination"],
            "source": "IDF Diabetes Atlas / Pakistan"
        },
        {
            "id": "disease_hypertension",
            "category": "disease",
            "condition": "hypertension",
            "content": "Hypertension (High BP) affects 33% Pakistani adults (40 million). Only 6% controlled! Silent killer - often no symptoms. Check BP regularly. Normal: <120/80. High: ≥140/90. Reduce salt to <5g/day, exercise, manage stress, quit smoking.",
            "keywords": ["hypertension", "blood pressure", "BP", "salt", "heart"],
            "source": "National Health Survey of Pakistan"
        },
        {
            "id": "disease_dengue",
            "category": "disease",
            "condition": "dengue",
            "content": "Dengue peaks August-November in Lahore, Karachi, Rawalpindi. Symptoms: high fever, severe headache, pain behind eyes, joint/muscle pain (breakbone fever), rash day 3-4. WARNING: Do NOT take aspirin - only paracetamol! Monitor platelets daily. Remove standing water to prevent mosquitoes.",
            "keywords": ["dengue", "mosquito", "fever", "platelets", "monsoon", "aspirin"],
            "source": "Pakistan Health Ministry / WHO Dengue Guidelines"
        },
        {
            "id": "disease_typhoid",
            "category": "disease",
            "condition": "typhoid",
            "content": "Typhoid (Motijhara) very common in Pakistan - 493/100,000. WARNING: 70% is now drug-resistant (XDR)! Symptoms: sustained fever, headache, stomach pain. Spread by contaminated water. Prevention: drink only boiled/filtered water, wash hands, fresh cooked food. Complete full antibiotic course!",
            "keywords": ["typhoid", "motijhara", "fever", "water", "XDR", "antibiotic"],
            "source": "Pakistan Health Ministry / WHO"
        },
        {
            "id": "disease_tb",
            "category": "disease",
            "condition": "tuberculosis",
            "content": "Pakistan has 5th highest TB burden - 510,000 cases/year. Symptoms: cough >2 weeks, blood in sputum, night sweats, weight loss, evening fever. TB is CURABLE with 6-month DOTS treatment. MUST complete full course - stopping early creates drug-resistant TB!",
            "keywords": ["TB", "tuberculosis", "cough", "sputum", "weight loss", "DOTS"],
            "source": "WHO Global TB Report"
        },
        {
            "id": "disease_hepatitis",
            "category": "disease",
            "condition": "hepatitis",
            "content": "Hepatitis C affects 5% Pakistanis (12 million). Hepatitis B: 2.5%. Causes: contaminated syringes (biggest cause), unsafe blood, barber razors. GOOD NEWS: Hepatitis C is now CURABLE in 12 weeks! Use only disposable syringes. Avoid roadside barbers.",
            "keywords": ["hepatitis", "liver", "jaundice", "yarqan", "syringe", "needle"],
            "source": "Pakistan Medical Research Council"
        },
    ])
    
    # === EMERGENCY ===
    knowledge_base.extend([
        {
            "id": "emergency_contacts",
            "category": "emergency",
            "condition": "emergency",
            "content": "Pakistan Emergency Numbers: Rescue 1122 (Punjab, KPK, Islamabad) - ambulance, fire, rescue. Edhi Foundation: 115 - nationwide ambulance. Aman Foundation: 1021 - Karachi. Police: 15. Fire: 16. Mental Health Umang: 0311-7786264.",
            "keywords": ["emergency", "1122", "115", "ambulance", "rescue", "hospital"],
            "source": "Pakistan Emergency Services"
        },
    ])
    
    return knowledge_base


def generate_embeddings_vertex(texts, credentials_path, project_id, location):
    """Generate embeddings using Vertex AI"""
    
    from google.oauth2 import service_account
    import vertexai
    from vertexai.language_models import TextEmbeddingModel
    
    # Load credentials
    credentials = service_account.Credentials.from_service_account_file(credentials_path)
    
    # Initialize Vertex AI
    vertexai.init(project=project_id, location=location, credentials=credentials)
    
    # Load embedding model
    model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL)
    
    embeddings = []
    batch_size = 5
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        try:
            batch_embeddings = model.get_embeddings(batch)
            for emb in batch_embeddings:
                embeddings.append(emb.values)
            print(f"   Processed {min(i + batch_size, len(texts))}/{len(texts)} documents")
        except Exception as e:
            print(f"   ⚠️ Batch {i} failed: {e}")
            # Add zero vectors as fallback
            for _ in batch:
                embeddings.append([0.0] * EMBEDDING_DIMENSION)
    
    return embeddings


def build_faiss_index():
    """Build and save FAISS index"""
    
    print("=" * 60)
    print("🏥 SehatAgent - FAISS Index Builder")
    print("=" * 60)
    
    print(f"\n📋 Configuration:")
    print(f"   Project ID: {PROJECT_ID}")
    print(f"   Location: {LOCATION}")
    print(f"   Credentials: {CREDENTIALS_PATH}")
    print(f"   Embedding Model: {EMBEDDING_MODEL}")
    print(f"   Output: {OUTPUT_DIR}")
    
    # Check credentials file
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"\n❌ Credentials file not found: {CREDENTIALS_PATH}")
        print("   Please ensure GOOGLE_APPLICATION_CREDENTIALS is set in .env")
        sys.exit(1)
    
    # Load knowledge base
    print(f"\n📚 Loading health knowledge base...")
    knowledge_base = get_health_knowledge_base()
    print(f"   ✅ Loaded {len(knowledge_base)} documents")
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Generate embeddings
    print(f"\n🔄 Generating embeddings with Vertex AI...")
    texts = [doc["content"] for doc in knowledge_base]
    
    try:
        embeddings = generate_embeddings_vertex(texts, CREDENTIALS_PATH, PROJECT_ID, LOCATION)
        
        # Create FAISS index
        print(f"\n📦 Creating FAISS index...")
        embedding_array = np.array(embeddings).astype('float32')
        
        index = faiss.IndexFlatL2(EMBEDDING_DIMENSION)
        index.add(embedding_array)
        
        # Save index
        index_path = os.path.join(OUTPUT_DIR, "index.faiss")
        faiss.write_index(index, index_path)
        print(f"   ✅ Saved FAISS index: {index_path}")
        
        embeddings_generated = True
        
    except Exception as e:
        print(f"\n⚠️ Vertex AI embedding failed: {e}")
        print("   Creating index without embeddings (will use keyword search)")
        embeddings_generated = False
    
    # Save documents (always)
    docs_path = os.path.join(OUTPUT_DIR, "documents.pkl")
    with open(docs_path, "wb") as f:
        pickle.dump(knowledge_base, f)
    print(f"   ✅ Saved documents: {docs_path}")
    
    # Save as JSON for inspection
    json_path = os.path.join(OUTPUT_DIR, "documents.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(knowledge_base, f, indent=2, ensure_ascii=False)
    print(f"   ✅ Saved JSON: {json_path}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 BUILD SUMMARY")
    print("=" * 60)
    print(f"   Documents: {len(knowledge_base)}")
    print(f"   Embeddings: {'✅ Generated' if embeddings_generated else '❌ Skipped'}")
    print(f"   Index: {OUTPUT_DIR}")
    print("\n✅ FAISS index build complete!")


if __name__ == "__main__":
    build_faiss_index()
#!/usr/bin/env python3
"""
Build FAISS Index Script
Creates the vector index for RAG from health knowledge base

Run this script before deployment to pre-build the FAISS index.
"""

import os
import sys
import json
import pickle
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import faiss
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel

# Configuration
PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
LOCATION = os.environ.get("GCP_REGION", "us-central1")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "faiss_index")
EMBEDDING_DIMENSION = 768


def get_health_knowledge_base():
    """Load the health knowledge base"""
    knowledge_base = []
    
    # Symptoms
    symptoms_data = [
        {
            "category": "symptom",
            "condition": "fever",
            "content": "Fever (Bukhar) is elevated body temperature, usually above 98.6°F (37°C). Common causes include viral infections, bacterial infections like typhoid, dengue fever, and malaria. In Pakistan, typhoid and dengue are particularly common. Treatment includes rest, hydration with ORS, and paracetamol. Seek medical attention if fever persists beyond 3 days or exceeds 103°F.",
            "keywords": ["fever", "bukhar", "temperature", "typhoid", "dengue"]
        },
        {
            "category": "symptom",
            "condition": "headache",
            "content": "Headache (Sir Dard) can be caused by tension, migraine, dehydration, stress, or underlying conditions like hypertension. In Pakistan, headaches are often related to dehydration due to hot climate. Treatment includes rest, hydration, and pain relievers. Severe headaches with fever may indicate meningitis.",
            "keywords": ["headache", "sir dard", "migraine", "tension"]
        },
        {
            "category": "symptom",
            "condition": "cough",
            "content": "Cough (Khansi) can be dry or productive. Common causes include common cold, flu, allergies, and tuberculosis (TB) in persistent cases. TB is prevalent in Pakistan. Treat with warm fluids, honey, and steam inhalation. If cough persists beyond 2 weeks with weight loss or night sweats, get tested for TB.",
            "keywords": ["cough", "khansi", "cold", "tuberculosis", "TB"]
        },
        {
            "category": "symptom",
            "condition": "diarrhea",
            "content": "Diarrhea (Dast) involves loose, watery stools and is common in Pakistan due to waterborne diseases. Main causes include contaminated water, food poisoning, and viral gastroenteritis. Critical treatment is ORS (Oral Rehydration Solution) to prevent dehydration.",
            "keywords": ["diarrhea", "dast", "loose motion", "dehydration", "ORS"]
        },
        {
            "category": "symptom",
            "condition": "fatigue",
            "content": "Fatigue (Thakan/Kamzori) is persistent tiredness not relieved by rest. Common causes include anemia (very common in Pakistan), vitamin deficiencies (D, B12), diabetes, thyroid issues, and sleep disorders. Iron-rich foods like palak, kaleji, channay help with anemia.",
            "keywords": ["fatigue", "thakan", "kamzori", "weakness", "anemia"]
        },
    ]
    
    # Nutrition
    nutrition_data = [
        {
            "category": "nutrition",
            "condition": "iron_deficiency",
            "content": "Iron deficiency (Khoon ki Kami) is very common in Pakistan, especially among women and children. Symptoms include fatigue, weakness, pale skin, and dizziness. Iron-rich Pakistani foods include: Palak (spinach), Kaleji (liver), Channay (chickpeas), Gur (jaggery), and dates.",
            "keywords": ["iron", "anemia", "khoon ki kami", "weakness", "palak", "kaleji"]
        },
        {
            "category": "nutrition",
            "condition": "vitamin_d_deficiency",
            "content": "Vitamin D deficiency affects about 66% of Pakistan's population. Symptoms include fatigue, bone pain, and muscle weakness. Get 15-20 minutes of morning sunlight. Eat eggs, fish, and fortified milk.",
            "keywords": ["vitamin d", "sunlight", "bones", "weakness", "calcium"]
        },
        {
            "category": "nutrition",
            "condition": "protein_deficiency",
            "content": "Protein deficiency is common in Pakistan, especially in low-income families. Symptoms include weakness, slow healing, hair loss. Good protein sources: Daal (lentils), Gosht (meat), Murgi (chicken), Machli (fish), eggs, milk.",
            "keywords": ["protein", "daal", "meat", "weakness", "growth"]
        },
    ]
    
    # Diseases
    disease_data = [
        {
            "category": "disease",
            "condition": "diabetes",
            "content": "Diabetes (Sugar ki Bimari) affects about 26% of Pakistan's adult population. Symptoms include excessive thirst, frequent urination, fatigue, blurred vision. Control through diet (avoid sugar, refined carbs), regular exercise, and medication.",
            "keywords": ["diabetes", "sugar", "thirst", "urination", "blood sugar"]
        },
        {
            "category": "disease",
            "condition": "hypertension",
            "content": "Hypertension (High Blood Pressure) affects about 33% of adults in Pakistan. Often called 'silent killer'. Symptoms include headache, dizziness, chest pain. Reduce salt, exercise regularly, manage stress.",
            "keywords": ["hypertension", "blood pressure", "BP", "heart", "salt"]
        },
        {
            "category": "disease",
            "condition": "dengue",
            "content": "Dengue fever is common in Pakistan during monsoon season (July-November). Symptoms include high fever, severe headache, pain behind eyes, muscle pain, rash. No specific treatment - rest, hydration, paracetamol (avoid aspirin).",
            "keywords": ["dengue", "mosquito", "fever", "monsoon", "rash"]
        },
        {
            "category": "disease",
            "condition": "typhoid",
            "content": "Typhoid (Motijhara) is common in Pakistan due to contaminated water. Symptoms include sustained fever, headache, stomach pain. Prevention: drink boiled/filtered water, eat freshly cooked food, wash hands.",
            "keywords": ["typhoid", "motijhara", "fever", "water", "contamination"]
        },
        {
            "category": "disease",
            "condition": "tuberculosis",
            "content": "Tuberculosis (TB) is prevalent in Pakistan. Symptoms include persistent cough (>2 weeks), weight loss, night sweats, fever. TB is curable with proper medication. Complete the full course of treatment.",
            "keywords": ["tuberculosis", "TB", "cough", "weight loss", "infection"]
        },
    ]
    
    knowledge_base.extend(symptoms_data)
    knowledge_base.extend(nutrition_data)
    knowledge_base.extend(disease_data)
    
    return knowledge_base


def generate_embeddings(texts, model):
    """Generate embeddings using Vertex AI"""
    embeddings = []
    batch_size = 5
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_embeddings = model.get_embeddings(batch)
        
        for embedding in batch_embeddings:
            embeddings.append(embedding.values)
        
        print(f"Processed {min(i + batch_size, len(texts))}/{len(texts)} documents")
    
    return embeddings


def build_faiss_index():
    """Build and save FAISS index"""
    print("=" * 50)
    print("SehatAgent - FAISS Index Builder")
    print("=" * 50)
    
    # Initialize Vertex AI
    if PROJECT_ID:
        print(f"\nInitializing Vertex AI (Project: {PROJECT_ID})...")
        aiplatform.init(project=PROJECT_ID, location=LOCATION)
        embedding_model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")
    else:
        print("\nNo GCP_PROJECT_ID set. Creating index without embeddings.")
        embedding_model = None
    
    # Load knowledge base
    print("\nLoading health knowledge base...")
    knowledge_base = get_health_knowledge_base()
    print(f"Loaded {len(knowledge_base)} documents")
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if embedding_model:
        # Generate embeddings
        print("\nGenerating embeddings...")
        texts = [doc["content"] for doc in knowledge_base]
        embeddings = generate_embeddings(texts, embedding_model)
        
        # Create FAISS index
        print("\nCreating FAISS index...")
        embedding_array = np.array(embeddings).astype('float32')
        
        index = faiss.IndexFlatL2(EMBEDDING_DIMENSION)
        index.add(embedding_array)
        
        # Save index
        index_path = os.path.join(OUTPUT_DIR, "index.faiss")
        faiss.write_index(index, index_path)
        print(f"Saved FAISS index to {index_path}")
    else:
        print("\nSkipping embedding generation (no Vertex AI)")
    
    # Save documents
    docs_path = os.path.join(OUTPUT_DIR, "documents.pkl")
    with open(docs_path, "wb") as f:
        pickle.dump(knowledge_base, f)
    print(f"Saved documents to {docs_path}")
    
    # Save as JSON for inspection
    json_path = os.path.join(OUTPUT_DIR, "documents.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(knowledge_base, f, indent=2, ensure_ascii=False)
    print(f"Saved JSON to {json_path}")
    
    print("\n" + "=" * 50)
    print("FAISS index build complete!")
    print("=" * 50)


if __name__ == "__main__":
    build_faiss_index()

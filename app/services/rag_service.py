"""
RAG Service for SehatAgent
Retrieval Augmented Generation using FAISS and health knowledge base

Data Sources:
- WHO Global Health Data (https://www.who.int/data)
- Pakistan Bureau of Statistics (https://pslm-sdgs.data.gov.pk/health/index)
- NIH Clinical Data (https://www.ncbi.nlm.nih.gov/gap)
- Open Food Facts (https://world.openfoodfacts.org/data)
"""

import os
import json
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import structlog

from app.config import get_settings
from app.knowledge.health_knowledge_base import (
    WHO_HEALTH_DATA,
    PAKISTAN_HEALTH_STATISTICS,
    PAKISTAN_NUTRITION_DATA,
    NIH_CLINICAL_PATTERNS,
    EMERGENCY_CONTACTS_PAKISTAN
)

logger = structlog.get_logger()
settings = get_settings()


class RAGService:
    """
    RAG Service using FAISS for vector search.
    Falls back to keyword search when embeddings unavailable.
    """
    
    def __init__(self):
        self.index = None
        self.documents = []
        self.embeddings_available = False
        self.vertex_service = None
        self.index_path = Path(settings.FAISS_INDEX_PATH)
        self.dimension = settings.FAISS_DIMENSION
        
    async def initialize(self, vertex_service=None):
        """Initialize RAG service with optional Vertex AI for embeddings"""
        
        self.vertex_service = vertex_service
        
        # Try to load pre-built index
        if self._load_index():
            logger.info("Loaded pre-built FAISS index")
            return
        
        # Build from knowledge base
        await self._build_knowledge_base()
        
    def _load_index(self) -> bool:
        """Load pre-built FAISS index if available"""
        
        index_file = self.index_path / "index.faiss"
        docs_file = self.index_path / "documents.pkl"
        
        if index_file.exists() and docs_file.exists():
            try:
                import faiss
                self.index = faiss.read_index(str(index_file))
                
                with open(docs_file, "rb") as f:
                    self.documents = pickle.load(f)
                
                self.embeddings_available = True
                return True
            except Exception as e:
                logger.warning(f"Failed to load FAISS index: {e}")
        
        return False
    
    async def _build_knowledge_base(self):
        """Build knowledge base from all data sources"""
        
        logger.info("Building knowledge base from health data sources...")
        
        # Collect all documents
        self.documents = []
        
        # 1. Add WHO Health Data
        self._add_who_data()
        
        # 2. Add Pakistan Health Statistics
        self._add_pakistan_health_data()
        
        # 3. Add Nutrition Data
        self._add_nutrition_data()
        
        # 4. Add NIH Clinical Patterns
        self._add_nih_data()
        
        # 5. Load downloaded data if available
        self._load_downloaded_data()
        
        logger.info(f"Built knowledge base with {len(self.documents)} documents")
        
        # Try to create FAISS index with embeddings
        if self.vertex_service:
            try:
                await self._create_faiss_index()
            except Exception as e:
                logger.warning(f"Could not create FAISS embeddings: {e}")
                logger.info("Using keyword-based search as fallback")
    
    def _add_who_data(self):
        """Add WHO health guidelines to knowledge base"""
        
        # Fever management
        self.documents.append({
            "id": "who_fever",
            "category": "symptom_management",
            "source": "WHO Global Health Data",
            "source_url": "https://www.who.int/data",
            "content": f"WHO Fever Management: Normal temperature is 37°C. Fever is defined as 38°C or above. "
                      f"For mild fever, give extra fluids and rest. For high fever (39°C+), give paracetamol "
                      f"15mg/kg and seek medical attention. WHO recommends tepid sponging only for very high fever.",
            "keywords": ["fever", "temperature", "bukhar", "paracetamol", "who"]
        })
        
        # ORS guidelines
        ors = WHO_HEALTH_DATA["dehydration_protocol"]["ors_who_formula"]["home_recipe"]
        self.documents.append({
            "id": "who_ors",
            "category": "treatment",
            "source": "WHO/UNICEF",
            "source_url": "https://www.who.int/data",
            "content": f"WHO ORS Recipe: {ors['water_liters']} liter clean water + {ors['salt_teaspoon']} "
                      f"teaspoon salt + {ors['sugar_tablespoons']} tablespoons sugar. Give after every loose stool. "
                      f"Continue breastfeeding. ORS saves lives by preventing dehydration.",
            "keywords": ["ors", "dehydration", "diarrhea", "dast", "namkol", "rehydration"]
        })
        
        # Danger signs
        danger_signs = WHO_HEALTH_DATA["imci_danger_signs"]["children_under_5"]
        self.documents.append({
            "id": "who_danger_signs",
            "category": "emergency",
            "source": "WHO IMCI Guidelines",
            "source_url": "https://www.who.int/data",
            "content": f"WHO Danger Signs in Children: {', '.join(danger_signs)}. "
                      f"If any of these signs present, refer URGENTLY to hospital. Do not delay.",
            "keywords": ["danger", "emergency", "children", "urgent", "hospital"]
        })
    
    def _add_pakistan_health_data(self):
        """Add Pakistan Bureau of Statistics health data"""
        
        disease_data = PAKISTAN_HEALTH_STATISTICS["disease_burden"]
        
        # Diabetes
        diabetes = disease_data["diabetes_mellitus"]
        self.documents.append({
            "id": "pak_diabetes",
            "category": "disease",
            "source": "Pakistan Bureau of Statistics",
            "source_url": "https://pslm-sdgs.data.gov.pk/health/index",
            "content": f"Diabetes in Pakistan: {diabetes['prevalence_percent']}% prevalence "
                      f"({diabetes['affected_adults_millions']} million adults). "
                      f"Symptoms: excessive thirst, frequent urination, fatigue, blurred vision. "
                      f"50% are undiagnosed. Get fasting blood sugar test after age 40.",
            "keywords": ["diabetes", "sugar", "thirst", "urination", "blood glucose"]
        })
        
        # Hypertension
        htn = disease_data["hypertension"]
        self.documents.append({
            "id": "pak_hypertension",
            "category": "disease",
            "source": "Pakistan Bureau of Statistics",
            "source_url": "https://pslm-sdgs.data.gov.pk/health/index",
            "content": f"Hypertension in Pakistan: {htn['prevalence_percent']}% prevalence "
                      f"({htn['affected_adults_millions']} million). Known as 'silent killer'. "
                      f"Only {htn['awareness_percent']}% are aware. Symptoms: headache, dizziness. "
                      f"Prevention: reduce salt, exercise, manage stress.",
            "keywords": ["hypertension", "blood pressure", "bp", "headache", "dizziness", "salt"]
        })
        
        # Anemia
        anemia = disease_data["anemia"]
        self.documents.append({
            "id": "pak_anemia",
            "category": "deficiency",
            "source": "Pakistan Bureau of Statistics / PDHS",
            "source_url": "https://pslm-sdgs.data.gov.pk/health/index",
            "content": f"Anemia in Pakistan: {anemia['women_prevalence_percent']}% in women, "
                      f"{anemia['children_prevalence_percent']}% in children. Very common! "
                      f"Symptoms: fatigue, weakness, pale skin, dizziness. "
                      f"Eat iron-rich foods: kaleji (liver), palak (spinach), chana (chickpeas), gur (jaggery).",
            "keywords": ["anemia", "iron", "fatigue", "weakness", "pale", "kaleji", "palak", "khoon ki kami"]
        })
        
        # Vitamin D
        vitd = disease_data["vitamin_d_deficiency"]
        self.documents.append({
            "id": "pak_vitamin_d",
            "category": "deficiency",
            "source": "Pakistan Medical Studies",
            "source_url": "https://pslm-sdgs.data.gov.pk/health/index",
            "content": f"Vitamin D Deficiency: {vitd['prevalence_percent']}% of Pakistanis are deficient! "
                      f"{vitd['women_prevalence_percent']}% in women. Symptoms: bone pain, muscle weakness, fatigue. "
                      f"Get 15-20 minutes morning sunlight before 10 AM. Eat eggs, fish, fortified milk.",
            "keywords": ["vitamin d", "sunlight", "bones", "fatigue", "muscle weakness", "dhoop"]
        })
        
        # Typhoid
        typhoid = disease_data["typhoid_fever"]
        self.documents.append({
            "id": "pak_typhoid",
            "category": "disease",
            "source": "Pakistan Health Ministry / WHO",
            "source_url": "https://pslm-sdgs.data.gov.pk/health/index",
            "content": f"Typhoid in Pakistan: Very common ({typhoid['annual_incidence']} per 100,000). "
                      f"WARNING: {typhoid['xdr_typhoid_percent']}% is now drug-resistant (XDR)! "
                      f"Symptoms: sustained fever, headache, stomach pain. Spread by contaminated water. "
                      f"Prevention: drink only boiled/filtered water, wash hands, eat freshly cooked food.",
            "keywords": ["typhoid", "fever", "motijhara", "water", "contaminated"]
        })
        
        # Dengue
        dengue = disease_data["dengue_fever"]
        self.documents.append({
            "id": "pak_dengue",
            "category": "disease",
            "source": "Pakistan Health Ministry",
            "source_url": "https://pslm-sdgs.data.gov.pk/health/index",
            "content": f"Dengue in Pakistan: Peak season August-November. High risk in {', '.join(dengue['high_risk_cities'])}. "
                      f"Symptoms: high fever, severe headache, pain behind eyes, joint/muscle pain, rash. "
                      f"WARNING: Do NOT take aspirin! Only paracetamol. Monitor platelets daily. "
                      f"Prevention: remove standing water, use mosquito nets and repellents.",
            "keywords": ["dengue", "fever", "mosquito", "platelets", "aspirin", "monsoon"]
        })
        
        # TB
        tb = disease_data["tuberculosis"]
        self.documents.append({
            "id": "pak_tb",
            "category": "disease",
            "source": "WHO Global TB Report / Pakistan",
            "source_url": "https://pslm-sdgs.data.gov.pk/health/index",
            "content": f"TB in Pakistan: {tb['ranking']} - {tb['incidence_per_100k']} cases per 100,000. "
                      f"Symptoms: cough >2 weeks, blood in sputum, night sweats, weight loss, evening fever. "
                      f"TB is CURABLE with 6-month treatment. MUST complete full course - stopping early creates drug resistance!",
            "keywords": ["tb", "tuberculosis", "cough", "weight loss", "night sweats", "sputum"]
        })
        
        # Hepatitis
        hep = disease_data["hepatitis_b_c"]
        self.documents.append({
            "id": "pak_hepatitis",
            "category": "disease",
            "source": "Pakistan Medical Research Council",
            "source_url": "https://pslm-sdgs.data.gov.pk/health/index",
            "content": f"Hepatitis in Pakistan: Hepatitis B: {hep['hepatitis_b_prevalence_percent']}%, "
                      f"Hepatitis C: {hep['hepatitis_c_prevalence_percent']}% ({hep['hepatitis_c_affected_millions']} million). "
                      f"GOOD NEWS: Hepatitis C is now CURABLE in 12 weeks! "
                      f"Prevention: use only disposable syringes, avoid roadside barbers, don't share razors.",
            "keywords": ["hepatitis", "liver", "jaundice", "yarqan", "syringe", "needle"]
        })
    
    def _add_nutrition_data(self):
        """Add nutrition data from Open Food Facts and local sources"""
        
        # Iron-rich foods
        iron_foods = PAKISTAN_NUTRITION_DATA["iron_rich_foods"]
        iron_list = [f"{v['name_roman']} ({v['name_en']}): {v['iron_mg_per_100g']}mg/100g" 
                     for k, v in iron_foods.items()]
        
        self.documents.append({
            "id": "nutrition_iron",
            "category": "nutrition",
            "source": "Open Food Facts / Pakistan Nutrition Data",
            "source_url": "https://world.openfoodfacts.org/data",
            "content": f"Iron-rich Pakistani Foods for Anemia: {'; '.join(iron_list)}. "
                      f"Iron deficiency is very common (41% women). Eat these foods regularly. "
                      f"Add lemon/vitamin C to improve iron absorption.",
            "keywords": ["iron", "anemia", "kaleji", "palak", "chana", "gur", "khajoor"]
        })
        
        # Vitamin D sources
        vitd_foods = PAKISTAN_NUTRITION_DATA["vitamin_d_sources"]
        self.documents.append({
            "id": "nutrition_vitamin_d",
            "category": "nutrition",
            "source": "Open Food Facts / Pakistan Nutrition Data",
            "source_url": "https://world.openfoodfacts.org/data",
            "content": f"Vitamin D Sources: Best source is morning sunlight (15-20 min before 10 AM). "
                      f"Foods: eggs (44 IU/egg), fish (150-500 IU/100g), fortified milk. "
                      f"66% of Pakistanis are deficient! Most need supplements.",
            "keywords": ["vitamin d", "sunlight", "eggs", "fish", "milk", "dhoop"]
        })
        
        # Protein sources
        protein_foods = PAKISTAN_NUTRITION_DATA["protein_sources"]
        protein_list = [f"{v['name_roman']} ({v['protein_g_per_100g']}g/100g)" 
                        for k, v in protein_foods.items() if 'protein_g_per_100g' in v]
        
        self.documents.append({
            "id": "nutrition_protein",
            "category": "nutrition",
            "source": "Open Food Facts / Pakistan Nutrition Data",
            "source_url": "https://world.openfoodfacts.org/data",
            "content": f"Protein Sources in Pakistan: {'; '.join(protein_list)}. "
                      f"Daal (lentils) combined with rice provides complete protein. "
                      f"Affordable protein: daal, eggs, dahi (yogurt), milk.",
            "keywords": ["protein", "daal", "chicken", "eggs", "milk", "meat"]
        })
    
    def _add_nih_data(self):
        """Add NIH clinical guidelines"""
        
        # Symptom duration guidelines
        duration = NIH_CLINICAL_PATTERNS["symptom_duration_guidelines"]
        
        self.documents.append({
            "id": "nih_symptom_duration",
            "category": "clinical_guideline",
            "source": "NIH Clinical Guidelines",
            "source_url": "https://www.ncbi.nlm.nih.gov/gap",
            "content": f"When to see a doctor: Fever >3 days or >39°C. Cough >2 weeks or with blood. "
                      f"Diarrhea >2 days or with blood. Headache: sudden severe, or with fever+stiff neck. "
                      f"These are general guidelines - when in doubt, seek medical help.",
            "keywords": ["duration", "when to see doctor", "symptoms", "guidelines"]
        })
        
        # Red flag symptoms
        red_flags = NIH_CLINICAL_PATTERNS["red_flag_symptoms"]
        all_flags = []
        for category, symptoms in red_flags.items():
            all_flags.extend(symptoms[:2])
        
        self.documents.append({
            "id": "nih_red_flags",
            "category": "emergency",
            "source": "NIH Clinical Guidelines",
            "source_url": "https://www.ncbi.nlm.nih.gov/gap",
            "content": f"Red Flag Symptoms - Seek immediate help: {'; '.join(all_flags)}. "
                      f"These symptoms may indicate serious conditions requiring urgent care.",
            "keywords": ["emergency", "red flag", "urgent", "serious", "hospital"]
        })
    
    def _load_downloaded_data(self):
        """Load data from downloaded JSON files if available"""
        
        data_dir = Path("./data")
        
        # Load Open Food Facts data
        off_file = data_dir / "openfoodfacts_pakistan.json"
        if off_file.exists():
            try:
                with open(off_file, "r", encoding="utf-8") as f:
                    off_data = json.load(f)
                    
                for product in off_data.get("products", [])[:20]:
                    self.documents.append({
                        "id": f"off_{product.get('search_term', '')}",
                        "category": "nutrition",
                        "source": "Open Food Facts API",
                        "source_url": "https://world.openfoodfacts.org/data",
                        "content": f"Food: {product.get('name', '')}. "
                                  f"Nutrients per 100g: Protein {product.get('nutriments', {}).get('proteins_g', 'N/A')}g, "
                                  f"Iron {product.get('nutriments', {}).get('iron_mg', 'N/A')}mg.",
                        "keywords": [product.get('search_term', ''), "nutrition", "food"]
                    })
                
                logger.info(f"Loaded {len(off_data.get('products', []))} products from Open Food Facts")
            except Exception as e:
                logger.warning(f"Could not load Open Food Facts data: {e}")
    
    async def _create_faiss_index(self):
        """Create FAISS index with embeddings"""
        
        import faiss
        
        logger.info("Creating FAISS index with embeddings...")
        
        # Generate embeddings for all documents
        texts = [doc["content"] for doc in self.documents]
        embeddings = []
        
        batch_size = 5
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await self.vertex_service.get_embeddings(batch)
            embeddings.extend(batch_embeddings)
        
        # Create FAISS index
        embedding_array = np.array(embeddings).astype('float32')
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(embedding_array)
        
        self.embeddings_available = True
        
        # Save index
        self.index_path.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.index_path / "index.faiss"))
        
        with open(self.index_path / "documents.pkl", "wb") as f:
            pickle.dump(self.documents, f)
        
        logger.info(f"Created FAISS index with {len(self.documents)} documents")
    
    async def search(
        self, 
        query: str, 
        top_k: int = 5,
        filter_category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search knowledge base"""
        
        if self.embeddings_available and self.vertex_service:
            return await self._vector_search(query, top_k, filter_category)
        else:
            return self._keyword_search(query, top_k, filter_category)
    
    async def _vector_search(
        self, 
        query: str, 
        top_k: int,
        filter_category: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Vector similarity search using FAISS"""
        
        # Get query embedding
        query_embedding = await self.vertex_service.get_embeddings([query])
        query_vector = np.array(query_embedding).astype('float32')
        
        # Search
        distances, indices = self.index.search(query_vector, top_k * 2)
        
        # Get results
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.documents):
                doc = self.documents[idx].copy()
                doc["score"] = float(1 / (1 + distance))
                
                if filter_category and doc.get("category") != filter_category:
                    continue
                    
                results.append(doc)
                
                if len(results) >= top_k:
                    break
        
        return results
    
    def _keyword_search(
        self, 
        query: str, 
        top_k: int,
        filter_category: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Keyword-based search fallback"""
        
        query_words = set(query.lower().split())
        
        scored_docs = []
        for doc in self.documents:
            if filter_category and doc.get("category") != filter_category:
                continue
            
            # Score based on keyword matches
            keywords = set(doc.get("keywords", []))
            content_words = set(doc.get("content", "").lower().split())
            
            keyword_matches = len(query_words & keywords)
            content_matches = len(query_words & content_words)
            
            score = keyword_matches * 2 + content_matches * 0.5
            
            if score > 0:
                doc_copy = doc.copy()
                doc_copy["score"] = score
                scored_docs.append(doc_copy)
        
        # Sort by score
        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        
        return scored_docs[:top_k]
    
    async def health_check(self) -> bool:
        """Check if RAG service is operational"""
        return len(self.documents) > 0

"""
Vertex AI Service
Integration with Google Cloud Vertex AI for LLM and embeddings
"""

from typing import Optional, List, Dict, Any
import asyncio
import structlog
import os
from tenacity import retry, stop_after_attempt, wait_exponential

from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig
import vertexai

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class VertexAIService:
    """
    Service for interacting with Vertex AI
    
    Features:
    - Text generation with Gemini
    - Embedding generation for RAG
    - Health check functionality
    - Automatic retry with exponential backoff
    """
    
    def __init__(self):
        self.project_id = settings.GCP_PROJECT_ID
        self.location = settings.VERTEX_AI_LOCATION
        self.model_name = settings.VERTEX_AI_MODEL
        self.embedding_model = settings.VERTEX_AI_EMBEDDING_MODEL
        self.model: Optional[GenerativeModel] = None
        self.is_initialized = False
        self.logger = logger.bind(service="vertex_ai")
    
    async def initialize(self):
        """Initialize Vertex AI client"""
        try:
            # Initialize Vertex AI
            vertexai.init(
                project=self.project_id,
                location=self.location
            )
            
            # Load the generative model
            self.model = GenerativeModel(self.model_name)
            
            # Test connection
            await self.health_check()
            
            self.is_initialized = True
            self.logger.info("Vertex AI initialized",
                           project=self.project_id,
                           model=self.model_name)
            
        except Exception as e:
            self.logger.error("Vertex AI initialization failed", error=str(e))
            raise
    
    async def health_check(self) -> bool:
        """Check if Vertex AI is accessible"""
        try:
            response = await self.generate(
                prompt="Say 'OK' if you are working.",
                max_tokens=10
            )
            return response is not None and len(response) > 0
        except Exception as e:
            self.logger.warning("Vertex AI health check failed", error=str(e))
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        top_p: float = 0.95,
        top_k: int = 40
    ) -> Optional[str]:
        """
        Generate text using Gemini model
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instructions
            temperature: Creativity (0-1)
            max_tokens: Maximum response length
            
        Returns:
            Generated text or None if failed
        """
        if not self.model:
            self.logger.error("Model not initialized")
            return None
        
        try:
            # Build the full prompt
            full_prompt = ""
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n"
            full_prompt += prompt
            
            # Configure generation parameters
            generation_config = GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                top_p=top_p,
                top_k=top_k
            )
            
            # Generate response (run in thread pool for async)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(
                    full_prompt,
                    generation_config=generation_config
                )
            )
            
            # Extract text from response
            if response and response.text:
                return response.text.strip()
            
            return None
            
        except Exception as e:
            self.logger.error("Generation failed", error=str(e))
            raise
    
    async def generate_embeddings(
        self,
        texts: List[str],
        task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> List[List[float]]:
        """
        Generate embeddings for texts using Vertex AI
        
        Args:
            texts: List of texts to embed
            task_type: Type of embedding task
            
        Returns:
            List of embedding vectors
        """
        try:
            from vertexai.language_models import TextEmbeddingModel
            
            model = TextEmbeddingModel.from_pretrained(self.embedding_model)
            
            embeddings = []
            # Process in batches of 5
            batch_size = 5
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                loop = asyncio.get_event_loop()
                batch_embeddings = await loop.run_in_executor(
                    None,
                    lambda b=batch: model.get_embeddings(b)
                )
                
                for embedding in batch_embeddings:
                    embeddings.append(embedding.values)
            
            return embeddings
            
        except Exception as e:
            self.logger.error("Embedding generation failed", error=str(e))
            raise
    
    async def generate_single_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        embeddings = await self.generate_embeddings([text], task_type="RETRIEVAL_QUERY")
        return embeddings[0] if embeddings else []
    
    async def analyze_health_query(
        self,
        user_input: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Specialized health query analysis
        
        Args:
            user_input: User's health query
            language: User's language
            
        Returns:
            Structured health analysis
        """
        system_prompt = """You are a healthcare AI assistant for Pakistan. Analyze health queries and provide:
1. Identified symptoms
2. Possible conditions (considering Pakistan-specific diseases)
3. Risk level (low/medium/high)
4. Recommended actions

Always include appropriate medical disclaimers. Be culturally sensitive.
Respond in JSON format."""

        prompt = f"""Analyze this health query:

Query: "{user_input}"
Language: {language}

Provide analysis as JSON:
{{
    "symptoms": ["list of symptoms"],
    "possible_conditions": ["list of conditions"],
    "risk_level": "low/medium/high",
    "recommendations": ["list of recommendations"],
    "see_doctor": true/false,
    "urgency": "routine/soon/urgent/emergency"
}}"""

        response = await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.2
        )
        
        if response:
            try:
                import json
                # Clean and parse JSON
                response = response.strip()
                if response.startswith("```"):
                    response = response.split("```")[1]
                    if response.startswith("json"):
                        response = response[4:]
                return json.loads(response)
            except:
                pass
        
        return {}
    
    async def translate_text(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """Translate text using Gemini"""
        prompt = f"""Translate the following text from {source_lang} to {target_lang}.
Maintain the meaning and tone. Only output the translation, nothing else.

Text: {text}

Translation:"""
        
        response = await self.generate(prompt, temperature=0.1, max_tokens=512)
        return response if response else text

"""
Speech Service
Handles voice input transcription for Urdu and Punjabi
"""

from typing import Optional, Tuple
import io
import structlog
from google.cloud import speech_v1 as speech

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class SpeechService:
    """
    Service for speech-to-text transcription
    
    Features:
    - Support for Urdu (ur-PK)
    - Support for Punjabi (pa-IN)
    - Support for English (en-US, en-IN)
    - Multi-language detection
    - Audio format handling
    """
    
    def __init__(self):
        self.client: Optional[speech.SpeechClient] = None
        self.logger = logger.bind(service="speech")
        
        # Supported language codes
        self.language_codes = {
            "ur": "ur-PK",      # Urdu (Pakistan)
            "pa": "pa-IN",      # Punjabi (India - closest available)
            "en": "en-US",      # English (US)
            "en_pk": "en-IN",   # English (India - closer to Pakistani accent)
        }
        
        # Default multi-language config
        self.default_languages = ["ur-PK", "en-US", "pa-IN"]
    
    async def initialize(self):
        """Initialize the Speech client"""
        try:
            self.client = speech.SpeechClient()
            self.logger.info("Speech service initialized")
        except Exception as e:
            self.logger.error("Speech service initialization failed", error=str(e))
            raise
    
    async def transcribe_audio(
        self,
        audio_content: bytes,
        language_hint: str = None,
        sample_rate: int = 16000,
        encoding: str = "LINEAR16"
    ) -> Tuple[Optional[str], str, float]:
        """
        Transcribe audio to text
        
        Args:
            audio_content: Audio bytes
            language_hint: Expected language (ur, pa, en)
            sample_rate: Audio sample rate in Hz
            encoding: Audio encoding format
            
        Returns:
            Tuple of (transcription, detected_language, confidence)
        """
        if not self.client:
            await self.initialize()
        
        try:
            # Prepare audio
            audio = speech.RecognitionAudio(content=audio_content)
            
            # Determine language codes
            if language_hint and language_hint in self.language_codes:
                primary_language = self.language_codes[language_hint]
                alternative_languages = [
                    lc for lc in self.default_languages 
                    if lc != primary_language
                ]
            else:
                primary_language = "ur-PK"  # Default to Urdu
                alternative_languages = ["en-US", "pa-IN"]
            
            # Configure recognition
            config = speech.RecognitionConfig(
                encoding=getattr(speech.RecognitionConfig.AudioEncoding, encoding),
                sample_rate_hertz=sample_rate,
                language_code=primary_language,
                alternative_language_codes=alternative_languages,
                enable_automatic_punctuation=True,
                model="default",
            )
            
            # Perform recognition
            response = self.client.recognize(config=config, audio=audio)
            
            # Extract best result
            if response.results:
                result = response.results[0]
                if result.alternatives:
                    best = result.alternatives[0]
                    detected_lang = result.language_code if hasattr(result, 'language_code') else primary_language
                    
                    self.logger.info("Transcription successful",
                                   language=detected_lang,
                                   confidence=best.confidence)
                    
                    return best.transcript, detected_lang, best.confidence
            
            return None, primary_language, 0.0
            
        except Exception as e:
            self.logger.error("Transcription failed", error=str(e))
            return None, "unknown", 0.0
    
    async def transcribe_stream(
        self,
        audio_generator,
        language_hint: str = None,
        sample_rate: int = 16000
    ):
        """
        Transcribe streaming audio (for real-time)
        
        Args:
            audio_generator: Generator yielding audio chunks
            language_hint: Expected language
            sample_rate: Audio sample rate
            
        Yields:
            Partial transcriptions
        """
        if not self.client:
            await self.initialize()
        
        primary_language = self.language_codes.get(language_hint, "ur-PK")
        
        config = speech.StreamingRecognitionConfig(
            config=speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=sample_rate,
                language_code=primary_language,
                enable_automatic_punctuation=True,
            ),
            interim_results=True,
        )
        
        def request_generator():
            yield speech.StreamingRecognizeRequest(streaming_config=config)
            for chunk in audio_generator:
                yield speech.StreamingRecognizeRequest(audio_content=chunk)
        
        try:
            responses = self.client.streaming_recognize(requests=request_generator())
            
            for response in responses:
                for result in response.results:
                    if result.alternatives:
                        yield {
                            "transcript": result.alternatives[0].transcript,
                            "is_final": result.is_final,
                            "confidence": result.alternatives[0].confidence if result.is_final else 0.0
                        }
                        
        except Exception as e:
            self.logger.error("Streaming transcription failed", error=str(e))
            yield {"error": str(e)}
    
    def get_supported_formats(self) -> dict:
        """Get supported audio formats"""
        return {
            "LINEAR16": "16-bit linear PCM",
            "FLAC": "FLAC audio",
            "MP3": "MP3 audio",
            "OGG_OPUS": "OGG Opus audio",
            "WEBM_OPUS": "WebM Opus audio",
        }
    
    def get_supported_languages(self) -> dict:
        """Get supported languages"""
        return {
            "ur": "Urdu (Pakistan)",
            "pa": "Punjabi",
            "en": "English",
        }


class OfflineSpeechService:
    """
    Fallback speech service for offline/degraded mode
    
    Uses basic pattern matching for common phrases
    (Limited functionality compared to full service)
    """
    
    def __init__(self):
        self.logger = logger.bind(service="offline_speech")
        
        # Common voice commands/phrases
        self.common_phrases = {
            # These would be pre-recorded patterns
            "emergency": ["emergency", "ایمرجنسی"],
            "help": ["help", "مدد", "madad"],
            "doctor": ["doctor", "ڈاکٹر", "daktar"],
        }
    
    async def transcribe_audio(
        self,
        audio_content: bytes,
        language_hint: str = None
    ) -> Tuple[Optional[str], str, float]:
        """
        Offline transcription (very limited)
        
        Returns placeholder indicating offline mode
        """
        self.logger.warning("Using offline speech service - limited functionality")
        
        return (
            "[Voice input unavailable in offline mode. Please type your symptoms.]",
            language_hint or "en",
            0.0
        )

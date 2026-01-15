"""
Voice Input API Endpoints
Handles voice/audio input for Urdu, Punjabi, and English
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
import structlog
import base64

from app.services.speech_service import SpeechService, OfflineSpeechService
from app.agents.orchestrator import AgentOrchestrator
from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

router = APIRouter()

# Initialize speech service
speech_service: Optional[SpeechService] = None
offline_speech_service = OfflineSpeechService()


class VoiceTranscriptionResponse(BaseModel):
    """Response for voice transcription"""
    success: bool
    transcript: Optional[str]
    detected_language: str
    confidence: float
    mode: str  # "online" or "offline"


class VoiceHealthQueryRequest(BaseModel):
    """Request with base64 audio for health query"""
    audio_base64: str
    audio_format: str = "LINEAR16"
    sample_rate: int = 16000
    language_hint: Optional[str] = None


class VoiceHealthQueryResponse(BaseModel):
    """Combined voice transcription + health analysis response"""
    transcription: VoiceTranscriptionResponse
    health_analysis: Optional[dict] = None


async def get_speech_service():
    """Get speech service instance"""
    global speech_service
    if speech_service is None:
        speech_service = SpeechService()
        try:
            await speech_service.initialize()
        except Exception as e:
            logger.warning("Speech service unavailable, using offline mode", error=str(e))
            return offline_speech_service
    return speech_service


async def get_orchestrator():
    """Get agent orchestrator"""
    from app.main import orchestrator
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="System initializing")
    return orchestrator


@router.post("/transcribe", response_model=VoiceTranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language_hint: Optional[str] = Form(default=None),
    speech: SpeechService = Depends(get_speech_service)
):
    """
    Transcribe voice audio to text
    
    Supports:
    - Urdu (ur)
    - Punjabi (pa)
    - English (en)
    
    Audio formats: WAV, FLAC, MP3, OGG
    """
    logger.info("Voice transcription request",
               filename=file.filename,
               content_type=file.content_type,
               language_hint=language_hint)
    
    try:
        # Read audio content
        audio_content = await file.read()
        
        if len(audio_content) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")
        
        # Determine audio format
        encoding = "LINEAR16"  # Default
        if file.content_type:
            if "flac" in file.content_type:
                encoding = "FLAC"
            elif "mp3" in file.content_type or "mpeg" in file.content_type:
                encoding = "MP3"
            elif "ogg" in file.content_type:
                encoding = "OGG_OPUS"
        
        # Transcribe
        transcript, detected_lang, confidence = await speech.transcribe_audio(
            audio_content=audio_content,
            language_hint=language_hint,
            encoding=encoding
        )
        
        is_offline = isinstance(speech, OfflineSpeechService)
        
        return VoiceTranscriptionResponse(
            success=transcript is not None,
            transcript=transcript,
            detected_language=detected_lang,
            confidence=confidence,
            mode="offline" if is_offline else "online"
        )
        
    except Exception as e:
        logger.error("Transcription failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/transcribe-base64", response_model=VoiceTranscriptionResponse)
async def transcribe_audio_base64(
    request: VoiceHealthQueryRequest,
    speech: SpeechService = Depends(get_speech_service)
):
    """
    Transcribe base64-encoded audio
    
    Useful for mobile apps that encode audio as base64
    """
    try:
        # Decode base64 audio
        audio_content = base64.b64decode(request.audio_base64)
        
        # Transcribe
        transcript, detected_lang, confidence = await speech.transcribe_audio(
            audio_content=audio_content,
            language_hint=request.language_hint,
            sample_rate=request.sample_rate,
            encoding=request.audio_format
        )
        
        is_offline = isinstance(speech, OfflineSpeechService)
        
        return VoiceTranscriptionResponse(
            success=transcript is not None,
            transcript=transcript,
            detected_language=detected_lang,
            confidence=confidence,
            mode="offline" if is_offline else "online"
        )
        
    except Exception as e:
        logger.error("Base64 transcription failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=VoiceHealthQueryResponse)
async def voice_health_analysis(
    file: UploadFile = File(...),
    language_hint: Optional[str] = Form(default=None),
    speech: SpeechService = Depends(get_speech_service),
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """
    Combined voice transcription + health analysis
    
    1. Transcribes voice input
    2. Analyzes health query
    3. Returns both transcription and analysis results
    
    Perfect for voice-first health consultations
    """
    logger.info("Voice health analysis request",
               filename=file.filename,
               language_hint=language_hint)
    
    try:
        # Step 1: Transcribe audio
        audio_content = await file.read()
        
        transcript, detected_lang, confidence = await speech.transcribe_audio(
            audio_content=audio_content,
            language_hint=language_hint
        )
        
        is_offline = isinstance(speech, OfflineSpeechService)
        
        transcription_result = VoiceTranscriptionResponse(
            success=transcript is not None,
            transcript=transcript,
            detected_language=detected_lang,
            confidence=confidence,
            mode="offline" if is_offline else "online"
        )
        
        # Step 2: If transcription successful, analyze health query
        health_result = None
        if transcript:
            health_result = await orchestrator.process_health_query(
                user_input=transcript,
                user_language=detected_lang.split("-")[0] if "-" in detected_lang else detected_lang,
                include_voice=True
            )
        
        return VoiceHealthQueryResponse(
            transcription=transcription_result,
            health_analysis=health_result
        )
        
    except Exception as e:
        logger.error("Voice health analysis failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/supported-languages")
async def get_supported_voice_languages():
    """Get list of supported voice input languages"""
    return {
        "languages": [
            {
                "code": "ur",
                "name": "Urdu",
                "native_name": "اردو",
                "region": "Pakistan",
                "speech_code": "ur-PK"
            },
            {
                "code": "pa",
                "name": "Punjabi",
                "native_name": "پنجابی",
                "region": "Punjab",
                "speech_code": "pa-IN"
            },
            {
                "code": "en",
                "name": "English",
                "native_name": "English",
                "region": "International",
                "speech_code": "en-US"
            }
        ],
        "tips": {
            "en": "Speak clearly and at normal pace for best results",
            "ur": "واضح اور عام رفتار سے بولیں",
            "roman_urdu": "Wazeh aur aam raftar se bolein"
        }
    }


@router.get("/audio-formats")
async def get_supported_audio_formats():
    """Get supported audio formats"""
    return {
        "formats": [
            {"name": "LINEAR16", "extension": ".wav", "description": "16-bit PCM WAV"},
            {"name": "FLAC", "extension": ".flac", "description": "FLAC lossless"},
            {"name": "MP3", "extension": ".mp3", "description": "MP3 audio"},
            {"name": "OGG_OPUS", "extension": ".ogg", "description": "OGG Opus"},
            {"name": "WEBM_OPUS", "extension": ".webm", "description": "WebM Opus"}
        ],
        "recommended": "LINEAR16",
        "sample_rates": [8000, 16000, 44100, 48000],
        "recommended_sample_rate": 16000
    }

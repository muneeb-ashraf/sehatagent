"""
Language Service
Handles language detection, translation, and multilingual processing
"""

from typing import Optional, Dict, List
import re
import structlog
from langdetect import detect, DetectorFactory
from deep_translator import GoogleTranslator

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# Set seed for consistent language detection
DetectorFactory.seed = 0


class LanguageService:
    """
    Service for handling multilingual text processing
    
    Features:
    - Language detection (English, Urdu, Roman Urdu)
    - Translation to/from English
    - Roman Urdu to Urdu script conversion
    - Code-switching handling (mixed language)
    """
    
    def __init__(self):
        self.logger = logger.bind(service="language")
        self.supported_languages = settings.SUPPORTED_LANGUAGES
        
        # Common Roman Urdu to Urdu mappings
        self.roman_to_urdu = {
            # Common words
            "bukhar": "بخار",
            "sir": "سر",
            "dard": "درد",
            "pet": "پیٹ",
            "pait": "پیٹ",
            "khansi": "کھانسی",
            "zukam": "زکام",
            "dast": "دست",
            "ulti": "الٹی",
            "kamzori": "کمزوری",
            "thakan": "تھکاوٹ",
            "neend": "نیند",
            "bhook": "بھوک",
            "pyas": "پیاس",
            "doctor": "ڈاکٹر",
            "dawai": "دوائی",
            "hospital": "ہسپتال",
            "sehat": "صحت",
            "bimari": "بیماری",
            "ilaj": "علاج",
            "paani": "پانی",
            "khana": "کھانا",
            "aaram": "آرام",
            
            # Body parts
            "sar": "سر",
            "aankh": "آنکھ",
            "naak": "ناک",
            "munh": "منہ",
            "gala": "گلا",
            "kamar": "کمر",
            "hath": "ہاتھ",
            "pair": "پیر",
            "jism": "جسم",
            
            # Common phrases
            "kya": "کیا",
            "hai": "ہے",
            "hain": "ہیں",
            "mujhe": "مجھے",
            "mera": "میرا",
            "meri": "میری",
            "bohat": "بہت",
            "bahut": "بہت",
            "zyada": "زیادہ",
            "kam": "کم",
            "din": "دن",
            "raat": "رات",
            
            # Symptoms
            "chakkar": "چکر",
            "behoshi": "بے ہوشی",
            "sujan": "سوجن",
            "khujli": "کھجلی",
            "jalan": "جلن",
        }
        
        # Urdu script character ranges
        self.urdu_pattern = re.compile('[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]')
        
        # Roman Urdu patterns
        self.roman_urdu_patterns = [
            r'\b(mujhe|mera|meri|hai|hain|kya|aur|ya|se|ko|mein|ka|ki|ke)\b',
            r'\b(bukhar|dard|pet|sir|aankh|khansi|zukam|dast)\b',
            r'\b(bohat|bahut|zyada|thora|kuch|sab)\b',
        ]
    
    def detect_language(self, text: str) -> str:
        """
        Detect the language of input text
        
        Returns:
            'en' for English
            'ur' for Urdu script
            'roman_urdu' for Roman Urdu
            'pa' for Punjabi
        """
        if not text or not text.strip():
            return "en"
        
        text = text.strip()
        
        # Check for Urdu script
        urdu_chars = len(self.urdu_pattern.findall(text))
        total_chars = len(text.replace(" ", ""))
        
        if total_chars > 0 and urdu_chars / total_chars > 0.3:
            return "ur"
        
        # Check for Roman Urdu patterns
        text_lower = text.lower()
        roman_urdu_score = 0
        
        for pattern in self.roman_urdu_patterns:
            matches = re.findall(pattern, text_lower)
            roman_urdu_score += len(matches)
        
        # If many Roman Urdu words found
        word_count = len(text.split())
        if word_count > 0 and roman_urdu_score / word_count > 0.3:
            return "roman_urdu"
        
        # Try langdetect for other cases
        try:
            detected = detect(text)
            if detected == "ur":
                return "ur"
            elif detected == "pa":
                return "pa"
        except:
            pass
        
        return "en"
    
    async def translate_to_english(self, text: str, source_lang: str = None) -> str:
        """
        Translate text to English
        
        Args:
            text: Input text
            source_lang: Source language (auto-detect if None)
            
        Returns:
            English translation
        """
        if not text:
            return text
        
        if source_lang is None:
            source_lang = self.detect_language(text)
        
        if source_lang == "en":
            return text
        
        try:
            if source_lang == "roman_urdu":
                # First convert Roman Urdu to Urdu script, then translate
                urdu_text = self._roman_to_urdu_script(text)
                source_lang = "ur"
                text = urdu_text
            
            # Use Google Translator
            translator = GoogleTranslator(source=source_lang, target='en')
            translated = translator.translate(text)
            
            return translated if translated else text
            
        except Exception as e:
            self.logger.warning("Translation failed", error=str(e))
            return text
    
    async def translate_from_english(
        self,
        text: str,
        target_lang: str
    ) -> str:
        """
        Translate English text to target language
        
        Args:
            text: English text
            target_lang: Target language code
            
        Returns:
            Translated text
        """
        if not text or target_lang == "en":
            return text
        
        try:
            if target_lang == "roman_urdu":
                # Translate to Urdu first, then we'd need to romanize
                target_lang = "ur"
            
            translator = GoogleTranslator(source='en', target=target_lang)
            translated = translator.translate(text)
            
            return translated if translated else text
            
        except Exception as e:
            self.logger.warning("Translation failed", error=str(e))
            return text
    
    def _roman_to_urdu_script(self, text: str) -> str:
        """Convert Roman Urdu to Urdu script"""
        words = text.lower().split()
        converted = []
        
        for word in words:
            # Remove punctuation for matching
            clean_word = re.sub(r'[^\w]', '', word)
            
            if clean_word in self.roman_to_urdu:
                converted.append(self.roman_to_urdu[clean_word])
            else:
                converted.append(word)
        
        return " ".join(converted)
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text for processing
        
        - Remove extra whitespace
        - Standardize punctuation
        - Handle common variations
        """
        if not text:
            return text
        
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Standardize common variations
        replacements = {
            "ہیں": "ہے",
            "nahi": "nahi",
            "nahin": "nahi",
            "nhi": "nahi",
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def get_response_language(
        self,
        detected_lang: str,
        user_preference: str = None
    ) -> str:
        """
        Determine the best response language
        
        Args:
            detected_lang: Detected input language
            user_preference: User's language preference
            
        Returns:
            Language code for response
        """
        if user_preference and user_preference in self.supported_languages:
            return user_preference
        
        return detected_lang if detected_lang in self.supported_languages else "en"
    
    def format_for_voice(self, text: str, language: str) -> str:
        """
        Format text for text-to-speech output
        
        - Expand abbreviations
        - Add appropriate pauses
        - Simplify complex sentences
        """
        if not text:
            return text
        
        # Expand common abbreviations
        abbreviations = {
            "ORS": "oral rehydration solution",
            "BP": "blood pressure",
            "TB": "tuberculosis",
            "°F": " degrees fahrenheit",
            "°C": " degrees celsius",
        }
        
        for abbr, full in abbreviations.items():
            text = text.replace(abbr, full)
        
        return text

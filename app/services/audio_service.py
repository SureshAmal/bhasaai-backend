"""
BhashaAI Backend - Audio Service

Handles Text-to-Speech (TTS) generation for Gujarati language learning.
Uses Google Text-to-Speech (gTTS) for the prototype.
"""

import os
import logging
from uuid import uuid4
from gtts import gTTS

# Configure logger
logger = logging.getLogger(__name__)

class AudioService:
    """
    Service for generating and managing audio content.
    """
    
    def __init__(self, storage_path: str = "static/audio"):
        self.storage_path = storage_path
        os.makedirs(self.storage_path, exist_ok=True)
        
    async def generate_pronunciation(self, text: str, lang: str = "gu") -> str:
        """
        Generate TTS audio for the given text.
        
        Args:
            text: Text to convert to speech
            lang: Language code (default: 'gu' for Gujarati)
            
        Returns:
            str: Relative URL/path to the generated audio file
        """
        try:
            # Generate unique filename
            filename = f"{uuid4().hex}.mp3"
            file_path = os.path.join(self.storage_path, filename)
            
            # gTTS generation (Runs synchronously, might block event loop if heavy usage)
            # In validation/production, run in thread/executor
            tts = gTTS(text=text, lang=lang)
            tts.save(file_path)
            
            logger.info(f"Generated audio for '{text}' at {file_path}")
            
            # Return relative path for frontend access
            # Assuming static files are served from /static
            return f"/static/audio/{filename}"
            
        except Exception as e:
            logger.error(f"TTS Generation failed: {e}")
            # Return None or raise? For prototype, returning None lets UI handle it or show error
            return ""

    async def get_audio_url(self, text: str) -> str:
        """Wrapper to get or create audio."""
        # Ideally check if hash(text) exists to avoid regenerating
        return await self.generate_pronunciation(text)

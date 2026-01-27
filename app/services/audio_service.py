import logging
from io import BytesIO
from uuid import uuid4
from gtts import gTTS

from app.core.storage import get_storage_service

# Configure logger
logger = logging.getLogger(__name__)

class AudioService:
    """
    Service for generating and managing audio content.
    """
    
    def __init__(self):
        self.storage = get_storage_service()
        self.folder = "audio"
        
    async def generate_pronunciation(self, text: str, lang: str = "gu") -> str:
        """
        Generate TTS audio and upload to MinIO.
        
        Args:
            text: Text to convert to speech
            lang: Language code (default: 'gu')
            
        Returns:
            str: Public/Presigned URL to the audio file
        """
        try:
            # Generate unique filename
            filename = f"{uuid4().hex}.mp3"
            
            # gTTS generation to memory
            tts = gTTS(text=text, lang=lang)
            mp3_fp = BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            
            # Upload to MinIO
            object_name = self.storage.upload_file(
                file_data=mp3_fp,
                filename=filename,
                content_type="audio/mpeg",
                folder=self.folder
            )
            
            logger.info(f"Generated and uploaded audio for '{text}' as {object_name}")
            
            # Return URL
            # For public/learning content, we might want a permanent URL or long expiry
            return self.storage.get_presigned_url(object_name, expires_hours=24)
            
        except Exception as e:
            logger.error(f"TTS Generation failed: {e}")
            return ""

    async def get_audio_url(self, text: str) -> str:
        """Wrapper to get or create audio."""
        return await self.generate_pronunciation(text)

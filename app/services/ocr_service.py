"""
BhashaAI Backend - OCR Service

Handles extraction of text from images and PDFs using vision capabilities (Mocked for Prototype).
"""

import logging
from typing import List

# In a real implementation, we would use Google Cloud Vision API or Tesseract
# For this prototype, we'll simulate OCR or perform basic extraction if possible.

logger = logging.getLogger(__name__)

class OCRService:
    """Service for Optical Character Recognition."""
    
    @staticmethod
    async def extract_text(file_path: str, mime_type: str = "image/jpeg") -> str:
        """
        Extract text from a file.
        
        Args:
           file_path: Local path or URL to the file
           mime_type: File content type
           
        Returns:
            str: Extracted raw text
        """
        logger.info(f"Extracting text from {file_path}")
        
        try:
            # 1. Handle PDF
            if file_path.lower().endswith('.pdf') or mime_type == 'application/pdf':
                from pypdf import PdfReader
                try:
                    reader = PdfReader(file_path)
                    text = ""
                    for page in reader.pages:
                        extracted = page.extract_text()
                        if extracted:
                            text += extracted + "\n"
                    
                    if text.strip():
                        return text
                except Exception as e:
                    logger.error(f"pypdf extraction failed: {e}")
            
            # 2. Handle Images (Placeholder/LLM Vision would go here)
            # For now, if pypdf fails or it's an image without Tesseract, 
            # we return empty string or specific error to avoid hallucination.
            return "" 

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return ""

    @staticmethod
    def segment_answers(raw_text: str) -> List[dict]:
        """
        Segment raw OCR text into individual answers.
        
        Returns:
            List[dict]: [{"label": "Q1", "text": "..."}]
        """
        # Simple heuristic split (this would be LLM powered in production)
        lines = raw_text.split('\n')
        segments = []
        current_segment = {"label": "Header", "text": ""}
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # Basic detection of Q1, Answer 1, 1., etc.
            if (line.lower().startswith('q') and line[1].isdigit()) or \
               (line.lower().startswith('answer')) or \
               (line[0].isdigit() and line[1] in ['.', ')']):
                
                if current_segment["text"]:
                    segments.append(current_segment)
                
                # split label and content
                parts = line.split(' ', 1)
                label = parts[0]
                content = parts[1] if len(parts) > 1 else ""
                
                current_segment = {"label": label, "text": content}
            else:
                current_segment["text"] += " " + line
                
        if current_segment["text"]:
            segments.append(current_segment)
            
        return segments

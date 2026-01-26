"""
BhashaAI Backend - LLM Service

Multi-provider LLM integration using LangChain.
Supports Cerebras, Google Gemini, OpenAI, and more.
"""

import json
import logging
from enum import Enum
from typing import Any, Optional

from langchain_core.language_models.chat_models import BaseChatModel

from app.config import settings
from app.services.prompts import (
    QUESTION_GENERATION_PROMPT,
    TOPIC_EXTRACTION_PROMPT,
    LANGUAGE_INSTRUCTIONS,
)

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    CEREBRAS = "cerebras"
    GOOGLE = "google"
    OPENAI = "openai"
    GROQ = "groq"


class LLMFactory:
    """
    Factory for creating LLM instances based on provider.
    
    Supports multiple providers with configurable models.
    """
    
    @staticmethod
    def create(
        provider: LLMProvider = None,
        model: str = None,
        temperature: float = 0.7,
        **kwargs,
    ) -> Optional[BaseChatModel]:
        """
        Create an LLM instance for the specified provider.
        
        Args:
            provider: LLM provider (cerebras, google, openai, groq)
            model: Model name (provider-specific)
            temperature: Generation temperature
            **kwargs: Additional provider-specific arguments
        
        Returns:
            BaseChatModel: LangChain chat model instance
        """
        # Default to settings or Cerebras
        provider = provider or LLMProvider(settings.llm_provider)
        
        try:
            if provider == LLMProvider.CEREBRAS:
                return LLMFactory._create_cerebras(model, temperature, **kwargs)
            elif provider == LLMProvider.GOOGLE:
                return LLMFactory._create_google(model, temperature, **kwargs)
            elif provider == LLMProvider.OPENAI:
                return LLMFactory._create_openai(model, temperature, **kwargs)
            elif provider == LLMProvider.GROQ:
                return LLMFactory._create_groq(model, temperature, **kwargs)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
        except ImportError as e:
            logger.error(f"Provider {provider} not installed: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to create LLM for {provider}: {e}")
            raise
    
    @staticmethod
    def _create_cerebras(model: str = None, temperature: float = 0.7, **kwargs) -> BaseChatModel:
        """Create Cerebras LLM instance."""
        from langchain_cerebras import ChatCerebras
        
        api_key = settings.cerebras_api_key
        if not api_key:
            raise ValueError("CEREBRAS_API_KEY not configured")
        
        return ChatCerebras(
            model=model or "llama-3.3-70b",
            api_key=api_key,
            temperature=temperature,
            **kwargs,
        )
    
    @staticmethod
    def _create_google(model: str = None, temperature: float = 0.7, **kwargs) -> BaseChatModel:
        """Create Google Gemini LLM instance."""
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        api_key = settings.google_api_key
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not configured")
        
        return ChatGoogleGenerativeAI(
            model=model or "gemini-2.0-flash",
            google_api_key=api_key,
            temperature=temperature,
            convert_system_message_to_human=True,
            **kwargs,
        )
    
    @staticmethod
    def _create_openai(model: str = None, temperature: float = 0.7, **kwargs) -> BaseChatModel:
        """Create OpenAI LLM instance."""
        from langchain_openai import ChatOpenAI
        
        api_key = settings.openai_api_key
        if not api_key:
            raise ValueError("OPENAI_API_KEY not configured")
        
        return ChatOpenAI(
            model=model or "gpt-4o-mini",
            api_key=api_key,
            temperature=temperature,
            **kwargs,
        )
    
    @staticmethod
    def _create_groq(model: str = None, temperature: float = 0.7, **kwargs) -> BaseChatModel:
        """Create Groq LLM instance."""
        from langchain_groq import ChatGroq
        
        api_key = settings.groq_api_key
        if not api_key:
            raise ValueError("GROQ_API_KEY not configured")
        
        return ChatGroq(
            model=model or "llama-3.3-70b-versatile",
            api_key=api_key,
            temperature=temperature,
            **kwargs,
        )


class LLMService:
    """
    LLM Service for AI-powered question generation.
    
    Uses LangChain with configurable providers (Cerebras, Gemini, OpenAI, Groq).
    """
    
    def __init__(
        self,
        provider: LLMProvider = None,
        model: str = None,
    ):
        """
        Initialize LLM service with specified provider.
        
        Args:
            provider: LLM provider to use
            model: Specific model name
        """
        self.provider = provider or LLMProvider(settings.llm_provider)
        self.model_name = model
        self._llm: Optional[BaseChatModel] = None
    
    @property
    def llm(self) -> BaseChatModel:
        """Lazy-load the LLM instance."""
        if self._llm is None:
            self._llm = LLMFactory.create(
                provider=self.provider,
                model=self.model_name,
            )
        return self._llm
    
    def switch_provider(
        self,
        provider: LLMProvider,
        model: str = None,
    ) -> None:
        """
        Switch to a different LLM provider.
        
        Args:
            provider: New provider
            model: Optional model name
        """
        self.provider = provider
        self.model_name = model
        self._llm = None  # Reset to lazy-load new provider
        logger.info(f"Switched LLM provider to: {provider}")
    
    async def generate_questions(
        self,
        context: str,
        subject: str,
        grade_level: Optional[str] = None,
        language: str = "gu",
        total_marks: int = 100,
        difficulty_distribution: dict[str, int] = None,
        question_types: dict[str, int] = None,
        include_answers: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Generate questions from context using configured LLM.
        
        Args:
            context: Source text/topic for question generation
            subject: Subject name
            grade_level: Target grade level
            language: Output language (gu, en, gu-en)
            total_marks: Total marks for all questions
            difficulty_distribution: % by difficulty (easy, medium, hard)
            question_types: Count by type (mcq, short_answer, etc.)
            include_answers: Whether to generate answers
        
        Returns:
            list[dict]: Generated questions with metadata
        """
        difficulty_distribution = difficulty_distribution or {"easy": 30, "medium": 50, "hard": 20}
        question_types = question_types or {"mcq": 5, "short_answer": 5, "long_answer": 2}
        
        total_questions = sum(question_types.values())
        
        # Build chain
        chain = QUESTION_GENERATION_PROMPT | self.llm
        
        try:
            response = await chain.ainvoke({
                "context": context[:8000],
                "subject": subject,
                "grade_level": grade_level or "Not specified",
                "total_marks": total_marks,
                "total_questions": total_questions,
                "difficulty_distribution": f"Easy {difficulty_distribution.get('easy', 30)}%, Medium {difficulty_distribution.get('medium', 50)}%, Hard {difficulty_distribution.get('hard', 20)}%",
                "question_types": json.dumps(question_types),
                "language_instruction": LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS["gu-en"]),
                "include_answers_instruction": "Include correct answers and explanations." if include_answers else "",
            })
            
            response_text = response.content.strip()
            
            # Clean markdown code blocks
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            questions = json.loads(response_text.strip())
            validated_questions = self._validate_questions(questions, total_marks)
            
            logger.info(f"Generated {len(validated_questions)} questions using {self.provider}")
            return validated_questions
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            raise ValueError("Failed to parse generated questions. Please try again.")
        except Exception as e:
            logger.error(f"Question generation failed: {e}")
            raise
    
    def _validate_questions(
        self,
        questions: list[dict],
        total_marks: int,
    ) -> list[dict[str, Any]]:
        """Validate and normalize generated questions."""
        validated = []
        
        for i, q in enumerate(questions):
            validated_q = {
                "question_number": q.get("question_number", i + 1),
                "question_text": q.get("question_text", ""),
                "question_text_gujarati": q.get("question_text_gujarati"),
                "question_type": q.get("question_type", "short_answer"),
                "marks": float(q.get("marks", 1)),
                "difficulty": q.get("difficulty", "medium"),
                "answer": q.get("answer"),
                "answer_gujarati": q.get("answer_gujarati"),
                "options": q.get("options"),
                "correct_option": q.get("correct_option"),
                "explanation": q.get("explanation"),
                "topic": q.get("topic"),
                "bloom_level": q.get("bloom_level"),
                "keywords": q.get("keywords", []),
            }
            
            valid_types = ["mcq", "short_answer", "long_answer", "true_false", "fill_blank"]
            if validated_q["question_type"] not in valid_types:
                validated_q["question_type"] = "short_answer"
            
            valid_difficulties = ["easy", "medium", "hard"]
            if validated_q["difficulty"] not in valid_difficulties:
                validated_q["difficulty"] = "medium"
            
            validated.append(validated_q)
        
        return validated
    
    async def extract_topics(self, text: str) -> list[str]:
        """Extract key topics from text."""
        chain = TOPIC_EXTRACTION_PROMPT | self.llm
        
        try:
            response = await chain.ainvoke({"text": text[:5000]})
            topics = json.loads(response.content.strip())
            return topics if isinstance(topics, list) else []
        except Exception as e:
            logger.error(f"Topic extraction failed: {e}")
            return []


# Default service instance
_llm_service: Optional[LLMService] = None


def get_llm_service(
    provider: LLMProvider = None,
    model: str = None,
) -> LLMService:
    """
    Get or create an LLM service instance.
    
    Args:
        provider: Optional provider override
        model: Optional model override
    
    Returns:
        LLMService: LLM service instance
    """
    global _llm_service
    
    if provider or model:
        # Return new instance with specific provider/model
        return LLMService(provider=provider, model=model)
    
    if _llm_service is None:
        _llm_service = LLMService()
    
    return _llm_service

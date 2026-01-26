"""
BhashaAI Backend - LLM Prompts

Prompt templates for question generation and AI services.
"""

from langchain_core.prompts import PromptTemplate


# Question Generation Prompt
QUESTION_GENERATION_PROMPT = PromptTemplate(
    input_variables=[
        "context",
        "subject", 
        "grade_level",
        "total_marks",
        "total_questions",
        "difficulty_distribution",
        "question_types",
        "language_instruction",
        "include_answers_instruction",
    ],
    template="""You are an expert educational content creator for {subject} subject.

Generate {total_questions} questions based on the following content:

---
{context}
---

Requirements:
1. Subject: {subject}
2. Grade Level: {grade_level}
3. Total Marks: {total_marks}
4. Difficulty Distribution: {difficulty_distribution}
5. Question Types: {question_types}
{language_instruction}

{include_answers_instruction}

Return ONLY a valid JSON array of questions. Each question must have this structure:
{{
    "question_number": 1,
    "question_text": "Question in English",
    "question_text_gujarati": "Question in Gujarati (if language includes gu)",
    "question_type": "mcq|short_answer|long_answer|true_false|fill_blank",
    "marks": 2,
    "difficulty": "easy|medium|hard",
    "answer": "Correct answer",
    "answer_gujarati": "Answer in Gujarati (if applicable)",
    "options": ["A", "B", "C", "D"] (for MCQ only),
    "correct_option": 0 (0-indexed, for MCQ only),
    "explanation": "Brief explanation",
    "topic": "Related topic/chapter",
    "bloom_level": "remember|understand|apply|analyze|evaluate|create"
}}

Return ONLY the JSON array, no other text."""
)


# Topic Extraction Prompt
TOPIC_EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["text"],
    template="""Extract the main educational topics from this text. Return as JSON array of strings.

Text:
{text}

Return ONLY a JSON array of topic strings, e.g. ["Topic 1", "Topic 2"]"""
)


# Language Instructions
LANGUAGE_INSTRUCTIONS = {
    "gu": "6. Output MUST be in Gujarati (ગુજરાતી). Include English translation in question_text field.",
    "en": "6. Output MUST be in English only.",
    "gu-en": "6. Output should be bilingual - provide both English and Gujarati versions.",
}


# Document Summary Prompt
DOCUMENT_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["text", "language"],
    template="""Summarize the following educational document in {language}.
Focus on key concepts, definitions, and important topics that could be used for question generation.

Document:
{text}

Provide a structured summary with:
1. Main Topics
2. Key Concepts
3. Important Definitions
4. Potential Question Areas"""
)


# Answer Explanation Prompt
ANSWER_EXPLANATION_PROMPT = PromptTemplate(
    input_variables=["question", "answer", "language"],
    template="""Provide a detailed explanation for this answer in {language}.

Question: {question}
Answer: {answer}

Explain why this is the correct answer, step by step. Make it educational and clear."""
)

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


# SOLUTION GENERATION PROMPT
SOLUTION_GENERATION_PROMPT = PromptTemplate(
    input_variables=[
        "question",
        "subject",
        "grade_level",
        "language_instruction",
    ],
    template="""You are an expert tutor for {subject} subject.
Provide a detailed step-by-step solution for the following question.

Question:
{question}

Requirements:
1. Grade Level: {grade_level}
2. Explain each step clearly.
3. Mark the final answer explicitly.
{language_instruction}

Return ONLY valid JSON in this format:
{{
    "steps": [
        {{"step": 1, "description": "Description of step 1", "explanation": "Why do this step (optional)"}},
        {{"step": 2, "description": "Description of step 2"}}
    ],
    "final_answer": "Final answer text",
    "explanation": "Overall summary or concept explanation",
    "difficulty": "easy|medium|hard"
}}

Return ONLY the JSON object."""
)


# SOCRATIC HINT PROMPTS (Levels 0-5)
SOCRATIC_HINT_PROMPT = PromptTemplate(
    input_variables=[
        "question",
        "subject",
        "grade_level",
        "hint_level",
        "history",
        "language_instruction",
    ],
    template="""You are an AI Tutor using the Socratic method to help a student solve a problem.
Do NOT give the answer directly. Guide them progressively.

Question: {question}
Subject: {subject}
Grade: {grade_level}
Current Hint Level: {hint_level} (0=Initial, 1=Concept, 2=Formula, 3=Partial, 4=Step, 5=Near Complete)

Interaction History:
{history}

Goal for this level:
Level 0: Ask clarifying questions or how they plan to start.
Level 1: Hint at the concept/principle involved.
Level 2: Provide the relevant formula or method name.
Level 3: Give partial information or first step.
Level 4: Guide through specific calculation/step.
Level 5: Solution is nearly complete, just need final step.

Instructions:
1. Provide a hint appropriate for Level {hint_level}.
2. Keep it encouraging and short.
3. If they are completely wrong, gently correct them.
{language_instruction}

Return ONLY valid JSON:
{{
    "hint": "The text of your hint/question",
    "level": {hint_level},
    "is_complete": false (true only if they solved it),
    "explanation": "Why this hint (internal use)"
}}"""
)

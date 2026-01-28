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
    "question_text": "Question content (in target language)",
    "question_text_gujarati": "Question in Gujarati (only if bilingual requested)",
    "question_type": "mcq|short_answer|long_answer|true_false|fill_blank",
    "marks": 2,
    "difficulty": "easy|medium|hard",
    "answer": "Correct answer (in target language)",
    "answer_gujarati": "Answer in Gujarati (only if bilingual requested)",
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
DEFAULT_LANGUAGE_INSTRUCTION = "6. Output MUST be in Gujarati (ગુજરાતી) script. All explanations, answers, and feedback must be in Gujarati. English terms can be included in brackets if technical."

LANGUAGE_INSTRUCTIONS = {
    "gu": DEFAULT_LANGUAGE_INSTRUCTION,
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


# ANSWER KEY EXTRACTION PROMPT
ANSWER_KEY_EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["text"],
    template="""You are an expert education assistant.
Extract an Answer Key structure from the following text (which might be from a PDF or image).

Text:
{text}

Extract the questions, their types, marks, and correct answers.
Return ONLY a valid JSON object matching this structure:

{{
    "title": "Suggested Title (e.g. Science Unit Test)",
    "subject": "Inferred Subject",
    "total_marks": 50,
    "answers": [
        {{
            "question_number": 1,
            "type": "mcq|short_answer|long_answer",
            "max_marks": 1.0,
            "correct_answer": "Option letter for MCQ (e.g. 'A')",
            "expected_answer": "Text answer for non-MCQ",
            "keywords": ["key", "words"] (for non-MCQ),
            "partial_marking": true
        }},
        ...
    ]
}}

Rules:
1. Infer types based on content (Options present = MCQ).
2. Infer marks if mentioned (e.g. "[2 marks]"), otherwise default to 1.
3. If no clear correct answer is found, leave 'expected_answer' empty but create the question entry.
4. If NO questions are found in the text, return {{ "answers": [], "error": "No questions found in text" }}.
5. Do NOT hallucinate or invent questions not present in the text.
6. Return ONLY valid JSON.
"""
)


# --- PAPER CHECKING PROMPTS ---

GRADING_PROMPT = PromptTemplate(
    input_variables=["question", "expected_answer", "student_answer", "max_marks", "keywords", "partial_marking", "language_instruction"],
    template="""You are an expert strict teacher grading an exam paper.
    
Question: {question}
Expected Answer: {expected_answer}
Keywords to look for: {keywords}
Max Marks: {max_marks}
Partial Marking Allowed: {partial_marking}

Student's Answer: "{student_answer}"

Evaluate the student's answer based on the expected answer and keywords.
Provide constructive feedback explaining where marks were lost or gained.

{language_instruction}

Return valid JSON:
{{
    "marks_obtained": 3.5,
    "confidence_score": 0.95,
    "feedback": "Correct definition but missed the key term 'photosynthesis'.",
    "improvement_suggestion": "Always mention the process name."
}}
Return ONLY the JSON.
"""
)


# --- TEACHING TOOL PROMPTS ---

# MIND MAP PROMPT
MIND_MAP_PROMPT = PromptTemplate(
    input_variables=["topic", "subject", "grade_level", "language_instruction"],
    template="""Create a hierarchical Mind Map for the topic: {topic}.
Subject: {subject}
Grade: {grade_level}

{language_instruction}

Return a valid JSON object with this recursive structure:
{{
    "id": "root",
    "label": "{topic}",
    "label_gujarati": "Topic in Gujarati",
    "children": [
        {{
            "id": "1",
            "label": "Subtopic A",
            "label_gujarati": "Subtopic in Gujarati",
            "children": [ ... ]
        }},
        ...
    ]
}}

CRITICAL RULES:
1. **DEPTH**: The map MUST have 4+ levels (Root -> Category -> Subconcept -> Detail -> Example).
2. **BREADTH**: 3-6 nodes per branch.
3. **DETAIL**: Leaf nodes must be specific examples or facts, not generic labels.
4. **STRUCTURE**: Ensure the tree is deep and rich.

Return ONLY the JSON."""
)


# LESSON PLAN PROMPT
LESSON_PLAN_PROMPT = PromptTemplate(
    input_variables=["topic", "subject", "grade_level", "duration", "language_instruction"],
    template="""Create a structured Lesson Plan for: {topic}.
Subject: {subject}
Grade: {grade_level}
Duration: {duration}

{language_instruction}

Return valid JSON:
{{
    "topic": "{topic}",
    "duration": "{duration}",
    "objectives": ["Obj 1", "Obj 2"],
    "materials_needed": ["Item 1", "Item 2"],
    "timeline": [
        {{"time": "0-5 min", "activity": "Introduction", "description": "..."}},
        {{"time": "5-15 min", "activity": "Core Concept", "description": "..."}},
        ...
    ],
    "homework": "Assignment description"
}}
Return ONLY the JSON."""
)


# ANALOGY PROMPT
ANALOGY_PROMPT = PromptTemplate(
    input_variables=["topic", "subject", "grade_level", "language_instruction"],
    template="""Explain the concept '{topic}' using a simple, real-world analogy appropriate for Grade {grade_level}.
Subject: {subject}

{language_instruction}

Return valid JSON:
{{
    "concept": "{topic}",
    "analogy_story": "The main story/scenario of the analogy...",
    "comparison_points": [
        {{"concept_part": "Nucleus", "analogy_part": "Brain/Control Center", "explanation": "Both control operations..."}},
        ...
    ],
    "takeaway": "One sentence summary"
}}
Return ONLY the JSON."""
)


# --- DICTIONARY TRANSLATION PROMPT ---

DICTIONARY_TRANSLATION_PROMPT = PromptTemplate(
    input_variables=["word", "direction", "language_instruction"],
    template="""You are an expert English-Gujarati bilingual dictionary.

Given a word, provide a complete dictionary entry with translation, meaning, 
part of speech, and examples.

Word: {word}
Direction: {direction}

{language_instruction}

Return ONLY valid JSON matching this structure:
{{
    "translation": "The translated word in target language",
    "transliteration": "Romanized pronunciation (for Gujarati words)",
    "part_of_speech": "noun|verb|adjective|adverb|pronoun|preposition|conjunction|interjection",
    "meaning": "Definition in English",
    "meaning_gujarati": "Definition in Gujarati (ગુજરાતી)",
    "example_sentence": "Example sentence using the word in source language",
    "example_sentence_translation": "Translation of the example sentence",
    "synonyms": ["synonym1", "synonym2"],
    "antonyms": ["antonym1", "antonym2"],
    "confidence": 0.95
}}

Rules:
1. If English to Gujarati: provide Gujarati translation with transliteration.
2. If Gujarati to English: provide English translation.
3. Include at least 2 synonyms if available.
4. Provide a natural example sentence.
5. Be accurate with part of speech.

Return ONLY the JSON object."""
)


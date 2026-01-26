# BhashaAI Backend Capabilities

The BhashaAI backend is a comprehensive Education AI platform designed to support the Gujarat education ecosystem. It features bilingual support (Gujarati/English), AI-driven content generation, and gamified learning.

## 1. Authentication & User Management
**Security & Role-Based Access Control (RBAC)**
- **Roles**: Admin, Teacher, Student, Parent.
- **Bilingual Profiles**: Stores user details in both English and Gujarati.
- **Institution Management**: SaaS-ready structure for Schools/Colleges/Coaching Classes.
- **Security**: JWT-based authentication with token rotation.

## 2. AI Question Paper Generator
**Automated Assessment Creation**
- **Sources**: Generate papers from uploaded documents (PDF/DOCX), specific topics, or raw text context.
- **Blueprints**: Custom control over:
  - Difficulty distribution (Easy/Medium/Hard).
  - Question types (MCQ, Short Answer, Long Answer, etc.).
  - Bloom's Taxonomy levels.
- **Bilingual Output**: Automatically generates questions in Gujarati and English.
- **Export**: Export papers to PDF/DOCX (structure ready).

## 3. Automated Paper Checking (AI Grading)
**Smart Evaluation System**
- **OCR Integration**: Extracts student handwriting from uploaded answer sheet images.
- **Answer Keys**: Teachers define rubric/expected answers with keywords and partial marking rules.
- **AI Grading**:
  - Semantic comparison of student answer vs expected answer.
  - Generates detailed feedback for improvement.
  - Calculates confidence scores for creating alerts.

## 4. Assignment & Homework Management
**Digital Classroom Workflow**
- **Creation**: Teachers verify/publish Assignments from Question Papers.
- **Submission**: Students submit work via Text, Image, or PDF.
- **Manual Grading**: Interface for teachers to override AI grades or grade manually.
- **Progress Tracking**: Status tracking (Pending -> Submitted -> Graded).

## 5. Smart Teaching Assistant
**AI Tools for Educators**
- **Lesson Planning**: Generates structured lesson plans with objectives, activities, and timelines.
- **Study Materials**: Creates summaries, flashcards, and notes from syllabus topics.
- **Help Sessions**: Interactive AI Chatbot that answers student queries contextually (Socratic method).

## 6. Gujarati Learning Module (Gamified)
**Language Acquisition System**
- **Spaced Repetition (SM-2)**: Scientifically optimized algorithm to schedule vocabulary reviews.
- **Gamification**:
  - **XP & Levels**: Earn points for learning actions.
  - **Streaks**: Daily activity tracking to build habits.
- **Audio Support**: Text-to-Speech (TTS) engine for pronunciation guides.
- **Interactive Exercises**: Support for Flashcards, Word Matching, and Quizzes.

## Technical Highlights
- **Stack**: FastAPI (Python), PostgreSQL + pgvector, Redis, MinIO (Object Storage).
- **Architecture**: Async operations, Modular Service-Repository pattern.
- **Deployment**: Dockerized with Health Checks and easy scaling.
- **Docs**: Full OpenAPI/Swagger documentation available at `/docs`.

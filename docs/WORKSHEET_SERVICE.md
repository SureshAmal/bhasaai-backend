# Worksheet Service Documentation

The Worksheet Service provides functionality for generating, managing, and solving interactive, step-by-step educational worksheets. It leverages LLMs to break down complex problems into guided steps, creating a "mini-game" experience for students.

## Features

- **AI Generation**: Create worksheets from topics or documents with automatic step-by-step breakdown.
- **Interactive Solving**: Users solve problems one step at a time.
- **Immediate Feedback**: Real-time validation of step answers with hints.
- **Gamification**: Scoring system based on correct steps and attempts.
- **Progress Tracking**: Detailed logging of user interactions and progress.

## Data Models

### Worksheet
Represents the container for a set of problems.
- `id`: UUID
- `title`: Worksheet title
- `topic`: Educational topic
- `difficulty`: EASY, MEDIUM, HARD
- `status`: DRAFT, PUBLISHED, ARCHIVED
- `questions`: List of `WorksheetQuestion`

### WorksheetQuestion
A single problem within a worksheet.
- `content`: The main problem text
- `steps`: JSON list of steps `[{ "step_text": "...", "answer_key": "...", "hint": "..." }]`
- `correct_answer`: Final answer

### WorksheetAttempt
A user's session solving a worksheet.
- `status`: IN_PROGRESS, COMPLETED, ABANDONED
- `current_question_index`: Tracks progress
- `current_step_index`: Tracks sub-step progress
- `score`: Current score
- `progress_data`: Log of submitted answers

## API Endpoints

Base URL: `/api/v1/worksheets`

### Generation

#### `POST /generate`
Generate a new worksheet using AI.

**Request Body:**
```json
{
  "topic": "Photosynthesis",
  "subject": "Biology",
  "grade_level": "10",
  "difficulty": "medium",
  "num_questions": 3
}
```

**Response:**
Returns the complete `Worksheet` object with generated questions and steps.

### Management

#### `GET /`
List all worksheets created by the current user.

#### `GET /{id}`
Get details of a specific worksheet.

### Gameplay (Attempts)

#### `POST /{id}/attempts`
Start a new game session (attempt) for a worksheet.

**Response:**
Returns a `WorksheetAttempt` object initialized at the first question/step.

#### `GET /attempts/{attempt_id}`
Get the current state of an attempt.

#### `POST /attempts/{attempt_id}/step`
Submit an answer for the current step.

**Request Body:**
```json
{
  "attempt_id": "uuid...",
  "step_answer": "user answer"
}
```

**Response:**
```json
{
  "is_correct": true,
  "message": "Correct! Moving to next step.",
  "points_awarded": 10,
  "next_step_index": 1,
  "next_question_index": 0,
  "is_complete": false
}
```

## Game Logic

1.  **Step-by-Step Flow**:
    - The user is presented with the `content` of the current question.
    - They must solve the current `step` defined by `current_step_index`.
    - They submit an answer via the `step` endpoint.

2.  **Validation**:
    - The service checks the `step_answer` against the stored `answer_key` (case-insensitive).
    - If correct:
        - Points are awarded (+10).
        - The `current_step_index` increments.
        - If all steps are done, `current_question_index` increments.
    - If incorrect:
        - No points awarded.
        - A hint is returned if available.
        - The user stays on the same step.

3.  **Completion**:
    - When all steps of all questions are completed, the attempt status becomes `COMPLETED`.

# Paper Checking Service API

The Paper Checking Service automates the grading of handwritten student answer sheets using OCR and LLM-based semantic analysis.

## Base URL
`/api/v1/paper-checking`

## Endpoints

### 1. Create Answer Key
Define the rubric and expected answers for a Question Paper.

- **URL**: `/answer-key`
- **Method**: `POST`
- **Auth Required**: Yes (Teacher)

#### Request Body (`AnswerKeyCreate`)
```json
{
  "question_paper_id": "uuid",
  "content": {
    "1": {
      "expected_answer": "Photosynthesis is the process...",
      "max_marks": 2,
      "keywords": ["sunlight", "chlorophyll"],
      "partial_marking": true
    },
    "2": { ... }
  }
}
```

#### Response (`AnswerKeyResponse`)
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "question_paper_id": "uuid",
    "created_at": "..."
  }
}
```

### 2. Upload Submission (Answer Sheet)
Upload a student's answer sheet for processing.

- **URL**: `/upload`
- **Method**: `POST`
- **Auth Required**: Yes
- **Content-Type**: `multipart/form-data`

#### Request Parameters
| Field | Type | Required | Description |
|---|---|---|---|
| `file` | file | Yes | PDF or Image of answer sheet |
| `question_paper_id` | UUID | No | Linked Paper ID |
| `student_name` | string | No | Name of student |

#### Response (`SubmissionResponse`)
```json
{
  "success": true,
  "message": "Submission uploaded and processing started",
  "data": {
    "id": "uuid",
    "status": "pending",
    "input_file_url": "..."
  }
}
```

### 3. Get Graded Result
Get the status and detailed AI feedback for a submission.

- **URL**: `/submission/{submission_id}`
- **Method**: `GET`
- **Auth Required**: Yes

#### Response (`SubmissionResponse`)
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "status": "completed",
    "overall_score": 15.5,
    "max_score": 20.0,
    "answers": [
      {
        "question_number": "1",
        "marks_obtained": 1.5,
        "feedback": "Good answer, but missed keyword 'chlorophyll'.",
        "student_answer_text": "Photosynthesis is..."
      }
    ]
  }
}
```

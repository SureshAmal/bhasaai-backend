# Assignment Service API

The Assignment Service manages homework distribution and student submissions. It includes AI grading (Solve mode) and Socratic Tutoring (Help mode).

## Base URL
`/api/v1/assignments`

## Endpoints

### 1. Create Assignment (Teacher)
Publish a Question Paper as a homework assignment.

- **URL**: `/`
- **Method**: `POST`
- **Auth Required**: Yes (Teacher Role)

#### Request Body (`AssignmentCreate`)
| Field | Type | Required | Description |
|---|---|---|---|
| `title` | string | Yes | Assignment Title |
| `question_paper_id` | UUID | Yes | Linked Question Paper ID |
| `description` | string | No | Instructions for students |
| `due_date` | datetime | No | ISO 8601 encoded deadline |
| `status` | string | No | `published` or `draft` |

#### Response (`AssignmentResponse`)
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "question_text": "Assignment: Science Test 1...",
    "status": "pending",
    "mode": "solve",
    "created_at": "2024-01-01T10:00:00Z"
  }
}
```

### 2. Submit Assignment (Student)
Submit an answer or start a help session for a specific question.

- **URL**: `/submit`
- **Method**: `POST`
- **Auth Required**: Yes (Student)

#### Request Body (`AssignmentSubmit`)
| Field | Type | Required | Description |
|---|---|---|---|
| `question_text` | string | Yes | The question content |
| `mode` | enum | No | `solve` (get answer) or `help` (get hints) |
| `language` | enum | No | `gu` or `en` |
| `subject` | string | No | Context subject |
| `input_type` | enum | No | `text` (default) |

### 3. List Assignments
Get assignments for the current user.

- **URL**: `/`
- **Method**: `GET`
- **Auth Required**: Yes

### 4. Get Assignment Details
Get submission status, AI solution, or help session state.

- **URL**: `/{assignment_id}`
- **Method**: `GET`
- **Auth Required**: Yes

### 5. Get Socratic Hint
Get the next hint in a Help Session.

- **URL**: `/{assignment_id}/hint`
- **Method**: `POST`
- **Auth Required**: Yes

#### Request Body (`HintRequest`)
| Field | Type | Required | Description |
|---|---|---|---|
| `student_response` | string | No | Student's attempt at previous hint |
| `request_next_level` | bool | No | Force move to next hint level |

#### Response (`HintResponse`)
```json
{
  "success": true,
  "data": {
    "hint": "Have you considered Newton's second law?",
    "hint_level": 2,
    "is_completed": false
  }
}
```

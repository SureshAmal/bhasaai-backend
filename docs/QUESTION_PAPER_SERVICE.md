# Question Paper Service API

The Question Paper Service generates assessment papers using AI based on source documents, topics, or custom context. It supports bilingual output (English/Gujarati).

## Base URL
`/api/v1/question-papers`

## Endpoints

### 1. Generate Question Paper
Generate a new question paper using AI.

- **URL**: `/generate`
- **Method**: `POST`
- **Auth Required**: Yes

#### Request Body (`GeneratePaperRequest`)
| Field | Type | Required | Description |
|---|---|---|---|
| `title` | string | Yes | Paper title |
| `subject` | string | Yes | Subject name |
| `language` | enum | No | `gu`, `en`, `gu-en` (default `gu`) |
| `document_id` | UUID | No | Source document ID (conditional) |
| `topic` | string | No | Topic string (conditional) |
| `total_marks` | int | No | Total marks (default 100) |
| `question_types` | object | No | Count of question types (e.g., `{"mcq": 10, "short_answer": 5}`) |
| `difficulty_distribution` | object | No | % split (`{"easy": 30, "medium": 50, "hard": 20}`) |

#### Response (`GeneratePaperResponse`)
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "Science Test",
    "status": "completed",
    "questions": [
      {
        "question_number": 1,
        "question_text": "Photosynthesis definition?",
        "question_type": "short_answer",
        "marks": 2,
        "answer": "..."
      }
    ]
  }
}
```

### 2. List Question Papers
Get all generated papers.

- **URL**: `/`
- **Method**: `GET`
- **Auth Required**: Yes

#### Query Parameters
| Param | Type | Default | Description |
|---|---|---|---|
| `page` | int | 1 | Page number |
| `per_page` | int | 20 | Items per page |

### 3. Get Question Paper
Get specific paper details with all questions.

- **URL**: `/{paper_id}`
- **Method**: `GET`
- **Auth Required**: Yes

### 4. Export Question Paper
Download the paper as PDF or Word document.

- **URL**: `/{paper_id}/export`
- **Method**: `POST`
- **Auth Required**: Yes

#### Request Body (`ExportPaperRequest`)
| Field | Type | Required | Description |
|---|---|---|---|
| `format` | enum | Yes | `pdf`, `docx`, `md` |
| `include_answers` | bool | No | Include answer key (default true) |
| `include_header` | bool | No | Include school header (default true) |

#### Response
File download stream.

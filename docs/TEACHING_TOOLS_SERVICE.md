# Teaching Tools Service API

The Teaching Tools Service leverages Generative AI to create educational aids for teachers, including Lesson Plans, Mind Maps, and Analogies. It supports both English and Gujarati.

## Base URL
`/api/v1/teaching-tools`

## Endpoints

### 1. Generate Tool
Generate a new teaching tool.

- **URL**: `/generate`
- **Method**: `POST`
- **Auth Required**: Yes

#### Request Body (`ToolGenerateRequest`)
| Field | Type | Required | Description |
|---|---|---|---|
| `tool_type` | enum | Yes | `mind_map`, `lesson_plan`, `analogy` |
| `topic` | string | Yes | Subject topic |
| `subject` | string | No | Academic subject |
| `grade_level` | string | No | Grade level |
| `language` | enum | No | `gu`, `en`, `gu-en` |
| `additional_instructions` | string | No | Custom prompt context |

#### Response (`TeachingToolResponse`)
The `content` field varies by tool type.

**Example (Lesson Plan):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "tool_type": "lesson_plan",
    "content": {
      "topic": "Photosynthesis",
      "duration": "45 min",
      "objectives": ["Define photosynthesis", ...],
      "timeline": [
        {"time": "0-5 min", "activity": "Introduction", "description": "..."}
      ]
    },
    ...
  }
}
```

**Example (Mind Map):**
```json
{
  "success": true,
  "data": {
    "tool_type": "mind_map",
    "content": {
      "id": "root",
      "label": "Ecosystem",
      "children": [
        {"id": "1", "label": "Biotic Factors", "children": []}
      ]
    },
    ...
  }
}
```

### 2. List Tools
Get all generated tools for the user.

- **URL**: `/`
- **Method**: `GET`
- **Auth Required**: Yes

#### Query Parameters
| Param | Type | Default | Description |
|---|---|---|---|
| `type` | enum | null | Filter by `mind_map`, etc. |
| `page` | int | 1 | Page number |

### 3. Get Tool Details
Get a specific tool.

- **URL**: `/{tool_id}`
- **Method**: `GET`
- **Auth Required**: Yes

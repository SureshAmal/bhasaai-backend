# Documents Service API

The Documents Service handles file uploads (PDF, DOCX, TXT), text extraction, and storage management (MinIO).

## Base URL
`/api/v1/documents`

## Endpoints

### 1. Upload Document
Upload an educational document for question generation.

- **URL**: `/upload`
- **Method**: `POST`
- **Auth Required**: Yes
- **Content-Type**: `multipart/form-data`

#### Request Parameters (Form Data)
| Field | Type | Required | Description |
|---|---|---|---|
| `file` | file | Yes | Max 50MB (PDF, DOCX, TXT) |
| `subject` | string | No | Subject category |
| `grade_level` | string | No | Target grade level |

#### Response (`DocumentUploadResponse`)
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "filename": "chapter1.pdf",
    "file_url": "documents/...",
    "file_type": "pdf",
    "processing_status": "pending",
    "text_content": "Extracted text...",
    "download_url": "https://minio..."
  }
}
```

### 2. List Documents
Get all documents uploaded by the user.

- **URL**: `/`
- **Method**: `GET`
- **Auth Required**: Yes

#### Query Parameters
| Param | Type | Default | Description |
|---|---|---|---|
| `page` | int | 1 | Page number |
| `per_page` | int | 20 | Items per page |

#### Response (`DocumentListResponse`)
```json
{
  "success": true,
  "data": {
    "documents": [ ... ],
    "total": 5,
    "page": 1,
    "pages": 1
  }
}
```

### 3. Get Document
Get document details.

- **URL**: `/{document_id}`
- **Method**: `GET`
- **Auth Required**: Yes

#### Response (`DocumentResponse`)
Returns full document object with `download_url`.

### 4. Delete Document
Soft delete a document.

- **URL**: `/{document_id}`
- **Method**: `DELETE`
- **Auth Required**: Yes

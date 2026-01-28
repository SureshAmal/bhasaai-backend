# BhashaAI Backend

BhashaAI Backend is a fast, asynchronous FastAPI service that powers the education platform. It provides APIs for Question Paper generation (PDF), Flashcards, and Dictionary services using Generative AI (Google Gemini).

## 🏗 Architecture

The backend is structured as a layered monolith with clear separation of concerns.

```mermaid
graph TD
    Client[Frontend / Client] --> |HTTP/JSON| API[FastAPI Router]
    API --> |Pydantic| Schema[Validation Layer]
    Schema --> Service[Service Layer]

    Service --> |SQLAlchemy| DB[(PostgreSQL + pgvector)]
    Service --> |LangChain| AI[Model providers]
    Service --> |ReportLab/FPDF| PDF[PDF Generator]

    subgraph "Infrastructure"
        Redis[Redis Cache]
        MinIO[MinIO Storage]
    end

    Service --> Redis
    Service --> MinIO
```

### Key Technologies

- **Core**: FastAPI, Python 3.12
- **Data**: PostgreSQL (Async), SQLAlchemy 2.0, Alembic
- **AI**: LangChain, Google Gemini
- **Storage**: MinIO (S3 Compatible), Redis
- **Package Manager**: `uv`

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL, Redis
- Google Gemini API Key

### Installation

1. Clone and enter directory:

    ```bash
    cd bhasaai-backend
    ```

2. Install dependencies using `uv`:

    ```bash
    # Install uv if needed: pip install uv
    uv sync
    ```

3. **Environment Setup**:
    Copy `.env.example` to `.env`:

    ```bash
    cp .env.example .env
    ```

    **Required Variables**:

    ```ini
    DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/education_ai
    SECRET_KEY=your_secret_key
    GEMINI_API_KEY=your_gemini_key
    REDIS_URL=redis://localhost:6379/0
    MINIO_ENDPOINT=localhost:9000
    MINIO_ACCESS_KEY=minioadmin
    MINIO_SECRET_KEY=minioadmin
    ```

4. Run Migrations:

    ```bash
    uv run alembic upgrade head
    ```

5. Run Server:

    ```bash
    uv run uvicorn app.main:app --reload
    ```

    Docs: <http://localhost:8000/docs>

## 🐳 Docker Setup

The backend includes a production-ready Dockerfile.

### Build & Run

```bash
docker build -t bhasaai-backend .
docker run -p 8000:8000 --env-file .env bhasaai-backend
```

### Full Stack (Recommended)

Use the root `docker-compose.yml` to spin up Postgres, Redis, MinIO, and Backend together.

## 🧪 Testing

Run the test suite using `pytest`:

```bash
uv run pytest
```

## 📚 API Services

- `/api/v1/auth`: User authentication (JWT)
- `/api/v1/question-papers`: Generate & Download papers
- `/api/v1/flashcards`: Create decks & SRS study
- `/api/v1/dictionary`: English-Gujarati dictionary

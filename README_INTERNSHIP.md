# Resume-Based AI Interview Platform

This project extends the existing multilingual RAG codebase to implement the AI/ML & Backend Intern Assignment. The original RAG modules remain in place; the new interview workflow is added under `backend/app/interviews`, and the React application is under `frontend-react`.

## Assignment workflow implemented

1. Candidate registers/logs in.
2. Candidate uploads a PDF/text resume; the backend extracts text and the candidate can review it.
3. Candidate selects AI/ML Engineer or Backend Engineer.
4. Candidate uploads the assignment's role-specific book PDFs into a role-tagged knowledge base (or uses Shared).
5. Existing Qdrant dense + BM25 hybrid retrieval with RRF retrieves chunks for the selected role.
6. Gemini (default), OpenRouter, or OpenAI generates a resume-aware question using retrieved textbook evidence. Evidence IDs and source chunks are persisted with the question.
7. Candidate submits answers; the backend evaluates against expected points and stores answer/evaluation.
8. The interview contains five questions and produces a structured report with per-answer feedback and average score.

## Architecture

- Frontend: React + Vite (`frontend-react`)
- Backend: FastAPI (`backend/app`)
- Resume/document extraction: existing `backend/app/documents/extractors.py`
- RAG: existing multilingual dense embeddings, BM25 sparse embeddings, Qdrant, RRF (`backend/app/rag`)
- LLM: Gemini/OpenRouter/OpenAI provider adapters (`backend/app/llm/providers.py`)
- Persistence: PostgreSQL + SQLAlchemy

## Setup

### 1. PostgreSQL

Create a PostgreSQL database and user, then copy `.env.example` to `.env` and configure `RAG_DATABASE_URL` and a long random `RAG_JWT_SECRET`.

### 2. Backend

From repository root:

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Windows: copy .env.example .env
python -m backend.app.db.init_db
uvicorn backend.app.main:app --reload
```

Backend API docs: http://localhost:8000/docs

### 3. Configure an LLM provider

Set at least one API key in `.env`:

- `LLM_PROVIDER=gemini` and `GEMINI_API_KEY=...` (recommended default)
- `LLM_PROVIDER=openrouter` and `OPENROUTER_API_KEY=...`
- `LLM_PROVIDER=openai` and `OPENAI_API_KEY=...` (API billing/credits are separate from ChatGPT subscription)

The application tries the selected provider first, then Gemini, OpenRouter, and OpenAI if configured. Provider free tiers, model names and quotas can change; configure a currently available model in the matching `*_MODEL` variable.

### 4. React frontend

```bash
cd frontend-react
npm install
npm run dev
```

Open http://localhost:5173. Optional API URL: create `frontend-react/.env` with `VITE_API_URL=http://localhost:8000`.

## How to use

1. Register and sign in.
2. Upload the relevant textbook PDF in the Role knowledge base panel. The document upload tags it for the currently selected role.
3. Upload and parse the candidate resume; review/edit extracted text.
4. Start the interview.
5. Answer five questions. Each question stores its evidence sources, topic, difficulty and expected answer points.
6. View the report.

Important: the assignment PDF lists recommended books but does not contain their full text. The actual book PDFs must be supplied and ingested before a book-grounded interview can run. Do not upload copyrighted books unless you have the right to use them.

## New API endpoints

- `POST /interviews/resume/parse` — parse a resume file (authenticated)
- `POST /interviews` — create an interview from role + resume text (authenticated)
- `POST /interviews/{session_id}/answers` — submit/evaluate answer and get next question (authenticated)
- `GET /interviews/{session_id}/report` — structured report (authenticated)
- Existing `POST /documents/upload` now accepts `knowledge_role=Shared|AI/ML Engineer|Backend Engineer`.

## Tests and verification

Run `python -m compileall -q backend evaluation tests` for Python syntax validation and `pytest -q` for the existing tests. Run the full backend and frontend locally with PostgreSQL and configured LLM credentials for integration validation. The generated questions intentionally fail closed when no relevant role-matched textbook evidence exists.

## Engineering limitations to validate before submission

- SQLAlchemy `create_all` creates new tables but does not migrate existing columns. This change adds `knowledge_role` to the existing `documents` table; for an existing PostgreSQL database, apply a migration (for example Alembic) adding the nullable/defaulted column before deploying.
- Qdrant role filtering applies to newly indexed documents containing `knowledge_role` payload. Re-upload old documents with the intended role to tag their chunks.
- LLM-generated profile/evaluation JSON is schema-checked at runtime but should be tested with the chosen provider/model and quotas.
- Interview evaluation is an assistive rubric score, not an objective hiring decision.
- Configure production CORS origins, HTTPS, upload limits, retention and privacy controls before public deployment.

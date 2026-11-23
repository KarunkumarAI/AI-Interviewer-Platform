# Resume-Based AI Interview Platform

An AI-powered, role-based technical interview platform built for the **AI/ML & Backend Engineering Intern Assignment**. The application uses a candidate's resume, selected job role, and role-specific textbook content to generate grounded technical interview questions, evaluate answers, and produce a structured interview report.

**Repository:** https://github.com/KarunkumarAI/AI-Interviewer-Platform

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [How It Works](#how-it-works)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Local Setup on Windows](#local-setup-on-windows)
- [Environment Configuration](#environment-configuration)
- [Running the Application](#running-the-application)
- [Using the Application](#using-the-application)
- [API Overview](#api-overview)
- [Data Storage](#data-storage)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Security and Privacy Notes](#security-and-privacy-notes)
- [Limitations and Future Improvements](#limitations-and-future-improvements)

## Overview

The platform simulates a structured technical interview for roles such as:

- AI/ML Engineer
- Backend Engineer

Instead of relying only on predefined questions, it constructs interview context from:

1. The candidate's uploaded resume.
2. The selected target role.
3. Relevant content retrieved from the role-specific knowledge base.

The retrieved textbook passages are supplied to the language model during question generation. The application records evidence associated with generated questions so that the question can be traced back to retrieved knowledge-base content.

The project also retains multilingual RAG assistant functionality from the original codebase, including document-grounded question answering and related assistant features.

## Key Features

### Resume Processing

- Accepts a candidate resume upload through the interview interface.
- Supports PDF and text extraction through the backend document extraction module.
- Extracts resume text for candidate-profile analysis.
- Uses the selected role and resume content to identify skills, technologies, projects, domains, experience summary, and potential role gaps.

### Role-Specific Knowledge Base

- Supports document ingestion for the following knowledge-base categories:
  - `Shared`
  - `AI/ML Engineer`
  - `Backend Engineer`
- Extracts text from supported document formats.
- Splits extracted text into overlapping chunks.
- Creates dense and sparse embeddings.
- Stores vectors and metadata in a local Qdrant collection.
- Filters retrieval by the selected role while also allowing `Shared` knowledge-base content.

**Important:** The assignment lists recommended books, but the repository does not include the full textbook contents. Upload the relevant book/document files through the application before starting a textbook-grounded interview. Only upload material you are permitted to use.

### Hybrid RAG Retrieval

The interview pipeline uses:

- Dense semantic embeddings with FastEmbed.
- Sparse BM25 retrieval.
- Qdrant vector storage.
- Reciprocal Rank Fusion (RRF) to combine retrieval results.
- Role-aware retrieval using the candidate's account and selected role.

The retrieved passages are provided to the question-generation process as supporting evidence.

### Dynamic Interview Generation

- Uses resume profile information and selected role.
- Generates one question at a time.
- Uses retrieved knowledge-base passages as grounding context.
- Records question topic, difficulty, expected answer points, provider, rationale, and selected evidence.
- Generates a five-question interview flow.
- Uses previous answers as context when generating subsequent questions to reduce repetition and probe relevant areas.

### Answer Evaluation and Interview Report

- Accepts candidate answers through the interview interface.
- Evaluates answers against expected answer points.
- Produces a score, strengths, gaps, and feedback.
- Stores submitted answers and evaluation output.
- Provides a structured report with questions, answers, evidence, per-answer evaluation, and average score.

The evaluation is an AI-assisted rubric assessment and should not be treated as an objective hiring decision.

### Authentication and Persistence

- Email-based registration and login.
- Password hashing and token-based authentication.
- User-associated interview sessions and interview records.
- PostgreSQL persistence through SQLAlchemy.

### Additional RAG Assistant Features

The repository also contains the original multilingual RAG assistant modules, including:

- English, Kannada, Hindi, and Telugu language support.
- Document-grounded question answering.
- Dense and sparse retrieval with RRF.
- Self-healing retrieval logic and evidence checks.
- Voice-related endpoints.
- Browser automation endpoints.
- A Streamlit frontend in the `frontend/` directory.

These are additional capabilities in the repository; the assignment's interview UI is the React application in `frontend-react/`.

## How It Works

```mermaid
flowchart TD
    A[Candidate opens React application] --> B[Register or Login]
    B --> C[Upload Resume]
    C --> D[Backend extracts resume text]
    D --> E[Select target role]
    E --> F[Upload role-specific textbook documents]
    F --> G[Text extraction and chunking]
    G --> H[Dense and BM25 embeddings]
    H --> I[(Local Qdrant knowledge base)]
    D --> J[LLM creates candidate profile]
    E --> K[Build role-aware retrieval query]
    J --> K
    I --> L[Hybrid retrieval with RRF]
    K --> L
    L --> M[Relevant evidence chunks]
    M --> N[LLM generates grounded interview question]
    N --> O[Store question and evidence in PostgreSQL]
    O --> P[Candidate submits answer]
    P --> Q[LLM evaluates answer]
    Q --> R[Store answer and evaluation]
    R --> S{Five questions completed?}
    S -->|No| T[Generate next contextual question]
    T --> O
    S -->|Yes| U[Generate structured interview report]
```

## Architecture

| Layer | Implementation | Responsibility |
|---|---|---|
| Frontend | React 18 + Vite | Resume upload, role selection, interview interaction, and report UI |
| Backend | FastAPI | Authentication, API routes, interview lifecycle, document processing, and orchestration |
| Resume/document processing | Python extraction module | Extract text from uploaded documents |
| RAG pipeline | FastEmbed + Qdrant | Chunking, embeddings, hybrid retrieval, role filtering, and evidence retrieval |
| LLM integration | Gemini, OpenRouter, or OpenAI adapters | Resume profile extraction, question generation, and answer evaluation |
| Relational persistence | PostgreSQL + SQLAlchemy | Users, documents, interview sessions, questions, and answers |
| Additional frontend | Streamlit | Original multilingual RAG assistant interface |

### Interview Data Flow

The core interview pipeline follows:

`Resume + Selected Role → Candidate Profile → Retrieval Query → Knowledge Retrieval → Grounded Question → Candidate Answer → Evaluation → Report`

Generated questions store selected evidence passages and related metadata to support traceability.

## Technology Stack

- **Language:** Python
- **Frontend:** React, Vite, JavaScript
- **Backend:** FastAPI, Uvicorn
- **Database:** PostgreSQL, SQLAlchemy
- **Vector database:** Qdrant (local persistent storage)
- **Embeddings:** FastEmbed
- **Sparse retrieval:** BM25
- **Retrieval fusion:** Reciprocal Rank Fusion
- **LLM providers:** Gemini, OpenRouter, OpenAI
- **Document processing:** pypdf, PyMuPDF, python-docx, openpyxl, BeautifulSoup
- **OCR:** Tesseract / pytesseract where applicable
- **Testing:** Pytest

## Project Structure

```text
multilingual-rag-main/
│
├── backend/
│   └── app/
│       ├── auth/              # Registration, login, authentication
│       ├── browser/           # Browser automation endpoints and service
│       ├── conversations/     # Conversation history endpoints
│       ├── core/              # Application configuration and language helpers
│       ├── db/                # SQLAlchemy models, database session, initialization
│       ├── documents/         # File extraction and knowledge-base ingestion
│       ├── interviews/        # Resume parsing, interview generation and evaluation
│       ├── llm/               # LLM provider integration
│       ├── rag/               # Embeddings, Qdrant retrieval and RAG logic
│       ├── security/          # Security middleware
│       ├── voice/             # Voice-related endpoints
│       └── main.py            # FastAPI application entry point
│
├── frontend-react/
│   ├── src/
│   │   ├── main.jsx           # React application
│   │   └── style.css          # Frontend styles
│   ├── index.html
│   └── package.json
│
├── frontend/                  # Original Streamlit assistant frontend
├── evaluation/                # RAG evaluation utilities
├── tests/                     # Automated tests
├── migrations/                # SQL migration scripts
├── screenshots/               # Project screenshots
├── requirements.txt
├── .env.example               # Environment variable template
├── .gitignore
├── README.md
├── README_INTERNSHIP.md
├── DEMO_SCRIPT.md
├── DEPLOYMENT.md
├── start_backend.bat
└── start_frontend.bat
```

## Prerequisites

Install the following before running the application:

1. **Python 3.11**
2. **Node.js and npm** (for the React frontend)
3. **PostgreSQL**
4. **Git**
5. An API key for at least one configured LLM provider:
   - Gemini
   - OpenRouter
   - OpenAI

Optional, depending on the features you use:

- Tesseract OCR for scanned-document OCR.
- A supported browser installation for browser automation.

## Local Setup on Windows

Run the commands from the repository root directory (the directory containing `requirements.txt`).

### 1. Clone the repository

```cmd
git clone https://github.com/KarunkumarAI/AI-Interviewer-Platform.git
cd AI-Interviewer-Platform
```

If the GitHub repository contains the project inside a subdirectory, first open the directory that contains `requirements.txt` and `backend/`.

### 2. Create and activate a Python virtual environment

```cmd
py -3.11 -m venv venv
venv\Scripts\activate
```

### 3. Install Python dependencies

```cmd
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install frontend dependencies

Open a terminal at the repository root and run:

```cmd
cd frontend-react
npm install
cd ..
```

### 5. Create the environment file

```cmd
copy .env.example .env
```

Open `.env` in an editor and configure the database credentials, JWT secret, and at least one LLM provider API key.

See [Environment Configuration](#environment-configuration).

### 6. Create the PostgreSQL database

Create a PostgreSQL database and user, then set the matching connection string in `.env`.

Example connection-string format:

```env
RAG_DATABASE_URL=postgresql+psycopg://YOUR_DB_USER:YOUR_DB_PASSWORD@localhost:5432/YOUR_DB_NAME
```

The database and user shown above are examples/placeholders. Replace them with the values configured in your PostgreSQL installation.

### 7. Initialize database tables

From the repository root, with the virtual environment activated:

```cmd
python -m backend.app.db.init_db
```

This creates tables defined by the current SQLAlchemy models. If you are upgrading an older database schema, review and apply the relevant SQL migration in `migrations/` before running the application.

## Environment Configuration

The application reads configuration from a root-level `.env` file. Use `.env.example` as the template.

| Variable | Purpose |
|---|---|
| `RAG_DATABASE_URL` | PostgreSQL SQLAlchemy connection URL |
| `RAG_JWT_SECRET` | Secret used to sign authentication tokens |
| `RAG_ACCESS_TOKEN_MINUTES` | Authentication token lifetime |
| `LLM_PROVIDER` | Preferred provider: `gemini`, `openrouter`, or `openai` |
| `LLM_FALLBACK_ENABLED` | Fallback configuration flag |
| `GEMINI_API_KEY` | Gemini API key |
| `GEMINI_MODEL` | Gemini model name |
| `OPENROUTER_API_KEY` | OpenRouter API key |
| `OPENROUTER_MODEL` | OpenRouter model name |
| `OPENAI_API_KEY` | OpenAI API key |
| `OPENAI_MODEL` | OpenAI model name |
| `FRONTEND_ORIGIN` | Frontend origin setting |

Configure at least one provider and a model supported by that provider. Provider availability, model names, quotas, and pricing can change.

Example only:

```env
RAG_DATABASE_URL=postgresql+psycopg://YOUR_DB_USER:YOUR_DB_PASSWORD@localhost:5432/YOUR_DB_NAME
RAG_JWT_SECRET=REPLACE_WITH_A_LONG_RANDOM_SECRET

LLM_PROVIDER=gemini
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL=gemini-2.0-flash

OPENROUTER_API_KEY=
OPENAI_API_KEY=
```

Do not commit your real `.env` file or paste API keys into source code, screenshots, issue trackers, or public messages.

## Running the Application

Run the backend and frontend in separate terminals.

### Terminal 1: Start the FastAPI backend

From the repository root:

```cmd
venv\Scripts\activate
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend base URL:

http://localhost:8000

Interactive API documentation:

http://localhost:8000/docs

Health endpoint:

http://localhost:8000/health

### Terminal 2: Start the React frontend

From the repository root:

```cmd
cd frontend-react
npm run dev
```

Open the Vite URL shown in the terminal. The default development URL is:

http://localhost:5173

If the frontend needs a custom backend URL, configure `VITE_API_URL` in a local `frontend-react/.env` file, for example:

```env
VITE_API_URL=http://localhost:8000
```

Keep local environment files out of Git.

## Using the Application

The normal interview workflow is:

1. Open the React application in your browser.
2. Register with an email address and password, then log in.
3. Select the target role: AI/ML Engineer or Backend Engineer.
4. Upload the role-specific textbook or knowledge-base document and select the matching role category. Use `Shared` only for content intended to be available to both roles.
5. Upload the candidate resume.
6. Review the extracted resume text/profile as presented by the application.
7. Start the interview.
8. Read the generated technical question and submit an answer.
9. Continue through the five-question interview.
10. Review the final report, including answers, scores, feedback, and supporting evidence.

If no relevant role-matched or shared textbook content has been indexed for the account, question generation may fail with a message asking for knowledge-base content. Upload and index the relevant source document before starting the interview.

## API Overview

The backend exposes interactive API documentation at `/docs`. The main interview endpoints are:

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/auth/register` | Register a user |
| `POST` | `/auth/login` | Log in and obtain an access token |
| `GET` | `/auth/me` | Get the authenticated user |
| `POST` | `/interviews/resume/parse` | Parse an uploaded resume |
| `POST` | `/interviews` | Create an interview session and generate the first question |
| `POST` | `/interviews/{session_id}/answers` | Submit and evaluate an answer; generate the next question when applicable |
| `GET` | `/interviews/{session_id}/report` | Retrieve the interview report |
| `POST` | `/documents/upload` | Upload and index a knowledge-base document |
| `GET` | `/documents` | List the current user's documents |
| `GET` | `/health` | Check backend health |
| `GET` | `/health/db` | Check database connectivity |

Interview and document endpoints require authentication where indicated by the API documentation. Use the **Authorize** control in Swagger UI to test authenticated endpoints.

## Data Storage

- **PostgreSQL** stores relational application data, including users, documents, interview sessions, questions, and answers.
- **Qdrant local storage** stores dense and sparse knowledge-base vectors and their payload metadata under `data/qdrant/`.
- Uploaded knowledge-base documents are associated with the authenticated user and a knowledge role.

The local Qdrant data directory is runtime data and is excluded from normal Git tracking by `.gitignore`. After cloning the repository, create or populate the knowledge base by uploading the required source documents through the application.

## Testing

Run the existing automated tests from the repository root:

```cmd
venv\Scripts\activate
pytest -q
```

Run Python syntax compilation:

```cmd
python -m compileall -q backend evaluation tests
```

The tests cover selected application areas. Passing unit tests does not replace end-to-end testing with PostgreSQL, a configured LLM provider, an indexed knowledge base, and the React frontend.

### Recommended End-to-End Checks

- Register a new user and log in.
- Upload a readable PDF resume and verify extracted text.
- Upload a role-specific knowledge-base document.
- Confirm that the document is indexed successfully.
- Start an interview for the selected role.
- Confirm that generated questions are relevant to the resume and retrieved source material.
- Submit answers and verify evaluation feedback.
- Complete the interview and inspect the report.
- Restart the backend and verify that relational records persist.
- Confirm that the knowledge base can be queried after restart.

## Troubleshooting

### Backend cannot connect to PostgreSQL

- Confirm that the PostgreSQL service is running.
- Verify the database name, username, password, host, and port in `RAG_DATABASE_URL`.
- Confirm that the database exists and the configured user has permission to access it.

### LLM provider errors

- Confirm that the selected provider's API key is present in `.env`.
- Check that the configured model name is available to your account.
- Check provider quota, billing, and rate limits.
- Restart the backend after changing environment variables.

### No textbook evidence found

- Upload a supported textbook/document file.
- Select the correct knowledge role during upload.
- Confirm the upload/indexing status is successful.
- Start the interview using the same user account that uploaded the document.
- Ensure the document contains extractable text.

### Resume parsing fails

- Use a readable PDF or supported text file.
- Check that the PDF contains selectable text or that OCR is configured for scanned pages.
- Ensure the resume file is within the backend's 8 MB limit.

### React cannot connect to the backend

- Confirm the backend is running at `http://localhost:8000`.
- Check the browser developer console for network or CORS errors.
- If using a custom backend URL, verify `VITE_API_URL` and restart the Vite development server.

### Frontend dependency errors

From `frontend-react/`, run:

```cmd
npm install
npm run dev
```

## Security and Privacy Notes

- Never commit `.env`, API keys, database passwords, access tokens, or private credentials.
- `.env.example` contains placeholders and is intended to be committed.
- Do not commit private candidate resumes, personal information, or confidential interview records.
- Review all files before running `git add .`.
- Configure production CORS, HTTPS, upload limits, access controls, data retention, and privacy requirements before public deployment.
- AI-generated scores and feedback are assistive outputs and should not be used as the sole basis for employment decisions.

## Limitations and Future Improvements

Potential areas for further development include:

- More comprehensive automated integration tests.
- Database schema migration management for evolving deployments.
- More configurable interview length and difficulty progression.
- Stronger evaluation calibration and human-review workflows.
- More detailed retrieval-quality and question-grounding metrics.
- Production deployment configuration, monitoring, and rate limiting.
- Additional role support and knowledge-base management features.


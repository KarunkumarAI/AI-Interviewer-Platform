from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from backend.app.auth.routes import router as auth_router
from backend.app.db.session import engine
from backend.app.llm.routes import router as chatbot_router
from backend.app.conversations.routes import router as conversations_router
from backend.app.documents.routes import router as documents_router
from backend.app.rag.routes import router as rag_router
from backend.app.voice.routes import router as voice_router
from backend.app.browser.routes import router as browser_router
from backend.app.interviews.routes import router as interviews_router
from backend.app.security.middleware import SecurityMiddleware

app = FastAPI(title="Resume-Based AI Interview Platform")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.29.90:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityMiddleware)
app.include_router(auth_router)
app.include_router(chatbot_router)
app.include_router(conversations_router)
app.include_router(documents_router)
app.include_router(rag_router)
app.include_router(voice_router)
app.include_router(browser_router)
app.include_router(interviews_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db")
def database_health() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc

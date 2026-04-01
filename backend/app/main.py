from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import prospects, emails, analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Cold Email Agent API",
    description="AI-powered cold email generation and management system",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prospects.router)
app.include_router(emails.router)
app.include_router(analytics.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "cold-email-agent"}

"""
Atelier — Phase 1 FastAPI application entry point.

Run with:
    uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from backend.api.routes import router
from backend.classifier.model import get_classifier

app = FastAPI(
    title="Atelier",
    description="R&D Creative Agency — AI-powered brand design foundation generator.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.on_event("startup")
async def startup_event() -> None:
    """Pre-warm the classifier so the first request isn't slow."""
    get_classifier()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "atelier-phase-1"}

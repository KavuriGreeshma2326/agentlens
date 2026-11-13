"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, health, runs, tasks

app = FastAPI(
    title="AgentLens API",
    description="Run AI agents on evaluation tasks and diagnose why they fail.",
    version="0.1.0",
)

# --- CORS -------------------------------------------------------------------
# Origins are read from the CORS_ORIGINS env var so the same Docker image
# works in dev (localhost:5173) and production (your real domain) without
# rebuilding.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ----------------------------------------------------------------
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(runs.router)
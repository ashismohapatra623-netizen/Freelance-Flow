"""
Freelancer Manager — FastAPI Application Entry Point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import engine, Base
from routes import clients, projects, tasks, time_entries

# Import all models so Base.metadata knows about them
import models  # noqa: F401

# Create all tables (dev convenience — Alembic for production migrations)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Freelancer Manager API",
    description="A single-user freelancer management tool to track clients, projects, tasks, and billable hours.",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(clients.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(time_entries.router)


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

"""AwaazLedger FastAPI Application Entrypoint."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.db.init_db import init_db

# Router imports
from app.api.health import router as health_router
from app.api.ingest import router as ingest_router
from app.api.disputes import router as disputes_router
from app.api.agent import router as agent_router
from app.api.escalations import router as escalations_router
from app.api.metrics import router as metrics_router
from app.api.webhooks import router as webhooks_router
from app.api.swarm import router as swarm_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    setup_logging()
    logger.info("Initializing AwaazLedger SQLite schema...")
    init_db()
    logger.info("AwaazLedger backend ready!")
    yield
    logger.info("AwaazLedger backend shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Autonomous AI Teammate for Self-Healing UPI Disputes",
    lifespan=lifespan,
)

# Enable CORS for frontend simulator and dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(ingest_router, prefix=settings.API_V1_STR)
app.include_router(disputes_router, prefix=settings.API_V1_STR)
app.include_router(agent_router, prefix=settings.API_V1_STR)
app.include_router(escalations_router, prefix=settings.API_V1_STR)
app.include_router(metrics_router, prefix=settings.API_V1_STR)
app.include_router(webhooks_router, prefix=settings.API_V1_STR)
app.include_router(swarm_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "app": settings.PROJECT_NAME,
        "tagline": "Autonomous AI Teammate for Self-Healing UPI Disputes",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health",
    }

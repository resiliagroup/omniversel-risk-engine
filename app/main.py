"""OMNI Risk Intelligence Engine — FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.v1.router import api_router
from app.db.base import engine, Base
from sqlalchemy import text
import structlog

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("omni.startup", version=settings.APP_VERSION, env=settings.ENV)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis SCHEMA public"))
        await conn.run_sync(Base.metadata.create_all)
        # Idempotent column migrations (IF NOT EXISTS — safe to re-run)
        migrations = [
            "ALTER TABLE risk_assessments ADD COLUMN IF NOT EXISTS bottleneck_score FLOAT",
            "ALTER TABLE risk_assessments ADD COLUMN IF NOT EXISTS hro_alpha FLOAT",
            "ALTER TABLE risk_assessments ADD COLUMN IF NOT EXISTS near_miss_count INTEGER",
            "ALTER TABLE risk_assessments ADD COLUMN IF NOT EXISTS k_matrix JSONB",
        ]
        for sql in migrations:
            await conn.execute(text(sql))
        logger.info("omni.migrations_applied")
    yield
    await engine.dispose()
    logger.info("omni.shutdown")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "OMNI Risk Intelligence Engine — HFER-720 multi-hazard risk scoring, "
        "exposure analysis, and AI-powered recommendations."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION, "engine": "HFER-720"}

@app.get("/")
async def root():
    return {
        "platform": "OMNI Risk Intelligence Engine",
        "version": settings.APP_VERSION,
        "model": "HFER-720",
        "docs": "/docs",
    }

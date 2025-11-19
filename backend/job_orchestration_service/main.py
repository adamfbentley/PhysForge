from fastapi import FastAPI
from contextlib import asynccontextmanager
from .database import engine, Base
from .routers import jobs
from .config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.ENVIRONMENT == "development":
        logger.info("ENVIRONMENT is 'development'. Creating database tables for Job Orchestration Service...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created.")
    else:
        logger.warning(
            f"ENVIRONMENT is '{settings.ENVIRONMENT}'. Skipping automatic database table creation. "
            "Ensure migrations are handled externally (e.g., with Alembic) in production."
        )
    yield
    logger.info("Job Orchestration Service shutting down.")

app = FastAPI(
    title="Job Orchestration Service",
    description="Manages the lifecycle of long-running computational jobs (PINN training, PDE discovery).",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Job Orchestration Service is running!"}

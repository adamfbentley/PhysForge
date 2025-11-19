from fastapi import FastAPI
from contextlib import asynccontextmanager
from .database import engine, Base
from .routers import active_experiment
from .config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.ENVIRONMENT == "development":
        logger.info("ENVIRONMENT is 'development'. Creating database tables for Active Experiment Service...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created.")
    else:
        logger.warning(
            f"ENVIRONMENT is '{settings.ENVIRONMENT}'. Skipping automatic database table creation. "
            "Ensure migrations are handled externally (e.g., with Alembic) in production."
        )
    yield
    logger.info("Active Experiment Service shutting down.")

app = FastAPI(
    title="Active Experiment Service",
    description="Proposes new simulation or experiment parameters to maximize information gain.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(active_experiment.router, prefix="/active-experiment", tags=["Active Experiment Design"])

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Active Experiment Service is running!"}

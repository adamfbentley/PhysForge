from fastapi import FastAPI
from contextlib import asynccontextmanager
from .database import engine, Base
from .routers import datasets
from .config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Conditional database table creation for development/testing
    if settings.ENVIRONMENT == "development":
        logger.info("ENVIRONMENT is 'development'. Creating database tables for Data Management Service...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created.")
    else:
        logger.warning(
            f"ENVIRONMENT is '{settings.ENVIRONMENT}'. Skipping automatic database table creation. "
            "Ensure migrations are handled externally (e.g., with Alembic) in production."
        )
    yield
    logger.info("Data Management Service shutting down.")

app = FastAPI(
    title="Data Management Service",
    description="Ingests, stores, and manages scientific datasets with metadata extraction and object storage.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(datasets.router, prefix="/datasets", tags=["Datasets"])

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Data Management Service is running!"}

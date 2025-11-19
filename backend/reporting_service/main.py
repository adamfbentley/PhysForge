from fastapi import FastAPI
from contextlib import asynccontextmanager
from .database import engine, Base
from .routers import reports
from .config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.ENVIRONMENT == "development":
        logger.info("ENVIRONMENT is 'development'. Creating database tables for Reporting Service...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created.")
    else:
        logger.warning(
            f"ENVIRONMENT is '{settings.ENVIRONMENT}'. Skipping automatic database table creation. "
            "Ensure migrations are handled externally (e.g., with Alembic) in production."
        )
    yield
    logger.info("Reporting Service shutting down.")

app = FastAPI(
    title="Reporting Service",
    description="Generates comprehensive discovery reports and reproducible Jupyter Notebooks.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(reports.router, prefix="/reports", tags=["Reports"])

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Reporting Service is running!"}

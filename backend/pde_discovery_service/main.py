from fastapi import FastAPI
from contextlib import asynccontextmanager
from .database import engine, Base
from .routers import pde_discovery
from .config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.ENVIRONMENT == "development":
        logger.info("ENVIRONMENT is 'development'. Creating database tables for PDE Discovery Service...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created.")
    else:
        logger.warning(
            f"ENVIRONMENT is '{settings.ENVIRONMENT}'. Skipping automatic database table creation. "
            "Ensure migrations are handled externally (e.g., with Alembic) in production."
        )
    yield
    logger.info("PDE Discovery Service shutting down.")

app = FastAPI(
    title="PDE Discovery Service",
    description="Integrates SINDy and PySR for sparse and symbolic regression to discover PDEs.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(pde_discovery.router, prefix="/pde-discovery", tags=["PDE Discovery"])

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "PDE Discovery Service is running!"}

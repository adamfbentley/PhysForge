from fastapi import FastAPI
from contextlib import asynccontextmanager
from .database import engine, Base
from .routers import auth
from .config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # CQ-001: Implement conditional database migration strategy.
    # Base.metadata.create_all is suitable for development/testing, but not production.
    if settings.ENVIRONMENT == "development":
        logger.info("ENVIRONMENT is 'development'. Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created.")
    else:
        logger.warning(
            f"ENVIRONMENT is '{settings.ENVIRONMENT}'. Skipping automatic database table creation. "
            "Ensure migrations are handled externally (e.g., with Alembic) in production."
        )
    yield
    # Clean up or close resources on shutdown (if any)
    logger.info("Auth Service shutting down.")

app = FastAPI(
    title="Auth Service",
    description="Manages user authentication (JWT) and role-based access control (RBAC).",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Auth Service is running!"}

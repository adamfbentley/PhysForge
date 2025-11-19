import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from ..main import app
from ..database import Base, get_db
from ..config import settings
import os

# Override settings for testing
@pytest.fixture(scope="session", autouse=True)
def override_test_settings():
    # Use an in-memory SQLite database for testing
    settings.DATABASE_URL = "sqlite:///./test.db" # Use a file-based SQLite for easier debugging if needed, or :memory:
    settings.SECRET_KEY = "test-secret-key"
    settings.ENVIRONMENT = "testing"
    # Ensure the test.db file is cleaned up if it exists from a previous run
    if os.path.exists("./test.db"):
        os.remove("./test.db")

# Setup test database
@pytest.fixture(scope="function")
def db_session():
    # Create a new in-memory SQLite database for each test function
    engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine) # Create tables for the test database

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine) # Clean up tables after each test
        if os.path.exists("./test.db"):
            os.remove("./test.db")

# Override the get_db dependency to use the test database
@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

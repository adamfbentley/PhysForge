from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL - should match the audit database in docker-compose
SQLALCHEMY_DATABASE_URL = "postgresql://physforge:physforge_password@postgres:5432/physforge_audit"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
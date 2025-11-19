-- Initialize databases for all services
-- This script runs when the PostgreSQL container starts

-- Note: Database 'physforge' is created automatically by POSTGRES_DB env var
-- Connect to the main database
\c physforge;

-- Note: Tables will be created by the services themselves in development mode
-- In production, use Alembic migrations instead
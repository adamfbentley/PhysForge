-- Initialize databases for all services
-- This script runs when the PostgreSQL container starts

-- Create databases for each service
CREATE DATABASE IF NOT EXISTS physforge;

-- Connect to the main database and create schemas if needed
\c physforge;

-- Note: Tables will be created by the services themselves in development mode
-- In production, use Alembic migrations instead
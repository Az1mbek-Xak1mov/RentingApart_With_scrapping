-- Database initialization script for RentingApart
-- This script will be run when the PostgreSQL container starts for the first time

-- Create database if it doesn't exist (this is handled by POSTGRES_DB env var)
-- But we can create additional databases or schemas here if needed

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- The actual table creation will be handled by SQLAlchemy models
-- This file is here for any additional database setup that might be needed
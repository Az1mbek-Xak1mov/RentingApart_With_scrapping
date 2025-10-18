-- Database initialization script for RentingApart
-- This script will be executed when the PostgreSQL container starts for the first time

-- Create database if it doesn't exist (this is handled by POSTGRES_DB environment variable)
-- But we can create additional schemas or extensions here if needed

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- You can add any additional database setup here
-- For example, creating additional schemas, setting up permissions, etc.

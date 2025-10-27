-- SQL script to increase media_url field length for GCS signed URLs
-- Run this directly in your PostgreSQL database if migration doesn't work

-- Increase media_url column length from 500 to 2000 characters
ALTER TABLE sessions ALTER COLUMN media_url TYPE VARCHAR(2000);

-- Verify the change
\d sessions;
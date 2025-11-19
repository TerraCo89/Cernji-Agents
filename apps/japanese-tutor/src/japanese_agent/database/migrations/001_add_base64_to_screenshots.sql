-- Migration: Add base64_data and mime_type columns to screenshots table
-- Date: 2025-11-05
-- Purpose: Store base64 image data in database for reliable retrieval

-- Add base64_data column
ALTER TABLE screenshots ADD COLUMN base64_data TEXT;

-- Add mime_type column with default
ALTER TABLE screenshots ADD COLUMN mime_type TEXT DEFAULT 'image/png';

-- Make file_path optional (SQLite doesn't support modifying column constraints)
-- Instead, we'll just document that file_path is now optional

-- Note: Existing records will have NULL base64_data and default mime_type
-- The application will continue to work by reading from file_path for old records

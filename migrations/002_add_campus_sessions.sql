-- ============================================================================
-- Migration 002: Add Campus and Archive Support to Sessions
-- ============================================================================
-- Purpose: Extends sessions table to support multi-campus deployment
--          (UBC Vancouver and UBC Okanagan) and session archival
-- 
-- Changes:
--   1. Add 'campus' column with CHECK constraint for 'UBC-V' or 'UBC-O'
--   2. Add 'is_archived' column for soft-delete functionality
--   3. Add unique constraint on (campus, program_code, year, session_abbrev)
--   4. Add index for faster campus-based queries
--
-- SAFETY GUARANTEES:
--   - Uses IF NOT EXISTS for idempotent operations
--   - No data deletion or modification
--   - Existing sessions default to 'UBC-V' campus
--   - Backward compatible with existing code until migration complete
-- ============================================================================

BEGIN;

-- ============================================================================
-- STEP 1: Add campus column
-- ============================================================================
-- Default to 'UBC-V' (Vancouver) for existing sessions
-- Valid values: 'UBC-V' (Vancouver) or 'UBC-O' (Okanagan)

DO $$
BEGIN
    -- Add campus column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'sessions' AND column_name = 'campus'
    ) THEN
        ALTER TABLE sessions 
        ADD COLUMN campus VARCHAR(10) DEFAULT 'UBC-V';
        
        RAISE NOTICE 'Added campus column to sessions table';
    ELSE
        RAISE NOTICE 'campus column already exists, skipping';
    END IF;
END $$;

-- Add CHECK constraint for valid campus values
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'sessions' AND constraint_name = 'sessions_campus_check'
    ) THEN
        ALTER TABLE sessions 
        ADD CONSTRAINT sessions_campus_check 
        CHECK (campus IN ('UBC-V', 'UBC-O'));
        
        RAISE NOTICE 'Added CHECK constraint for campus values';
    ELSE
        RAISE NOTICE 'campus CHECK constraint already exists, skipping';
    END IF;
END $$;

-- ============================================================================
-- STEP 2: Add is_archived column for soft-delete
-- ============================================================================
-- Archived sessions are hidden from the UI but data is preserved

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'sessions' AND column_name = 'is_archived'
    ) THEN
        ALTER TABLE sessions 
        ADD COLUMN is_archived BOOLEAN DEFAULT FALSE NOT NULL;
        
        RAISE NOTICE 'Added is_archived column to sessions table';
    ELSE
        RAISE NOTICE 'is_archived column already exists, skipping';
    END IF;
END $$;

-- ============================================================================
-- STEP 3: Add unique constraint on session identification
-- ============================================================================
-- Prevents duplicate sessions for same campus/program/year/term

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'sessions' 
        AND constraint_name = 'sessions_campus_program_year_term_unique'
    ) THEN
        ALTER TABLE sessions 
        ADD CONSTRAINT sessions_campus_program_year_term_unique 
        UNIQUE (campus, program_code, year, session_abbrev);
        
        RAISE NOTICE 'Added unique constraint on (campus, program_code, year, session_abbrev)';
    ELSE
        RAISE NOTICE 'Unique constraint already exists, skipping';
    END IF;
EXCEPTION
    WHEN unique_violation THEN
        RAISE WARNING 'Cannot add unique constraint: duplicate values exist. Please resolve duplicates manually.';
END $$;

-- ============================================================================
-- STEP 4: Add indexes for performance
-- ============================================================================

-- Index for filtering by campus
CREATE INDEX IF NOT EXISTS idx_sessions_campus 
    ON sessions(campus);

-- Index for filtering non-archived sessions
CREATE INDEX IF NOT EXISTS idx_sessions_not_archived 
    ON sessions(is_archived) 
    WHERE is_archived = FALSE;

-- Composite index for common query pattern
CREATE INDEX IF NOT EXISTS idx_sessions_campus_year 
    ON sessions(campus, year DESC);

-- ============================================================================
-- STEP 5: Verification
-- ============================================================================

DO $$
DECLARE
    campus_count INTEGER;
    archived_count INTEGER;
    total_sessions INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_sessions FROM sessions;
    SELECT COUNT(*) INTO campus_count FROM sessions WHERE campus IS NOT NULL;
    SELECT COUNT(*) INTO archived_count FROM sessions WHERE is_archived = TRUE;
    
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Migration 002 Complete - Summary:';
    RAISE NOTICE '  Total sessions: %', total_sessions;
    RAISE NOTICE '  Sessions with campus set: %', campus_count;
    RAISE NOTICE '  Archived sessions: %', archived_count;
    RAISE NOTICE '========================================';
END $$;

COMMIT;

-- ============================================================================
-- ROLLBACK SCRIPT (Run separately if migration needs to be reverted)
-- ============================================================================
-- 
-- BEGIN;
-- 
-- -- Remove indexes
-- DROP INDEX IF EXISTS idx_sessions_campus_year;
-- DROP INDEX IF EXISTS idx_sessions_not_archived;
-- DROP INDEX IF EXISTS idx_sessions_campus;
-- 
-- -- Remove constraints
-- ALTER TABLE sessions DROP CONSTRAINT IF EXISTS sessions_campus_program_year_term_unique;
-- ALTER TABLE sessions DROP CONSTRAINT IF EXISTS sessions_campus_check;
-- 
-- -- Remove columns
-- ALTER TABLE sessions DROP COLUMN IF EXISTS is_archived;
-- ALTER TABLE sessions DROP COLUMN IF EXISTS campus;
-- 
-- COMMIT;
-- 
-- ============================================================================

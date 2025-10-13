-- =====================================================
-- V2.2 CONSTRAINT FIX - Add 'deleted' and 'active' to status
-- Date: 13 oktober 2025, 19:30 CET
-- =====================================================

-- =====================================================
-- 1. DROP OLD CHECK CONSTRAINT
-- =====================================================

ALTER TABLE campaigns 
DROP CONSTRAINT IF EXISTS campaigns_status_check;

-- =====================================================
-- 2. ADD NEW CHECK CONSTRAINT (with 'deleted' and 'active')
-- =====================================================

ALTER TABLE campaigns 
ADD CONSTRAINT campaigns_status_check 
CHECK (status IN (
    'draft',
    'scheduled', 
    'active',      -- NEW: for running campaigns
    'running',     -- LEGACY: keep for backwards compat
    'paused',
    'completed',
    'stopped',
    'deleted'      -- NEW: for soft delete
));

-- =====================================================
-- 3. VERIFICATION
-- =====================================================

-- Verify constraint exists
SELECT 
    conname AS constraint_name,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint 
WHERE conrelid = 'campaigns'::regclass 
  AND conname = 'campaigns_status_check';

-- =====================================================
-- 4. TEST UPDATE (optional - uncomment to test)
-- =====================================================

-- Test setting status to 'deleted'
-- UPDATE campaigns 
-- SET status = 'deleted', deleted_at = NOW()
-- WHERE id = 'd21d4079-a41d-4e36-a923-94831a88cfa1';

-- Test setting status to 'active'
-- UPDATE campaigns 
-- SET status = 'active'
-- WHERE status = 'running';

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================

SELECT 'V2.2 Constraint Fix Complete - deleted and active status now allowed!' AS status;

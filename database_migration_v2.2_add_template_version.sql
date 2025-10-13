-- =====================================================
-- V2.2 ADD template_version TO messages TABLE
-- Date: 13 oktober 2025, 20:55 CET
-- =====================================================

-- =====================================================
-- 1. ADD template_version COLUMN
-- =====================================================

ALTER TABLE messages 
ADD COLUMN IF NOT EXISTS template_version INTEGER DEFAULT 1;

-- =====================================================
-- 2. UPDATE EXISTING MESSAGES (set default)
-- =====================================================

UPDATE messages 
SET template_version = 1 
WHERE template_version IS NULL;

-- =====================================================
-- 3. VERIFICATION
-- =====================================================

-- Check column exists
SELECT column_name, data_type, column_default
FROM information_schema.columns 
WHERE table_name = 'messages' 
  AND column_name = 'template_version';

-- Check sample data
SELECT id, campaign_id, domain_used, template_version, mail_number
FROM messages 
LIMIT 5;

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================

SELECT 'V2.2 template_version column added to messages table!' AS status;

-- =====================================================
-- V2.2 ADD template_version AND attempts TO messages TABLE
-- Date: 13 oktober 2025, 21:05 CET
-- =====================================================

-- =====================================================
-- 1. ADD template_version COLUMN
-- =====================================================

ALTER TABLE messages 
ADD COLUMN IF NOT EXISTS template_version INTEGER DEFAULT 1;

-- =====================================================
-- 2. ADD attempts COLUMN
-- =====================================================

ALTER TABLE messages 
ADD COLUMN IF NOT EXISTS attempts INTEGER DEFAULT 0;

-- =====================================================
-- 3. UPDATE EXISTING MESSAGES (set defaults)
-- =====================================================

UPDATE messages 
SET template_version = 1 
WHERE template_version IS NULL;

UPDATE messages 
SET attempts = 0 
WHERE attempts IS NULL;

-- =====================================================
-- 4. VERIFICATION
-- =====================================================

-- Check columns exist
SELECT column_name, data_type, column_default
FROM information_schema.columns 
WHERE table_name = 'messages' 
  AND column_name IN ('template_version', 'attempts')
ORDER BY column_name;

-- Check sample data
SELECT id, campaign_id, domain_used, template_version, attempts, retry_count, mail_number
FROM messages 
LIMIT 5;

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================

SELECT 'V2.2 template_version and attempts columns added to messages table!' AS status;

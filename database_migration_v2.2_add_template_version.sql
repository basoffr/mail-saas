-- =====================================================
-- V2.2 ADD template_version AND attempts TO messages TABLE
-- Date: 14 oktober 2025, 08:46 CET (UPDATED - Idempotent version)
-- =====================================================

-- =====================================================
-- 1. ADD template_version COLUMN (SAFE - checks if exists first)
-- =====================================================

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'messages' AND column_name = 'template_version'
    ) THEN
        ALTER TABLE messages ADD COLUMN template_version INTEGER DEFAULT 1;
        RAISE NOTICE 'Column template_version added';
    ELSE
        RAISE NOTICE 'Column template_version already exists, skipping';
    END IF;
END $$;

-- =====================================================
-- 2. ADD attempts COLUMN (SAFE - checks if exists first)
-- =====================================================

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'messages' AND column_name = 'attempts'
    ) THEN
        ALTER TABLE messages ADD COLUMN attempts INTEGER DEFAULT 0;
        RAISE NOTICE 'Column attempts added';
    ELSE
        RAISE NOTICE 'Column attempts already exists, skipping';
    END IF;
END $$;

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

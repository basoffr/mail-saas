-- =====================================================
-- V2.2 ADD template_id TO messages TABLE
-- Date: 14 oktober 2025, 09:35 CET
-- =====================================================

-- REASON:
-- Add template_id field for direct template lookup
-- Instead of deriving template from domain → version → mail_number
-- Now we have: template_id = "v2m3" (version 2, mail 3)

-- =====================================================
-- 1. ADD template_id COLUMN (SAFE - checks if exists first)
-- =====================================================

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'messages' AND column_name = 'template_id'
    ) THEN
        ALTER TABLE messages ADD COLUMN template_id VARCHAR DEFAULT 'v1m1';
        RAISE NOTICE 'Column template_id added';
    ELSE
        RAISE NOTICE 'Column template_id already exists, skipping';
    END IF;
END $$;

-- =====================================================
-- 2. CREATE INDEX FOR FAST TEMPLATE LOOKUP
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_messages_template_id ON messages(template_id);

-- =====================================================
-- 3. UPDATE EXISTING MESSAGES (derive from domain + mail_number)
-- =====================================================

-- For existing messages, calculate template_id from domain_used + mail_number
-- domain → version mapping:
--   punthelder-vindbaarheid.nl  → v1
--   punthelder-marketing.nl     → v2
--   punthelder-seo.nl           → v3
--   punthelder-zoekmachine.nl   → v4

UPDATE messages 
SET template_id = CASE
    WHEN domain_used LIKE '%vindbaarheid%' THEN 'v1m' || mail_number
    WHEN domain_used LIKE '%marketing%' THEN 'v2m' || mail_number
    WHEN domain_used LIKE '%seo%' THEN 'v3m' || mail_number
    WHEN domain_used LIKE '%zoekmachine%' THEN 'v4m' || mail_number
    ELSE 'v1m' || mail_number  -- Fallback to v1
END
WHERE template_id IS NULL OR template_id = 'v1m1';  -- Only update default values

-- =====================================================
-- 4. VERIFY TEMPLATE IDS ARE CORRECT
-- =====================================================

SELECT 
    domain_used,
    mail_number,
    template_id,
    COUNT(*) as count
FROM messages
GROUP BY domain_used, mail_number, template_id
ORDER BY domain_used, mail_number
LIMIT 20;

-- Expected output:
-- domain_used              | mail_number | template_id | count
-- ─────────────────────────┼─────────────┼─────────────┼───────
-- punthelder-marketing.nl  | 1           | v2m1        | X
-- punthelder-marketing.nl  | 2           | v2m2        | X
-- punthelder-marketing.nl  | 3           | v2m3        | X
-- punthelder-marketing.nl  | 4           | v2m4        | X

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================

SELECT 'V2.2 template_id column added to messages table! Direct template lookup now available.' AS status;

-- =====================================================
-- V2.2 DROP INCORRECT UNIQUE CONSTRAINT ON messages TABLE
-- Date: 13 oktober 2025, 21:18 CET
-- =====================================================

-- PROBLEM:
-- The messages table has a unique constraint on (campaign_id, lead_id)
-- This prevents creating multiple messages per lead in a campaign.
-- But we NEED 4 messages per lead (mail 1, 2, 3, 4)!

-- SOLUTION:
-- Drop the incorrect unique constraint

-- =====================================================
-- 1. CHECK CURRENT CONSTRAINT
-- =====================================================

SELECT 
    conname AS constraint_name,
    contype AS constraint_type,
    pg_get_constraintdef(c.oid) AS constraint_definition
FROM pg_constraint c
JOIN pg_namespace n ON n.oid = c.connamespace
WHERE conrelid = 'messages'::regclass
  AND conname LIKE '%campaign_id%lead_id%';

-- =====================================================
-- 2. DROP THE INCORRECT UNIQUE CONSTRAINT
-- =====================================================

ALTER TABLE messages 
DROP CONSTRAINT IF EXISTS messages_campaign_id_lead_id_key;

-- =====================================================
-- 3. VERIFY CONSTRAINT IS DROPPED
-- =====================================================

SELECT 
    conname AS constraint_name,
    contype AS constraint_type,
    pg_get_constraintdef(c.oid) AS constraint_definition
FROM pg_constraint c
JOIN pg_namespace n ON n.oid = c.connamespace
WHERE conrelid = 'messages'::regclass
  AND conname LIKE '%campaign_id%lead_id%';

-- Should return 0 rows (constraint is gone)

-- =====================================================
-- 4. VERIFY MESSAGES TABLE CAN HAVE MULTIPLE MESSAGES PER LEAD
-- =====================================================

-- Check existing messages with same campaign_id + lead_id
SELECT 
    campaign_id,
    lead_id,
    COUNT(*) as message_count,
    ARRAY_AGG(mail_number ORDER BY mail_number) as mail_numbers
FROM messages
GROUP BY campaign_id, lead_id
HAVING COUNT(*) > 1
ORDER BY message_count DESC
LIMIT 10;

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================

SELECT 'V2.2 Incorrect unique constraint dropped! Multiple messages per lead now allowed.' AS status;

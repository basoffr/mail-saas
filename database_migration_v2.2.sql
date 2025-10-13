-- =====================================================
-- MAIL DASHBOARD V2.2 DATABASE MIGRATION
-- Campaign Controls + Scheduling View + Stop Lead Flow
-- Date: 13 oktober 2025
-- =====================================================

-- =====================================================
-- 1. CAMPAIGNS TABLE - Add control timestamps
-- =====================================================

-- Add paused_at column (nullable)
ALTER TABLE campaigns 
ADD COLUMN IF NOT EXISTS paused_at TIMESTAMPTZ DEFAULT NULL;

-- Add deleted_at column (nullable, indexed for soft delete queries)
ALTER TABLE campaigns 
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;

-- Create index on deleted_at for efficient filtering
CREATE INDEX IF NOT EXISTS idx_campaigns_deleted_at 
ON campaigns(deleted_at) 
WHERE deleted_at IS NOT NULL;

-- Add comment for documentation
COMMENT ON COLUMN campaigns.paused_at IS 'Timestamp when campaign was paused (V2.2)';
COMMENT ON COLUMN campaigns.deleted_at IS 'Timestamp when campaign was soft deleted (V2.2)';


-- =====================================================
-- 2. MESSAGES TABLE - Add cancel reason tracking
-- =====================================================

-- Add cancel_reason column (nullable)
ALTER TABLE messages 
ADD COLUMN IF NOT EXISTS cancel_reason TEXT DEFAULT NULL;

-- Add comment for documentation
COMMENT ON COLUMN messages.cancel_reason IS 'Reason for message cancellation: campaign_deleted, stopped_bounce, stopped_unsubscribe, stopped_manual (V2.2)';

-- Create index for cancel reason analytics (optional, for performance)
CREATE INDEX IF NOT EXISTS idx_messages_cancel_reason 
ON messages(cancel_reason) 
WHERE cancel_reason IS NOT NULL;


-- =====================================================
-- 3. LEADS TABLE - Add stop criteria flags
-- =====================================================

-- Add is_unsubscribed column (default false, indexed)
ALTER TABLE leads 
ADD COLUMN IF NOT EXISTS is_unsubscribed BOOLEAN DEFAULT FALSE;

-- Add is_hard_bounce column (default false, indexed)
ALTER TABLE leads 
ADD COLUMN IF NOT EXISTS is_hard_bounce BOOLEAN DEFAULT FALSE;

-- Add unsubscribed_at timestamp (nullable)
ALTER TABLE leads 
ADD COLUMN IF NOT EXISTS unsubscribed_at TIMESTAMPTZ DEFAULT NULL;

-- Add bounced_at timestamp (nullable)
ALTER TABLE leads 
ADD COLUMN IF NOT EXISTS bounced_at TIMESTAMPTZ DEFAULT NULL;

-- Create indexes for efficient filtering
CREATE INDEX IF NOT EXISTS idx_leads_is_unsubscribed 
ON leads(is_unsubscribed) 
WHERE is_unsubscribed = TRUE;

CREATE INDEX IF NOT EXISTS idx_leads_is_hard_bounce 
ON leads(is_hard_bounce) 
WHERE is_hard_bounce = TRUE;

-- Add comments for documentation
COMMENT ON COLUMN leads.is_unsubscribed IS 'Global unsubscribe flag - stops all future campaigns (V2.2)';
COMMENT ON COLUMN leads.is_hard_bounce IS 'Global hard bounce flag - stops all future campaigns (V2.2)';
COMMENT ON COLUMN leads.unsubscribed_at IS 'Timestamp when lead unsubscribed (V2.2)';
COMMENT ON COLUMN leads.bounced_at IS 'Timestamp when lead bounced (V2.2)';


-- =====================================================
-- 4. UPDATE CAMPAIGN STATUS ENUM (if needed)
-- =====================================================

-- Note: If you're using an ENUM type for campaign status, you may need to add 'deleted' and 'active'
-- This depends on your existing schema. If status is TEXT, no action needed.

-- Example for ENUM (uncomment if applicable):
-- ALTER TYPE campaign_status ADD VALUE IF NOT EXISTS 'active';
-- ALTER TYPE campaign_status ADD VALUE IF NOT EXISTS 'deleted';


-- =====================================================
-- 5. UPDATE MESSAGE STATUS ENUM (if needed)
-- =====================================================

-- Note: If you're using an ENUM type for message status, you may need to add 'canceled'
-- This depends on your existing schema. If status is TEXT, no action needed.

-- Example for ENUM (uncomment if applicable):
-- ALTER TYPE message_status ADD VALUE IF NOT EXISTS 'canceled';


-- =====================================================
-- 6. VERIFICATION QUERIES
-- =====================================================

-- Verify campaigns table structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'campaigns' 
  AND column_name IN ('paused_at', 'deleted_at')
ORDER BY column_name;

-- Verify messages table structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'messages' 
  AND column_name = 'cancel_reason';

-- Verify leads table structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'leads' 
  AND column_name IN ('is_unsubscribed', 'is_hard_bounce', 'unsubscribed_at', 'bounced_at')
ORDER BY column_name;


-- =====================================================
-- 7. DATA INTEGRITY CHECKS (Optional)
-- =====================================================

-- Check for any campaigns that should be marked as deleted based on status
-- (Run this AFTER migration if you have existing 'deleted' status campaigns)
-- UPDATE campaigns 
-- SET deleted_at = updated_at 
-- WHERE status = 'deleted' 
--   AND deleted_at IS NULL;

-- Check for any campaigns that should be marked as paused
-- UPDATE campaigns 
-- SET paused_at = updated_at 
-- WHERE status = 'paused' 
--   AND paused_at IS NULL;


-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================

-- Summary:
-- ✅ campaigns: +2 columns (paused_at, deleted_at)
-- ✅ messages: +1 column (cancel_reason)
-- ✅ leads: +4 columns (is_unsubscribed, is_hard_bounce, unsubscribed_at, bounced_at)
-- ✅ indexes: +5 indexes for performance
-- ✅ comments: Added for documentation

SELECT 'V2.2 Database Migration Complete!' AS status;

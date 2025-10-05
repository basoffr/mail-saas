-- ============================================================================
-- SUPABASE SECURITY FINAL FIX
-- ============================================================================
-- Fix remaining 9 view errors + 5 function warnings
-- Run this in Supabase SQL Editor
-- ============================================================================

-- ============================================================================
-- PART 1: Fix Views - Add explicit SECURITY INVOKER
-- ============================================================================

-- Drop all views WITH CASCADE to ensure clean slate
DROP VIEW IF EXISTS leads_enriched CASCADE;
DROP VIEW IF EXISTS leads_incomplete CASCADE;
DROP VIEW IF EXISTS campaign_kpis CASCADE;
DROP VIEW IF EXISTS message_timeline CASCADE;
DROP VIEW IF EXISTS campaign_schedule_preview CASCADE;
DROP VIEW IF EXISTS reports_with_links CASCADE;
DROP VIEW IF EXISTS unbound_reports CASCADE;
DROP VIEW IF EXISTS inbox_summary CASCADE;
DROP VIEW IF EXISTS daily_stats CASCADE;

-- Recreate with EXPLICIT SECURITY INVOKER (this is the key!)

CREATE VIEW leads_enriched 
WITH (security_invoker = true) AS
SELECT 
    l.*,
    COALESCE(m.last_sent_at, l.created_at) as last_activity,
    m.total_sent,
    m.total_opened,
    m.total_clicked,
    CASE 
        WHEN m.total_sent > 0 THEN ROUND((m.total_opened::numeric / m.total_sent * 100), 2)
        ELSE 0 
    END as open_rate_pct
FROM leads l
LEFT JOIN LATERAL (
    SELECT 
        MAX(sent_at) as last_sent_at,
        COUNT(*) FILTER (WHERE status = 'sent') as total_sent,
        COUNT(*) FILTER (WHERE status = 'opened') as total_opened,
        COUNT(*) FILTER (WHERE status IN ('opened', 'clicked')) as total_clicked
    FROM messages 
    WHERE lead_id = l.id
) m ON true
WHERE l.deleted_at IS NULL;

CREATE VIEW leads_incomplete
WITH (security_invoker = true) AS
SELECT 
    l.id,
    l.email,
    l.company,
    l.url,
    l.created_at,
    ARRAY_REMOVE(ARRAY[
        CASE WHEN l.company IS NULL OR l.company = '' THEN 'company' END,
        CASE WHEN l.url IS NULL OR l.url = '' THEN 'url' END,
        CASE WHEN l.vars->>'keyword' IS NULL THEN 'keyword' END,
        CASE WHEN l.vars->>'google_rank' IS NULL THEN 'google_rank' END
    ], NULL) as missing_fields
FROM leads l
WHERE l.deleted_at IS NULL
AND (
    l.company IS NULL OR l.company = '' OR
    l.url IS NULL OR l.url = '' OR
    l.vars->>'keyword' IS NULL OR
    l.vars->>'google_rank' IS NULL
);

CREATE VIEW campaign_kpis
WITH (security_invoker = true) AS
SELECT 
    c.id as campaign_id,
    c.name as campaign_name,
    c.status,
    c.created_at,
    jsonb_array_length(COALESCE(ca.lead_ids, '[]'::jsonb)) as total_leads,
    COUNT(DISTINCT CASE WHEN m.status = 'sent' THEN m.lead_id END) as leads_contacted,
    COUNT(m.id) FILTER (WHERE m.status = 'sent') as messages_sent,
    COUNT(m.id) FILTER (WHERE m.status = 'opened') as messages_opened,
    COUNT(m.id) FILTER (WHERE m.status IN ('opened', 'clicked')) as messages_clicked,
    COUNT(m.id) FILTER (WHERE m.status = 'bounced') as messages_bounced,
    ROUND(COALESCE(COUNT(CASE WHEN m.status = 'opened' THEN 1 END)::numeric / NULLIF(COUNT(CASE WHEN m.status = 'sent' THEN 1 END), 0) * 100, 0), 2) as open_rate_pct,
    ROUND(COALESCE(COUNT(CASE WHEN m.status IN ('opened', 'clicked') THEN 1 END)::numeric / NULLIF(COUNT(CASE WHEN m.status = 'sent' THEN 1 END), 0) * 100, 0), 2) as click_rate_pct
FROM campaigns c
LEFT JOIN campaign_audience ca ON c.id = ca.campaign_id
LEFT JOIN messages m ON c.id = m.campaign_id
GROUP BY c.id, c.name, c.status, c.created_at, ca.lead_ids;

CREATE VIEW message_timeline
WITH (security_invoker = true) AS
SELECT 
    m.id,
    m.campaign_id,
    m.lead_id,
    l.email as lead_email,
    l.company as lead_company,
    m.mail_number,
    m.status,
    m.sent_at,
    m.open_at as opened_at,
    m.domain_used,
    c.name as campaign_name,
    m.alias,
    m.from_email
FROM messages m
JOIN leads l ON m.lead_id = l.id
JOIN campaigns c ON m.campaign_id = c.id
ORDER BY m.sent_at DESC NULLS LAST;

CREATE VIEW campaign_schedule_preview
WITH (security_invoker = true) AS
SELECT 
    c.id as campaign_id,
    c.name as campaign_name,
    m.lead_id,
    l.email,
    l.company,
    m.mail_number,
    m.scheduled_at as scheduled_for,
    m.status,
    m.domain_used,
    m.alias
FROM campaigns c
JOIN messages m ON c.id = m.campaign_id
LEFT JOIN leads l ON m.lead_id = l.id
WHERE c.status IN ('draft', 'running', 'paused')
ORDER BY m.scheduled_at NULLS LAST;

CREATE VIEW reports_with_links
WITH (security_invoker = true) AS
SELECT 
    r.id,
    r.filename,
    r.storage_path,
    r.size_bytes,
    r.type,
    r.created_at as uploaded_at,
    rl.lead_id,
    l.email as lead_email,
    l.company as lead_company,
    rl.created_at as linked_at
FROM reports r
LEFT JOIN report_links rl ON r.id = rl.report_id
LEFT JOIN leads l ON rl.lead_id = l.id;

CREATE VIEW unbound_reports
WITH (security_invoker = true) AS
SELECT 
    r.id,
    r.filename,
    r.storage_path,
    r.size_bytes,
    r.type,
    r.created_at as uploaded_at
FROM reports r
WHERE NOT EXISTS (
    SELECT 1 FROM report_links rl WHERE rl.report_id = r.id
);

CREATE VIEW inbox_summary
WITH (security_invoker = true) AS
SELECT 
    ma.id as account_id,
    ma.label as account_email,
    ma.imap_host,
    COUNT(mm.id) as total_messages,
    COUNT(mm.id) FILTER (WHERE mm.linked_message_id IS NOT NULL) as linked_messages,
    COUNT(mm.id) FILTER (WHERE mm.linked_message_id IS NULL) as unlinked_messages,
    MAX(mm.received_at) as last_message_at
FROM mail_accounts ma
LEFT JOIN mail_messages mm ON ma.id = mm.account_id
WHERE ma.active = true
GROUP BY ma.id, ma.label, ma.imap_host;

CREATE VIEW daily_stats
WITH (security_invoker = true) AS
SELECT 
    DATE(m.sent_at) as date,
    COUNT(m.id) FILTER (WHERE m.status = 'sent') as sent_count,
    COUNT(m.id) FILTER (WHERE m.status = 'opened') as opened_count,
    COUNT(m.id) FILTER (WHERE m.status IN ('opened', 'clicked')) as clicked_count,
    COUNT(m.id) FILTER (WHERE m.status = 'bounced') as bounced_count,
    ROUND(COALESCE(COUNT(CASE WHEN m.status = 'opened' THEN 1 END)::numeric / NULLIF(COUNT(CASE WHEN m.status = 'sent' THEN 1 END), 0) * 100, 0), 2) as open_rate_pct,
    COUNT(DISTINCT m.campaign_id) as campaigns_active,
    COUNT(DISTINCT m.lead_id) as unique_leads
FROM messages m
WHERE m.sent_at IS NOT NULL
GROUP BY DATE(m.sent_at)
ORDER BY date DESC;

-- ============================================================================
-- PART 2: Fix remaining 5 functions - Add search_path
-- ============================================================================

-- Fix calculate_campaign_eta
CREATE OR REPLACE FUNCTION calculate_campaign_eta(campaign_id_param VARCHAR)
RETURNS TIMESTAMPTZ
SECURITY DEFINER
SET search_path = public, pg_temp
LANGUAGE plpgsql AS $$
DECLARE
    eta TIMESTAMPTZ;
BEGIN
    SELECT MAX(scheduled_at) INTO eta
    FROM messages
    WHERE campaign_id = campaign_id_param;
    
    RETURN eta;
END;
$$;

-- Fix get_next_send_slot
CREATE OR REPLACE FUNCTION get_next_send_slot(domain_param VARCHAR)
RETURNS TIMESTAMPTZ
SECURITY DEFINER
SET search_path = public, pg_temp
LANGUAGE plpgsql AS $$
DECLARE
    last_sent TIMESTAMPTZ;
    next_slot TIMESTAMPTZ;
BEGIN
    SELECT MAX(sent_at) INTO last_sent
    FROM messages
    WHERE domain_used = domain_param;
    
    IF last_sent IS NULL THEN
        RETURN NOW();
    ELSE
        next_slot := last_sent + INTERVAL '20 minutes';
        IF next_slot < NOW() THEN
            RETURN NOW();
        ELSE
            RETURN next_slot;
        END IF;
    END IF;
END;
$$;

-- Fix link_inbox_message
CREATE OR REPLACE FUNCTION link_inbox_message(
    mail_message_id_param VARCHAR,
    campaign_message_id_param VARCHAR
)
RETURNS BOOLEAN
SECURITY DEFINER
SET search_path = public, pg_temp
LANGUAGE plpgsql AS $$
BEGIN
    UPDATE mail_messages
    SET linked_message_id = campaign_message_id_param
    WHERE id = mail_message_id_param;
    
    RETURN FOUND;
END;
$$;

-- Fix get_campaign_stats (needs DROP first due to return type)
DROP FUNCTION IF EXISTS get_campaign_stats(VARCHAR);

CREATE FUNCTION get_campaign_stats(campaign_id_param VARCHAR)
RETURNS TABLE(
    total_messages BIGINT,
    sent_count BIGINT,
    opened_count BIGINT,
    clicked_count BIGINT,
    bounced_count BIGINT,
    open_rate NUMERIC
)
SECURITY DEFINER
SET search_path = public, pg_temp
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_messages,
        COUNT(*) FILTER (WHERE status = 'sent')::BIGINT as sent_count,
        COUNT(*) FILTER (WHERE status = 'opened')::BIGINT as opened_count,
        COUNT(*) FILTER (WHERE status IN ('opened', 'clicked'))::BIGINT as clicked_count,
        COUNT(*) FILTER (WHERE status = 'bounced')::BIGINT as bounced_count,
        ROUND(COALESCE(
            COUNT(*) FILTER (WHERE status = 'opened')::numeric / 
            NULLIF(COUNT(*) FILTER (WHERE status = 'sent'), 0) * 100, 
            0
        ), 2) as open_rate
    FROM messages
    WHERE campaign_id = campaign_id_param;
END;
$$;

-- Fix get_domain_stats (needs DROP first due to return type)
DROP FUNCTION IF EXISTS get_domain_stats(VARCHAR);

CREATE FUNCTION get_domain_stats(domain_param VARCHAR)
RETURNS TABLE(
    total_sent BIGINT,
    last_sent TIMESTAMPTZ,
    avg_open_rate NUMERIC
)
SECURITY DEFINER
SET search_path = public, pg_temp
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) FILTER (WHERE status = 'sent')::BIGINT as total_sent,
        MAX(sent_at) as last_sent,
        ROUND(COALESCE(
            COUNT(*) FILTER (WHERE status = 'opened')::numeric / 
            NULLIF(COUNT(*) FILTER (WHERE status = 'sent'), 0) * 100, 
            0
        ), 2) as avg_open_rate
    FROM messages
    WHERE domain_used = domain_param;
END;
$$;

-- ============================================================================
-- COMPLETE! All security issues should now be FULLY resolved.
-- ============================================================================

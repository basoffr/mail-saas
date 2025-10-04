-- ============================================================================
-- SUPABASE DATABASE VIEWS - MAIL DASHBOARD
-- ============================================================================
-- Project: Mail SaaS Platform
-- Total Views: 8 denormalized views voor performance
-- Usage: Run AFTER supabase_indexes.sql
-- ============================================================================

-- ============================================================================
-- LEADS MODULE VIEWS
-- ============================================================================

-- View 1: leads_enriched
-- Complete lead view met alle computed fields (has_report, has_image, vars completeness)
CREATE OR REPLACE VIEW leads_enriched AS
SELECT 
    l.*,
    -- Has report indicator
    EXISTS(
        SELECT 1 FROM report_links rl 
        WHERE rl.lead_id = l.id
    ) as has_report,
    
    -- Has image indicator
    (l.image_key IS NOT NULL AND l.image_key != '') as has_image,
    
    -- Vars completeness calculation
    (CASE WHEN l.company IS NOT NULL AND l.company != '' THEN 1 ELSE 0 END +
     CASE WHEN l.url IS NOT NULL AND l.url != '' THEN 1 ELSE 0 END +
     CASE WHEN l.vars ? 'keyword' AND l.vars->>'keyword' != '' THEN 1 ELSE 0 END +
     CASE WHEN l.vars ? 'google_rank' AND l.vars->>'google_rank' != '' THEN 1 ELSE 0 END +
     CASE WHEN l.image_key IS NOT NULL AND l.image_key != '' THEN 1 ELSE 0 END
    ) as vars_filled,
    
    5 as vars_total,
    
    -- Missing variables array
    ARRAY_REMOVE(ARRAY[
        CASE WHEN l.company IS NULL OR l.company = '' THEN 'lead.company' END,
        CASE WHEN l.url IS NULL OR l.url = '' THEN 'lead.url' END,
        CASE WHEN NOT (l.vars ? 'keyword') OR l.vars->>'keyword' = '' THEN 'vars.keyword' END,
        CASE WHEN NOT (l.vars ? 'google_rank') OR l.vars->>'google_rank' = '' THEN 'vars.google_rank' END,
        CASE WHEN l.image_key IS NULL OR l.image_key = '' THEN 'image.cid' END
    ], NULL) as vars_missing,
    
    -- Percentage completeness
    ROUND(
        (CASE WHEN l.company IS NOT NULL AND l.company != '' THEN 1 ELSE 0 END +
         CASE WHEN l.url IS NOT NULL AND l.url != '' THEN 1 ELSE 0 END +
         CASE WHEN l.vars ? 'keyword' AND l.vars->>'keyword' != '' THEN 1 ELSE 0 END +
         CASE WHEN l.vars ? 'google_rank' AND l.vars->>'google_rank' != '' THEN 1 ELSE 0 END +
         CASE WHEN l.image_key IS NOT NULL AND l.image_key != '' THEN 1 ELSE 0 END
        )::float / 5 * 100, 0
    ) as vars_percentage,
    
    -- Is complete flag
    (
        l.company IS NOT NULL AND l.company != '' AND
        l.url IS NOT NULL AND l.url != '' AND
        l.vars ? 'keyword' AND l.vars->>'keyword' != '' AND
        l.vars ? 'google_rank' AND l.vars->>'google_rank' != '' AND
        l.image_key IS NOT NULL AND l.image_key != '' AND
        EXISTS(SELECT 1 FROM report_links rl WHERE rl.lead_id = l.id)
    ) as is_complete
    
FROM leads l
WHERE l.deleted_at IS NULL;

COMMENT ON VIEW leads_enriched IS 'Enriched lead view met computed fields voor UI';

-- View 2: leads_incomplete
-- Alleen incomplete leads voor easy filtering
CREATE OR REPLACE VIEW leads_incomplete AS
SELECT 
    l.*,
    le.vars_missing,
    le.vars_filled,
    le.vars_total,
    le.vars_percentage
FROM leads l
JOIN leads_enriched le ON l.id = le.id
WHERE le.is_complete = FALSE
ORDER BY le.vars_percentage DESC;

COMMENT ON VIEW leads_incomplete IS 'Leads die nog niet compleet zijn (missing data)';

-- ============================================================================
-- CAMPAIGNS MODULE VIEWS
-- ============================================================================

-- View 3: campaign_kpis
-- Real-time campaign KPIs (sent, opened, failed, bounced)
CREATE OR REPLACE VIEW campaign_kpis AS
SELECT 
    c.id,
    c.name,
    c.domain,
    c.status,
    c.start_at,
    
    -- Message counts
    COUNT(m.id) as total_planned,
    COUNT(CASE WHEN m.status = 'sent' THEN 1 END) as total_sent,
    COUNT(CASE WHEN m.status = 'opened' THEN 1 END) as total_opened,
    COUNT(CASE WHEN m.status = 'failed' THEN 1 END) as total_failed,
    COUNT(CASE WHEN m.status = 'bounced' THEN 1 END) as total_bounced,
    COUNT(CASE WHEN m.status = 'queued' THEN 1 END) as total_queued,
    
    -- Rates (in percentage)
    ROUND(
        COALESCE(
            COUNT(CASE WHEN m.status = 'opened' THEN 1 END)::float / 
            NULLIF(COUNT(CASE WHEN m.status = 'sent' THEN 1 END), 0) * 100,
            0
        ), 2
    ) as open_rate_pct,
    
    ROUND(
        COALESCE(
            COUNT(CASE WHEN m.status = 'bounced' THEN 1 END)::float / 
            NULLIF(COUNT(CASE WHEN m.status IN ('sent', 'bounced') THEN 1 END), 0) * 100,
            0
        ), 2
    ) as bounce_rate_pct,
    
    ROUND(
        COALESCE(
            COUNT(CASE WHEN m.status = 'failed' THEN 1 END)::float / 
            NULLIF(COUNT(m.id), 0) * 100,
            0
        ), 2
    ) as failure_rate_pct,
    
    -- Timestamps
    MIN(m.sent_at) as first_sent_at,
    MAX(m.sent_at) as last_sent_at,
    
    c.created_at,
    c.updated_at

FROM campaigns c
LEFT JOIN messages m ON c.id = m.campaign_id
GROUP BY c.id, c.name, c.domain, c.status, c.start_at, c.created_at, c.updated_at;

COMMENT ON VIEW campaign_kpis IS 'Real-time campaign KPIs met all metrics';

-- View 4: message_timeline
-- Daily aggregated message stats per campaign
CREATE OR REPLACE VIEW message_timeline AS
SELECT 
    m.campaign_id,
    DATE(m.sent_at) as date,
    COUNT(*) as sent,
    COUNT(CASE WHEN m.status = 'opened' THEN 1 END) as opened,
    COUNT(CASE WHEN m.status = 'bounced' THEN 1 END) as bounced,
    COUNT(CASE WHEN m.status = 'failed' THEN 1 END) as failed,
    ROUND(
        COALESCE(
            COUNT(CASE WHEN m.status = 'opened' THEN 1 END)::float / 
            NULLIF(COUNT(*), 0) * 100,
            0
        ), 2
    ) as open_rate_pct
FROM messages m
WHERE m.sent_at IS NOT NULL
GROUP BY m.campaign_id, DATE(m.sent_at)
ORDER BY m.campaign_id, DATE(m.sent_at);

COMMENT ON VIEW message_timeline IS 'Daily timeline voor campaign performance grafieken';

-- View 5: campaign_schedule_preview
-- Upcoming scheduled messages (next 7 days)
CREATE OR REPLACE VIEW campaign_schedule_preview AS
SELECT 
    c.id as campaign_id,
    c.name as campaign_name,
    c.domain,
    DATE(m.scheduled_at) as date,
    COUNT(*) as messages_scheduled,
    MIN(m.scheduled_at) as first_message_at,
    MAX(m.scheduled_at) as last_message_at
FROM campaigns c
JOIN messages m ON c.id = m.campaign_id
WHERE m.status = 'queued'
    AND m.scheduled_at BETWEEN NOW() AND NOW() + INTERVAL '7 days'
GROUP BY c.id, c.name, c.domain, DATE(m.scheduled_at)
ORDER BY DATE(m.scheduled_at), c.name;

COMMENT ON VIEW campaign_schedule_preview IS '7-day preview van scheduled messages';

-- ============================================================================
-- REPORTS MODULE VIEWS
-- ============================================================================

-- View 6: reports_with_links
-- Reports met bound kind (lead/campaign/unbound)
CREATE OR REPLACE VIEW reports_with_links AS
SELECT 
    r.id,
    r.filename,
    r.type,
    r.size_bytes,
    r.created_at,
    r.uploaded_by,
    
    -- Binding info
    CASE 
        WHEN rl.lead_id IS NOT NULL THEN 'lead'
        WHEN rl.campaign_id IS NOT NULL THEN 'campaign'
        ELSE NULL
    END as bound_kind,
    
    COALESCE(rl.lead_id, rl.campaign_id) as bound_id,
    
    -- Lead info (if bound to lead)
    l.email as lead_email,
    l.company as lead_company,
    
    -- Campaign info (if bound to campaign)
    c.name as campaign_name
    
FROM reports r
LEFT JOIN report_links rl ON r.id = rl.report_id
LEFT JOIN leads l ON rl.lead_id = l.id
LEFT JOIN campaigns c ON rl.campaign_id = c.id;

COMMENT ON VIEW reports_with_links IS 'Reports met bound info voor UI display';

-- View 7: unbound_reports
-- Reports zonder binding (voor manual binding UI)
CREATE OR REPLACE VIEW unbound_reports AS
SELECT r.*
FROM reports r
LEFT JOIN report_links rl ON r.id = rl.report_id
WHERE rl.id IS NULL
ORDER BY r.created_at DESC;

COMMENT ON VIEW unbound_reports IS 'Unbound reports voor manual binding';

-- ============================================================================
-- INBOX MODULE VIEWS
-- ============================================================================

-- View 8: inbox_summary
-- Aggregate inbox statistics per account
CREATE OR REPLACE VIEW inbox_summary AS
SELECT 
    ma.id as account_id,
    ma.label,
    ma.username,
    ma.active,
    ma.last_fetch_at,
    
    -- Message counts
    COUNT(mm.id) as total_messages,
    COUNT(CASE WHEN mm.is_read = FALSE THEN 1 END) as unread_count,
    COUNT(CASE WHEN mm.linked_campaign_id IS NOT NULL THEN 1 END) as linked_campaign_count,
    COUNT(CASE WHEN mm.linked_lead_id IS NOT NULL THEN 1 END) as linked_lead_count,
    COUNT(CASE WHEN mm.weak_link = TRUE THEN 1 END) as weak_link_count,
    
    -- Latest message
    MAX(mm.received_at) as latest_message_at,
    
    -- Fetch stats
    (SELECT COUNT(*) FROM mail_fetch_runs mfr WHERE mfr.account_id = ma.id) as total_fetch_runs,
    (SELECT MAX(finished_at) FROM mail_fetch_runs mfr WHERE mfr.account_id = ma.id) as last_fetch_finished_at

FROM mail_accounts ma
LEFT JOIN mail_messages mm ON ma.id = mm.account_id
GROUP BY ma.id, ma.label, ma.username, ma.active, ma.last_fetch_at;

COMMENT ON VIEW inbox_summary IS 'Aggregate inbox statistics per IMAP account';

-- ============================================================================
-- STATISTICS & MONITORING VIEWS
-- ============================================================================

-- View 9: daily_stats
-- Aggregated daily statistics (leads, campaigns, messages)
CREATE OR REPLACE VIEW daily_stats AS
SELECT 
    date_series.date,
    
    -- Leads stats
    (SELECT COUNT(*) FROM leads WHERE DATE(created_at) = date_series.date) as leads_created,
    (SELECT COUNT(*) FROM leads WHERE deleted_at IS NULL AND DATE(created_at) <= date_series.date) as leads_total,
    
    -- Campaign stats
    (SELECT COUNT(*) FROM campaigns WHERE DATE(created_at) = date_series.date) as campaigns_created,
    (SELECT COUNT(*) FROM campaigns WHERE status = 'running' AND DATE(start_at) <= date_series.date) as campaigns_running,
    
    -- Message stats
    (SELECT COUNT(*) FROM messages WHERE DATE(sent_at) = date_series.date) as messages_sent,
    (SELECT COUNT(*) FROM messages WHERE DATE(sent_at) = date_series.date AND status = 'opened') as messages_opened,
    (SELECT COUNT(*) FROM messages WHERE DATE(sent_at) = date_series.date AND status = 'bounced') as messages_bounced,
    
    -- Open rate
    ROUND(
        COALESCE(
            (SELECT COUNT(*) FROM messages WHERE DATE(sent_at) = date_series.date AND status = 'opened')::float /
            NULLIF((SELECT COUNT(*) FROM messages WHERE DATE(sent_at) = date_series.date), 0) * 100,
            0
        ), 2
    ) as open_rate_pct
    
FROM generate_series(
    NOW() - INTERVAL '30 days',
    NOW(),
    INTERVAL '1 day'
) AS date_series(date);

COMMENT ON VIEW daily_stats IS 'Aggregated daily statistics voor laatste 30 dagen';

-- ============================================================================
-- REFRESH MATERIALIZED VIEWS (FUTURE)
-- ============================================================================

-- Voor performance bij zeer grote datasets, convert views naar materialized views:
-- CREATE MATERIALIZED VIEW mv_campaign_kpis AS SELECT * FROM campaign_kpis;
-- CREATE UNIQUE INDEX ON mv_campaign_kpis(id);
-- 
-- Refresh schedule (via cron):
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_campaign_kpis;

-- ============================================================================
-- VIEW DEPLOYMENT COMPLETE
-- ============================================================================
-- Total views created: 9 views
-- Performance: Denormalized data voor snelle queries
-- Next step: Run supabase_functions.sql
-- ============================================================================

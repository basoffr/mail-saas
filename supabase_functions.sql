-- ============================================================================
-- SUPABASE DATABASE FUNCTIONS - MAIL DASHBOARD
-- ============================================================================
-- Project: Mail SaaS Platform
-- Total Functions: 15+ stored procedures & functions
-- Usage: Run AFTER supabase_views.sql
-- ============================================================================

-- ============================================================================
-- UTILITY FUNCTIONS
-- ============================================================================

-- Function 1: Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_updated_at_column IS 'Trigger function om updated_at automatisch te updaten';

-- ============================================================================
-- LEADS MODULE FUNCTIONS
-- ============================================================================

-- Function 2: Check lead completeness
CREATE OR REPLACE FUNCTION is_lead_complete(lead_id_param VARCHAR)
RETURNS BOOLEAN AS $$
DECLARE
    result BOOLEAN;
BEGIN
    SELECT 
        l.company IS NOT NULL AND l.company != '' AND
        l.url IS NOT NULL AND l.url != '' AND
        l.vars ? 'keyword' AND l.vars->>'keyword' != '' AND
        l.vars ? 'google_rank' AND l.vars->>'google_rank' != '' AND
        l.image_key IS NOT NULL AND l.image_key != '' AND
        EXISTS(SELECT 1 FROM report_links rl WHERE rl.lead_id = l.id)
    INTO result
    FROM leads l
    WHERE l.id = lead_id_param AND l.deleted_at IS NULL;
    
    RETURN COALESCE(result, FALSE);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION is_lead_complete IS 'Check of een lead alle required data heeft';

-- Function 3: Get lead vars completeness percentage
CREATE OR REPLACE FUNCTION get_lead_completeness_pct(lead_id_param VARCHAR)
RETURNS INTEGER AS $$
DECLARE
    pct INTEGER;
BEGIN
    SELECT vars_percentage INTO pct
    FROM leads_enriched
    WHERE id = lead_id_param;
    
    RETURN COALESCE(pct, 0);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_lead_completeness_pct IS 'Geef completeness percentage voor een lead';

-- Function 4: Soft delete lead
CREATE OR REPLACE FUNCTION soft_delete_lead(lead_id_param VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE leads 
    SET deleted_at = NOW()
    WHERE id = lead_id_param AND deleted_at IS NULL;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION soft_delete_lead IS 'Soft delete een lead (zet deleted_at timestamp)';

-- Function 5: Restore soft-deleted lead
CREATE OR REPLACE FUNCTION restore_lead(lead_id_param VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE leads 
    SET deleted_at = NULL
    WHERE id = lead_id_param AND deleted_at IS NOT NULL;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION restore_lead IS 'Restore een soft-deleted lead';

-- ============================================================================
-- CAMPAIGNS MODULE FUNCTIONS
-- ============================================================================

-- Function 6: Get available domains for campaign
CREATE OR REPLACE FUNCTION get_available_domains(exclude_campaigns VARCHAR[] DEFAULT ARRAY[]::VARCHAR[])
RETURNS TABLE(domain VARCHAR, active_campaign_count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.domain_value as domain,
        COUNT(c.id) as active_campaign_count
    FROM 
        (SELECT jsonb_array_elements_text(domains) as domain_value FROM settings WHERE id = 'singleton') s
    LEFT JOIN campaigns c ON s.domain_value = c.domain AND c.status = 'running' AND NOT (c.id = ANY(exclude_campaigns))
    GROUP BY s.domain_value
    ORDER BY active_campaign_count ASC, s.domain_value;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_available_domains IS 'Get beschikbare domains voor nieuwe campaign (sorted by least active)';

-- Function 7: Calculate campaign ETA
CREATE OR REPLACE FUNCTION calculate_campaign_eta(
    lead_count INTEGER,
    throttle_minutes INTEGER DEFAULT 20,
    domains_count INTEGER DEFAULT 4
)
RETURNS INTERVAL AS $$
DECLARE
    messages_per_hour INTEGER;
    total_hours FLOAT;
BEGIN
    -- 1 email per throttle_minutes per domain
    messages_per_hour := (60 / throttle_minutes) * domains_count;
    
    -- Total hours needed
    total_hours := lead_count::float / messages_per_hour;
    
    RETURN (total_hours || ' hours')::INTERVAL;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calculate_campaign_eta IS 'Bereken geschatte duur voor campaign completion';

-- Function 8: Get next available send slot
CREATE OR REPLACE FUNCTION get_next_send_slot(
    domain_param VARCHAR,
    after_time TIMESTAMPTZ DEFAULT NOW()
)
RETURNS TIMESTAMPTZ AS $$
DECLARE
    last_scheduled TIMESTAMPTZ;
    throttle_mins INTEGER;
    next_slot TIMESTAMPTZ;
BEGIN
    -- Get throttle setting
    SELECT throttle_minutes INTO throttle_mins FROM settings WHERE id = 'singleton';
    
    -- Get last scheduled message for this domain
    SELECT MAX(scheduled_at) INTO last_scheduled
    FROM messages
    WHERE domain_used = domain_param
        AND scheduled_at >= after_time;
    
    -- Calculate next slot
    IF last_scheduled IS NULL THEN
        next_slot := after_time;
    ELSE
        next_slot := last_scheduled + (throttle_mins || ' minutes')::INTERVAL;
    END IF;
    
    RETURN next_slot;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_next_send_slot IS 'Get next available send slot voor een domain (throttling)';

-- ============================================================================
-- REPORTS MODULE FUNCTIONS
-- ============================================================================

-- Function 9: Bind report to lead
CREATE OR REPLACE FUNCTION bind_report_to_lead(
    report_id_param VARCHAR,
    lead_id_param VARCHAR
)
RETURNS VARCHAR AS $$
DECLARE
    link_id VARCHAR;
BEGIN
    -- Check if report exists
    IF NOT EXISTS (SELECT 1 FROM reports WHERE id = report_id_param) THEN
        RAISE EXCEPTION 'Report not found: %', report_id_param;
    END IF;
    
    -- Check if lead exists
    IF NOT EXISTS (SELECT 1 FROM leads WHERE id = lead_id_param) THEN
        RAISE EXCEPTION 'Lead not found: %', lead_id_param;
    END IF;
    
    -- Remove existing links for this report
    DELETE FROM report_links WHERE report_id = report_id_param;
    
    -- Create new link
    link_id := 'link_' || substr(md5(random()::text), 0, 16);
    INSERT INTO report_links (id, report_id, lead_id, created_at)
    VALUES (link_id, report_id_param, lead_id_param, NOW());
    
    RETURN link_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION bind_report_to_lead IS 'Bind een report aan een lead (removes existing bindings)';

-- Function 10: Unbind report
CREATE OR REPLACE FUNCTION unbind_report(report_id_param VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN
    DELETE FROM report_links WHERE report_id = report_id_param;
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION unbind_report IS 'Remove alle bindings voor een report';

-- ============================================================================
-- INBOX MODULE FUNCTIONS
-- ============================================================================

-- Function 11: Link inbox message to campaign message
CREATE OR REPLACE FUNCTION link_inbox_message(
    inbox_message_id_param VARCHAR,
    campaign_message_id_param VARCHAR,
    is_weak_link BOOLEAN DEFAULT FALSE
)
RETURNS BOOLEAN AS $$
DECLARE
    campaign_id_val VARCHAR;
    lead_id_val VARCHAR;
BEGIN
    -- Get campaign and lead from campaign message
    SELECT campaign_id, lead_id INTO campaign_id_val, lead_id_val
    FROM messages
    WHERE id = campaign_message_id_param;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Campaign message not found: %', campaign_message_id_param;
    END IF;
    
    -- Update inbox message with links
    UPDATE mail_messages
    SET 
        linked_campaign_id = campaign_id_val,
        linked_lead_id = lead_id_val,
        linked_message_id = campaign_message_id_param,
        weak_link = is_weak_link
    WHERE id = inbox_message_id_param;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION link_inbox_message IS 'Link inbox message to campaign/lead/message';

-- ============================================================================
-- STATISTICS FUNCTIONS
-- ============================================================================

-- Function 12: Get campaign statistics
CREATE OR REPLACE FUNCTION get_campaign_stats(
    campaign_id_param VARCHAR,
    from_date TIMESTAMPTZ DEFAULT NULL,
    to_date TIMESTAMPTZ DEFAULT NULL
)
RETURNS TABLE(
    metric VARCHAR,
    value BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 'total_planned'::VARCHAR, COUNT(*)
    FROM messages WHERE campaign_id = campaign_id_param
    UNION ALL
    SELECT 'total_sent'::VARCHAR, COUNT(*)
    FROM messages WHERE campaign_id = campaign_id_param AND status = 'sent'
    UNION ALL
    SELECT 'total_opened'::VARCHAR, COUNT(*)
    FROM messages WHERE campaign_id = campaign_id_param AND status = 'opened'
    UNION ALL
    SELECT 'total_bounced'::VARCHAR, COUNT(*)
    FROM messages WHERE campaign_id = campaign_id_param AND status = 'bounced'
    UNION ALL
    SELECT 'total_failed'::VARCHAR, COUNT(*)
    FROM messages WHERE campaign_id = campaign_id_param AND status = 'failed';
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_campaign_stats IS 'Get detailed campaign statistics';

-- Function 13: Get domain statistics
CREATE OR REPLACE FUNCTION get_domain_stats(
    domain_param VARCHAR DEFAULT NULL,
    from_date TIMESTAMPTZ DEFAULT NOW() - INTERVAL '30 days',
    to_date TIMESTAMPTZ DEFAULT NOW()
)
RETURNS TABLE(
    domain VARCHAR,
    total_sent BIGINT,
    total_opened BIGINT,
    total_bounced BIGINT,
    open_rate_pct NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.domain_used as domain,
        COUNT(CASE WHEN m.status = 'sent' THEN 1 END) as total_sent,
        COUNT(CASE WHEN m.status = 'opened' THEN 1 END) as total_opened,
        COUNT(CASE WHEN m.status = 'bounced' THEN 1 END) as total_bounced,
        ROUND(
            COALESCE(
                COUNT(CASE WHEN m.status = 'opened' THEN 1 END)::float / 
                NULLIF(COUNT(CASE WHEN m.status = 'sent' THEN 1 END), 0) * 100,
                0
            ), 2
        ) as open_rate_pct
    FROM messages m
    WHERE (domain_param IS NULL OR m.domain_used = domain_param)
        AND m.sent_at BETWEEN from_date AND to_date
    GROUP BY m.domain_used
    ORDER BY total_sent DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_domain_stats IS 'Get statistics per domain';

-- ============================================================================
-- MAINTENANCE FUNCTIONS
-- ============================================================================

-- Function 14: Clean old deleted leads (permanent delete after 30 days)
CREATE OR REPLACE FUNCTION cleanup_deleted_leads(days_threshold INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete leads that were soft-deleted more than X days ago
    WITH deleted AS (
        DELETE FROM leads
        WHERE deleted_at IS NOT NULL
            AND deleted_at < NOW() - (days_threshold || ' days')::INTERVAL
        RETURNING id
    )
    SELECT COUNT(*) INTO deleted_count FROM deleted;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_deleted_leads IS 'Permanent delete soft-deleted leads ouder dan X dagen';

-- Function 15: Archive old campaigns (move completed campaigns older than 1 year)
CREATE OR REPLACE FUNCTION archive_old_campaigns(years_threshold INTEGER DEFAULT 1)
RETURNS INTEGER AS $$
DECLARE
    archived_count INTEGER;
BEGIN
    -- Update campaign status to 'archived' (zou nieuwe status moeten zijn)
    WITH archived AS (
        UPDATE campaigns
        SET status = 'completed'  -- In MVP hebben we geen 'archived' status
        WHERE status = 'completed'
            AND created_at < NOW() - (years_threshold || ' years')::INTERVAL
        RETURNING id
    )
    SELECT COUNT(*) INTO archived_count FROM archived;
    
    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION archive_old_campaigns IS 'Archive oude completed campaigns';

-- ============================================================================
-- ADMIN / DEBUGGING FUNCTIONS
-- ============================================================================

-- Function 16: Get table sizes
CREATE OR REPLACE FUNCTION get_table_sizes()
RETURNS TABLE(
    table_name TEXT,
    row_count BIGINT,
    total_size TEXT,
    table_size TEXT,
    indexes_size TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        schemaname || '.' || tablename AS table_name,
        n_live_tup AS row_count,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
        pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS indexes_size
    FROM pg_stat_user_tables
    WHERE schemaname = 'public'
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_table_sizes IS 'Get sizes van alle tabellen voor monitoring';

-- ============================================================================
-- FUNCTION DEPLOYMENT COMPLETE
-- ============================================================================
-- Total functions created: 16 functions
-- Usage: Various business logic, maintenance, and utility functions
-- Next step: Run supabase_triggers.sql
-- ============================================================================

-- ============================================================================
-- UPDATE 5 FUNCTIONS WITH search_path
-- ============================================================================
-- Run deze 5 functies opnieuw met SET search_path toegevoegd
-- ============================================================================

-- Function 7: Calculate campaign ETA
CREATE OR REPLACE FUNCTION calculate_campaign_eta(
    lead_count INTEGER,
    throttle_minutes INTEGER DEFAULT 20,
    domains_count INTEGER DEFAULT 4
)
RETURNS INTERVAL
SET search_path = public, pg_temp
AS $$
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

-- Function 8: Get next available send slot
CREATE OR REPLACE FUNCTION get_next_send_slot(
    domain_param VARCHAR,
    after_time TIMESTAMPTZ DEFAULT NOW()
)
RETURNS TIMESTAMPTZ
SET search_path = public, pg_temp
AS $$
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

-- Function 11: Link inbox message to campaign message
CREATE OR REPLACE FUNCTION link_inbox_message(
    inbox_message_id_param VARCHAR,
    campaign_message_id_param VARCHAR,
    is_weak_link BOOLEAN DEFAULT FALSE
)
RETURNS BOOLEAN
SET search_path = public, pg_temp
AS $$
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

-- Function 12: Get campaign statistics
CREATE OR REPLACE FUNCTION get_campaign_stats(
    campaign_id_param VARCHAR,
    from_date TIMESTAMPTZ DEFAULT NULL,
    to_date TIMESTAMPTZ DEFAULT NULL
)
RETURNS TABLE(
    metric VARCHAR,
    value BIGINT
)
SET search_path = public, pg_temp
AS $$
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
)
SET search_path = public, pg_temp
AS $$
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

-- ============================================================================
-- DONE! All 5 functions updated with SET search_path
-- ============================================================================

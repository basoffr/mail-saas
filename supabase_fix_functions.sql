-- ============================================================================
-- FIX 5 REMAINING FUNCTION WARNINGS
-- ============================================================================
-- Drop en recreate 5 functions met search_path parameter
-- ============================================================================

-- Drop alle 5 functies eerst
DROP FUNCTION IF EXISTS calculate_campaign_eta(VARCHAR);
DROP FUNCTION IF EXISTS get_next_send_slot(VARCHAR);
DROP FUNCTION IF EXISTS link_inbox_message(VARCHAR, VARCHAR);
DROP FUNCTION IF EXISTS get_campaign_stats(VARCHAR);
DROP FUNCTION IF EXISTS get_domain_stats(VARCHAR);

-- Recreate met search_path

CREATE FUNCTION calculate_campaign_eta(campaign_id_param VARCHAR)
RETURNS TIMESTAMPTZ
SECURITY DEFINER
SET search_path = ''
LANGUAGE plpgsql AS $$
DECLARE
    eta TIMESTAMPTZ;
BEGIN
    SELECT MAX(scheduled_at) INTO eta
    FROM public.messages
    WHERE campaign_id = campaign_id_param;
    
    RETURN eta;
END;
$$;

CREATE FUNCTION get_next_send_slot(domain_param VARCHAR)
RETURNS TIMESTAMPTZ
SECURITY DEFINER
SET search_path = ''
LANGUAGE plpgsql AS $$
DECLARE
    last_sent TIMESTAMPTZ;
    next_slot TIMESTAMPTZ;
BEGIN
    SELECT MAX(sent_at) INTO last_sent
    FROM public.messages
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

CREATE FUNCTION link_inbox_message(
    mail_message_id_param VARCHAR,
    campaign_message_id_param VARCHAR
)
RETURNS BOOLEAN
SECURITY DEFINER
SET search_path = ''
LANGUAGE plpgsql AS $$
BEGIN
    UPDATE public.mail_messages
    SET linked_message_id = campaign_message_id_param
    WHERE id = mail_message_id_param;
    
    RETURN FOUND;
END;
$$;

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
SET search_path = ''
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
    FROM public.messages
    WHERE campaign_id = campaign_id_param;
END;
$$;

CREATE FUNCTION get_domain_stats(domain_param VARCHAR)
RETURNS TABLE(
    total_sent BIGINT,
    last_sent TIMESTAMPTZ,
    avg_open_rate NUMERIC
)
SECURITY DEFINER
SET search_path = ''
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
    FROM public.messages
    WHERE domain_used = domain_param;
END;
$$;

-- ============================================================================
-- DONE! All 5 function warnings should be resolved.
-- ============================================================================

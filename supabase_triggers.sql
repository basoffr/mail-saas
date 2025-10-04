-- ============================================================================
-- SUPABASE DATABASE TRIGGERS - MAIL DASHBOARD
-- ============================================================================
-- Project: Mail SaaS Platform
-- Total Triggers: 10+ triggers for auto-updates
-- Usage: Run AFTER supabase_functions.sql
-- ============================================================================

-- ============================================================================
-- AUTO-UPDATE TRIGGERS (updated_at)
-- ============================================================================

-- Trigger 1: Leads updated_at
DROP TRIGGER IF EXISTS trigger_leads_updated_at ON leads;
CREATE TRIGGER trigger_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TRIGGER trigger_leads_updated_at ON leads IS 'Auto-update updated_at bij lead wijziging';

-- Trigger 2: Campaigns updated_at
DROP TRIGGER IF EXISTS trigger_campaigns_updated_at ON campaigns;
CREATE TRIGGER trigger_campaigns_updated_at
    BEFORE UPDATE ON campaigns
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TRIGGER trigger_campaigns_updated_at ON campaigns IS 'Auto-update updated_at bij campaign wijziging';

-- Trigger 3: Templates updated_at
DROP TRIGGER IF EXISTS trigger_templates_updated_at ON templates;
CREATE TRIGGER trigger_templates_updated_at
    BEFORE UPDATE ON templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TRIGGER trigger_templates_updated_at ON templates IS 'Auto-update updated_at bij template wijziging';

-- Trigger 4: Mail accounts updated_at
DROP TRIGGER IF EXISTS trigger_mail_accounts_updated_at ON mail_accounts;
CREATE TRIGGER trigger_mail_accounts_updated_at
    BEFORE UPDATE ON mail_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TRIGGER trigger_mail_accounts_updated_at ON mail_accounts IS 'Auto-update updated_at bij mail account wijziging';

-- ============================================================================
-- AUDIT / LOGGING TRIGGERS (FUTURE)
-- ============================================================================

-- Function: Log lead changes (voor audit trail)
CREATE OR REPLACE FUNCTION log_lead_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Future: Insert into audit_log table
    -- Voor MVP: Alleen logging via backend applicatie
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger 5: Lead changes audit (DISABLED voor MVP)
-- DROP TRIGGER IF EXISTS trigger_lead_audit ON leads;
-- CREATE TRIGGER trigger_lead_audit
--     AFTER INSERT OR UPDATE OR DELETE ON leads
--     FOR EACH ROW
--     EXECUTE FUNCTION log_lead_change();

-- ============================================================================
-- BUSINESS LOGIC TRIGGERS
-- ============================================================================

-- Function: Auto-update campaign status
CREATE OR REPLACE FUNCTION auto_update_campaign_status()
RETURNS TRIGGER AS $$
DECLARE
    all_sent BOOLEAN;
    has_queued BOOLEAN;
BEGIN
    -- Check if all messages are sent/failed/bounced
    SELECT 
        NOT EXISTS(SELECT 1 FROM messages WHERE campaign_id = NEW.campaign_id AND status = 'queued'),
        EXISTS(SELECT 1 FROM messages WHERE campaign_id = NEW.campaign_id AND status = 'queued')
    INTO all_sent, has_queued;
    
    -- Update campaign status if needed
    IF all_sent AND NOT has_queued THEN
        UPDATE campaigns 
        SET status = 'completed' 
        WHERE id = NEW.campaign_id AND status = 'running';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger 6: Message status change updates campaign
DROP TRIGGER IF EXISTS trigger_message_status_updates_campaign ON messages;
CREATE TRIGGER trigger_message_status_updates_campaign
    AFTER UPDATE OF status ON messages
    FOR EACH ROW
    WHEN (OLD.status IS DISTINCT FROM NEW.status)
    EXECUTE FUNCTION auto_update_campaign_status();

COMMENT ON TRIGGER trigger_message_status_updates_campaign ON messages IS 'Auto-update campaign status als alle messages done zijn';

-- ============================================================================
-- DATA VALIDATION TRIGGERS
-- ============================================================================

-- Function: Validate lead email format
CREATE OR REPLACE FUNCTION validate_lead_email()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.email IS NULL OR NEW.email = '' THEN
        RAISE EXCEPTION 'Email cannot be empty';
    END IF;
    
    IF NEW.email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$' THEN
        RAISE EXCEPTION 'Invalid email format: %', NEW.email;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger 7: Lead email validation (DISABLED voor MVP - gebeurt in backend)
-- DROP TRIGGER IF EXISTS trigger_validate_lead_email ON leads;
-- CREATE TRIGGER trigger_validate_lead_email
--     BEFORE INSERT OR UPDATE OF email ON leads
--     FOR EACH ROW
--     EXECUTE FUNCTION validate_lead_email();

-- ============================================================================
-- CASCADE UPDATE TRIGGERS
-- ============================================================================

-- Function: Update lead last_emailed_at when message sent
CREATE OR REPLACE FUNCTION update_lead_last_emailed()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'sent' AND (OLD.status IS NULL OR OLD.status != 'sent') THEN
        UPDATE leads 
        SET last_emailed_at = NEW.sent_at
        WHERE id = NEW.lead_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger 8: Message sent updates lead last_emailed_at
DROP TRIGGER IF EXISTS trigger_message_sent_updates_lead ON messages;
CREATE TRIGGER trigger_message_sent_updates_lead
    AFTER UPDATE OF status ON messages
    FOR EACH ROW
    WHEN (NEW.status = 'sent')
    EXECUTE FUNCTION update_lead_last_emailed();

COMMENT ON TRIGGER trigger_message_sent_updates_lead ON messages IS 'Update lead.last_emailed_at when message sent';

-- Function: Update lead last_open_at when message opened
CREATE OR REPLACE FUNCTION update_lead_last_opened()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'opened' AND (OLD.status IS NULL OR OLD.status != 'opened') THEN
        UPDATE leads 
        SET last_open_at = NEW.open_at
        WHERE id = NEW.lead_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger 9: Message opened updates lead last_open_at
DROP TRIGGER IF EXISTS trigger_message_opened_updates_lead ON messages;
CREATE TRIGGER trigger_message_opened_updates_lead
    AFTER UPDATE OF status ON messages
    FOR EACH ROW
    WHEN (NEW.status = 'opened')
    EXECUTE FUNCTION update_lead_last_opened();

COMMENT ON TRIGGER trigger_message_opened_updates_lead ON messages IS 'Update lead.last_open_at when message opened';

-- ============================================================================
-- AUTO-CREATE MESSAGE EVENTS TRIGGER
-- ============================================================================

-- Function: Auto-create message event on status change
CREATE OR REPLACE FUNCTION auto_create_message_event()
RETURNS TRIGGER AS $$
DECLARE
    event_type_val VARCHAR;
BEGIN
    -- Determine event type from status
    CASE NEW.status
        WHEN 'sent' THEN event_type_val := 'sent';
        WHEN 'opened' THEN event_type_val := 'opened';
        WHEN 'bounced' THEN event_type_val := 'bounced';
        WHEN 'failed' THEN event_type_val := 'failed';
        ELSE RETURN NEW;  -- No event for other statuses
    END CASE;
    
    -- Only create event on status change
    IF OLD.status IS NULL OR OLD.status != NEW.status THEN
        INSERT INTO message_events (id, message_id, event_type, created_at)
        VALUES (
            'event_' || substr(md5(random()::text), 0, 16),
            NEW.id,
            event_type_val,
            NOW()
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger 10: Message status change creates event
DROP TRIGGER IF EXISTS trigger_auto_create_message_event ON messages;
CREATE TRIGGER trigger_auto_create_message_event
    AFTER UPDATE OF status ON messages
    FOR EACH ROW
    EXECUTE FUNCTION auto_create_message_event();

COMMENT ON TRIGGER trigger_auto_create_message_event ON messages IS 'Auto-create message_event bij status change';

-- ============================================================================
-- PREVENT INVALID OPERATIONS TRIGGERS
-- ============================================================================

-- Function: Prevent modifying sent messages
CREATE OR REPLACE FUNCTION prevent_sent_message_modification()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status = 'sent' AND NEW.status != OLD.status THEN
        -- Allow sent → opened transition
        IF NEW.status != 'opened' THEN
            RAISE EXCEPTION 'Cannot change status of sent message to %', NEW.status;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger 11: Prevent invalid message status changes (DISABLED voor MVP)
-- DROP TRIGGER IF EXISTS trigger_prevent_sent_modification ON messages;
-- CREATE TRIGGER trigger_prevent_sent_modification
--     BEFORE UPDATE OF status ON messages
--     FOR EACH ROW
--     WHEN (OLD.status = 'sent')
--     EXECUTE FUNCTION prevent_sent_message_modification();

-- ============================================================================
-- CLEANUP TRIGGERS (FUTURE)
-- ============================================================================

-- Function: Auto-cleanup old message events
CREATE OR REPLACE FUNCTION auto_cleanup_old_events()
RETURNS TRIGGER AS $$
BEGIN
    -- Delete message_events older than 1 year (voor MVP: manual cleanup)
    -- DELETE FROM message_events 
    -- WHERE created_at < NOW() - INTERVAL '1 year';
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger 12: Cleanup events on message insert (DISABLED - use cron job)
-- DROP TRIGGER IF EXISTS trigger_auto_cleanup_events ON messages;
-- CREATE TRIGGER trigger_auto_cleanup_events
--     AFTER INSERT ON messages
--     FOR EACH STATEMENT
--     EXECUTE FUNCTION auto_cleanup_old_events();

-- ============================================================================
-- NOTIFICATION TRIGGERS (FUTURE - voor real-time updates)
-- ============================================================================

-- Function: Notify on campaign status change
CREATE OR REPLACE FUNCTION notify_campaign_status_change()
RETURNS TRIGGER AS $$
BEGIN
    -- PostgreSQL NOTIFY voor real-time updates
    PERFORM pg_notify(
        'campaign_status_changed',
        json_build_object(
            'campaign_id', NEW.id,
            'old_status', OLD.status,
            'new_status', NEW.status,
            'timestamp', NOW()
        )::text
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger 13: Campaign status change notification (DISABLED voor MVP)
-- DROP TRIGGER IF EXISTS trigger_notify_campaign_status ON campaigns;
-- CREATE TRIGGER trigger_notify_campaign_status
--     AFTER UPDATE OF status ON campaigns
--     FOR EACH ROW
--     WHEN (OLD.status IS DISTINCT FROM NEW.status)
--     EXECUTE FUNCTION notify_campaign_status_change();

-- ============================================================================
-- TRIGGER DEPLOYMENT COMPLETE
-- ============================================================================
-- Active triggers: 9 enabled triggers
-- Disabled triggers: 4 disabled (voor future use)
-- Key features:
--   - Auto-update updated_at timestamps
--   - Auto-update campaign status
--   - Auto-update lead tracking fields
--   - Auto-create message events
-- Next step: Run supabase_rls.sql (optional voor multi-tenant)
-- ============================================================================

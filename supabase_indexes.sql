-- ============================================================================
-- SUPABASE PERFORMANCE INDEXES - MAIL DASHBOARD
-- ============================================================================
-- Project: Mail SaaS Platform
-- Total Indexes: 60+ indexes voor performance optimization
-- Usage: Run AFTER supabase_schema.sql
-- Concurrency: Use CONCURRENTLY voor zero-downtime op production
-- ============================================================================

-- ============================================================================
-- MODULE 1: LEADS INDEXES
-- ============================================================================

-- Primary indexes (already created via model, maar expliciet hier voor volledigheid)
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_domain ON leads(domain);
CREATE INDEX IF NOT EXISTS idx_leads_list_name ON leads(list_name);
CREATE INDEX IF NOT EXISTS idx_leads_last_emailed_at ON leads(last_emailed_at);
CREATE INDEX IF NOT EXISTS idx_leads_stopped ON leads(stopped);
CREATE INDEX IF NOT EXISTS idx_leads_deleted_at ON leads(deleted_at);

-- Composite indexes voor complexe queries
CREATE INDEX IF NOT EXISTS idx_leads_active_status ON leads(status, deleted_at, stopped) 
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_leads_domain_status ON leads(domain, status) 
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_leads_list_active ON leads(list_name, status, last_emailed_at) 
    WHERE status = 'active' AND deleted_at IS NULL AND stopped = FALSE;

CREATE INDEX IF NOT EXISTS idx_leads_targeting ON leads(status, list_name, last_emailed_at, stopped, deleted_at) 
    WHERE deleted_at IS NULL AND stopped = FALSE;

-- JSON indexes voor vars queries
CREATE INDEX IF NOT EXISTS idx_leads_vars_gin ON leads USING GIN(vars);
CREATE INDEX IF NOT EXISTS idx_leads_tags_gin ON leads USING GIN(tags);

-- Performance index voor vars completeness checks
CREATE INDEX IF NOT EXISTS idx_leads_image_key ON leads(image_key) WHERE image_key IS NOT NULL;

-- Assets indexes
CREATE INDEX IF NOT EXISTS idx_assets_key ON assets(key);
CREATE INDEX IF NOT EXISTS idx_assets_created_at ON assets(created_at DESC);

-- Import jobs indexes
CREATE INDEX IF NOT EXISTS idx_import_jobs_status ON import_jobs(status);
CREATE INDEX IF NOT EXISTS idx_import_jobs_created_at ON import_jobs(created_at DESC);

-- ============================================================================
-- MODULE 2: CAMPAIGNS INDEXES
-- ============================================================================

-- Campaigns indexes
CREATE INDEX IF NOT EXISTS idx_campaigns_name ON campaigns(name);
CREATE INDEX IF NOT EXISTS idx_campaigns_domain ON campaigns(domain);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaigns_start_at ON campaigns(start_at);
CREATE INDEX IF NOT EXISTS idx_campaigns_template_id ON campaigns(template_id);

-- Composite indexes voor campaign queries
CREATE INDEX IF NOT EXISTS idx_campaigns_status_start ON campaigns(status, start_at, domain) 
    WHERE status IN ('running', 'paused');

CREATE INDEX IF NOT EXISTS idx_campaigns_domain_status ON campaigns(domain, status);

-- Campaign audience indexes
CREATE INDEX IF NOT EXISTS idx_campaign_audience_campaign_id ON campaign_audience(campaign_id);
CREATE INDEX IF NOT EXISTS idx_campaign_audience_created_at ON campaign_audience(created_at DESC);

-- Messages indexes (CRITICAL VOOR PERFORMANCE)
CREATE INDEX IF NOT EXISTS idx_messages_campaign_id ON messages(campaign_id);
CREATE INDEX IF NOT EXISTS idx_messages_lead_id ON messages(lead_id);
CREATE INDEX IF NOT EXISTS idx_messages_domain_used ON messages(domain_used);
CREATE INDEX IF NOT EXISTS idx_messages_scheduled_at ON messages(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status);
CREATE INDEX IF NOT EXISTS idx_messages_mail_number ON messages(mail_number);
CREATE INDEX IF NOT EXISTS idx_messages_smtp_message_id ON messages(smtp_message_id);
CREATE INDEX IF NOT EXISTS idx_messages_x_campaign_message_id ON messages(x_campaign_message_id);
CREATE INDEX IF NOT EXISTS idx_messages_parent_message_id ON messages(parent_message_id);

-- Composite indexes voor message queries (HOT QUERIES)
CREATE INDEX IF NOT EXISTS idx_messages_status_scheduled ON messages(status, scheduled_at, domain_used) 
    WHERE status = 'queued';

CREATE INDEX IF NOT EXISTS idx_messages_campaign_status ON messages(campaign_id, status, scheduled_at);

CREATE INDEX IF NOT EXISTS idx_messages_domain_scheduled ON messages(domain_used, scheduled_at, status);

CREATE INDEX IF NOT EXISTS idx_messages_active_campaigns ON messages(campaign_id, status, scheduled_at) 
    WHERE status IN ('queued', 'sent');

CREATE INDEX IF NOT EXISTS idx_messages_sent_at ON messages(sent_at) WHERE sent_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_messages_open_at ON messages(open_at) WHERE open_at IS NOT NULL;

-- Message events indexes
CREATE INDEX IF NOT EXISTS idx_message_events_message_id ON message_events(message_id);
CREATE INDEX IF NOT EXISTS idx_message_events_event_type ON message_events(event_type);
CREATE INDEX IF NOT EXISTS idx_message_events_created_at ON message_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_message_events_type_created ON message_events(event_type, created_at DESC);

-- ============================================================================
-- MODULE 3: TEMPLATES INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_templates_name ON templates(name);
CREATE INDEX IF NOT EXISTS idx_templates_updated_at ON templates(updated_at DESC);

-- ============================================================================
-- MODULE 4: REPORTS INDEXES
-- ============================================================================

-- Reports indexes
CREATE INDEX IF NOT EXISTS idx_reports_filename ON reports(filename);
CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(type);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_uploaded_by ON reports(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_reports_type_created ON reports(type, created_at DESC);

-- Report links indexes
CREATE INDEX IF NOT EXISTS idx_report_links_report_id ON report_links(report_id);
CREATE INDEX IF NOT EXISTS idx_report_links_lead_id ON report_links(lead_id);
CREATE INDEX IF NOT EXISTS idx_report_links_campaign_id ON report_links(campaign_id);
CREATE INDEX IF NOT EXISTS idx_report_links_lead_created ON report_links(lead_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_report_links_campaign_created ON report_links(campaign_id, created_at DESC);

-- ============================================================================
-- MODULE 5: INBOX INDEXES
-- ============================================================================

-- Mail accounts indexes
CREATE INDEX IF NOT EXISTS idx_mail_accounts_label ON mail_accounts(label);
CREATE INDEX IF NOT EXISTS idx_mail_accounts_active ON mail_accounts(active);
CREATE INDEX IF NOT EXISTS idx_mail_accounts_username ON mail_accounts(username);

-- Mail messages indexes (CRITICAL VOOR INBOX LINKING)
CREATE INDEX IF NOT EXISTS idx_mail_messages_account_id ON mail_messages(account_id);
CREATE INDEX IF NOT EXISTS idx_mail_messages_message_id ON mail_messages(message_id);
CREATE INDEX IF NOT EXISTS idx_mail_messages_in_reply_to ON mail_messages(in_reply_to);
CREATE INDEX IF NOT EXISTS idx_mail_messages_from_email ON mail_messages(from_email);
CREATE INDEX IF NOT EXISTS idx_mail_messages_received_at ON mail_messages(received_at DESC);

-- Composite indexes voor inbox queries
CREATE INDEX IF NOT EXISTS idx_mail_messages_account_received ON mail_messages(account_id, received_at DESC);

CREATE INDEX IF NOT EXISTS idx_mail_messages_account_folder ON mail_messages(account_id, folder, received_at DESC);

-- Linking indexes
CREATE INDEX IF NOT EXISTS idx_mail_messages_linked_campaign ON mail_messages(linked_campaign_id) 
    WHERE linked_campaign_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_mail_messages_linked_lead ON mail_messages(linked_lead_id) 
    WHERE linked_lead_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_mail_messages_linked_message ON mail_messages(linked_message_id) 
    WHERE linked_message_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_mail_messages_weak_link ON mail_messages(weak_link) 
    WHERE weak_link = TRUE;

-- Mail fetch runs indexes
CREATE INDEX IF NOT EXISTS idx_mail_fetch_runs_account_id ON mail_fetch_runs(account_id);
CREATE INDEX IF NOT EXISTS idx_mail_fetch_runs_started_at ON mail_fetch_runs(started_at DESC);

-- ============================================================================
-- MODULE 6: SETTINGS INDEXES
-- ============================================================================

-- Settings heeft geen extra indexes nodig (singleton tabel)

-- ============================================================================
-- ADVANCED PERFORMANCE INDEXES
-- ============================================================================

-- Full-text search indexes (FUTURE)
-- CREATE INDEX IF NOT EXISTS idx_leads_email_trgm ON leads USING gin(email gin_trgm_ops);
-- CREATE INDEX IF NOT EXISTS idx_leads_company_trgm ON leads USING gin(company gin_trgm_ops);

-- Partial indexes voor specifieke use cases
CREATE INDEX IF NOT EXISTS idx_leads_incomplete ON leads(id, company, url, vars) 
    WHERE (company IS NULL OR url IS NULL OR vars = '{}'::jsonb) 
    AND deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_messages_failed_retryable ON messages(id, campaign_id, lead_id, retry_count) 
    WHERE status = 'failed' AND retry_count < 3;

-- ============================================================================
-- INDEX STATISTICS & MONITORING
-- ============================================================================

-- View om index usage te monitoren
CREATE OR REPLACE VIEW v_index_usage AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

COMMENT ON VIEW v_index_usage IS 'Monitor index usage voor performance optimization';

-- View om missing indexes te identificeren
CREATE OR REPLACE VIEW v_missing_indexes AS
SELECT 
    schemaname,
    tablename,
    seq_scan as sequential_scans,
    seq_tup_read as sequential_tuples,
    idx_scan as index_scans,
    idx_tup_fetch as index_tuples,
    CASE 
        WHEN seq_scan > 0 THEN ROUND((100.0 * seq_tup_read / seq_scan)::numeric, 2)
        ELSE 0 
    END as avg_seq_tuples
FROM pg_stat_user_tables
WHERE schemaname = 'public'
    AND seq_scan > idx_scan
ORDER BY seq_scan DESC;

COMMENT ON VIEW v_missing_indexes IS 'Identificeer tabellen met veel sequential scans (mogelijk missing indexes)';

-- ============================================================================
-- VACUUM & ANALYZE
-- ============================================================================

-- Run ANALYZE om query planner te updaten met nieuwe index statistics
ANALYZE leads;
ANALYZE campaigns;
ANALYZE messages;
ANALYZE message_events;
ANALYZE reports;
ANALYZE report_links;
ANALYZE mail_messages;
ANALYZE mail_accounts;

-- ============================================================================
-- INDEX DEPLOYMENT COMPLETE
-- ============================================================================
-- Total indexes created: 60+
-- Performance impact: Estimated 10-100x speedup op kritieke queries
-- Next step: Run supabase_views.sql
-- ============================================================================

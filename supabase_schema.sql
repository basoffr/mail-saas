-- ============================================================================
-- SUPABASE DATABASE SCHEMA - MAIL DASHBOARD
-- ============================================================================
-- Project: Mail SaaS Platform
-- Database: PostgreSQL 15+ via Supabase
-- Date: 2025-10-04
-- Tables: 11 tables across 6 modules
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- MODULE 1: LEADS (3 tables)
-- ============================================================================

-- Table: leads
CREATE TABLE IF NOT EXISTS leads (
    id VARCHAR PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    company VARCHAR(255),
    url TEXT,
    domain VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suppressed', 'bounced')),
    tags JSONB DEFAULT '[]'::jsonb,
    image_key VARCHAR(255),
    list_name VARCHAR(255),
    last_emailed_at TIMESTAMPTZ,
    last_open_at TIMESTAMPTZ,
    vars JSONB DEFAULT '{}'::jsonb,
    stopped BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE leads IS 'Lead informatie met email tracking en custom variables';
COMMENT ON COLUMN leads.email IS 'Unique email address';
COMMENT ON COLUMN leads.vars IS 'Custom variables zoals keyword, google_rank';
COMMENT ON COLUMN leads.stopped IS 'Lead stop functionaliteit - geen emails meer sturen';
COMMENT ON COLUMN leads.deleted_at IS 'Soft delete timestamp';

-- Table: assets
CREATE TABLE IF NOT EXISTS assets (
    id VARCHAR PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    mime VARCHAR(100) NOT NULL,
    size INTEGER NOT NULL CHECK (size > 0),
    checksum VARCHAR(64),
    storage_path TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE assets IS 'Dashboard images en andere asset bestanden';
COMMENT ON COLUMN assets.key IS 'Unique asset key voor referencing in templates/leads';

-- Table: import_jobs
CREATE TABLE IF NOT EXISTS import_jobs (
    id VARCHAR PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    inserted INTEGER DEFAULT 0,
    updated INTEGER DEFAULT 0,
    skipped INTEGER DEFAULT 0,
    errors JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE import_jobs IS 'Tracking van Excel import jobs';

-- ============================================================================
-- MODULE 2: CAMPAIGNS (4 tables)
-- ============================================================================

-- Table: campaigns
CREATE TABLE IF NOT EXISTS campaigns (
    id VARCHAR PRIMARY KEY,
    name TEXT NOT NULL,
    template_id VARCHAR NOT NULL,
    domain VARCHAR(255),
    start_at TIMESTAMPTZ,
    status VARCHAR(50) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'running', 'paused', 'completed', 'stopped')),
    followup_enabled BOOLEAN DEFAULT TRUE,
    followup_days INTEGER DEFAULT 3,
    followup_attach_report BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE campaigns IS 'Email campaigns met 4-domain flow support';
COMMENT ON COLUMN campaigns.domain IS 'Auto-assigned domain (v1-v4)';

-- Table: campaign_audience
CREATE TABLE IF NOT EXISTS campaign_audience (
    id VARCHAR PRIMARY KEY,
    campaign_id VARCHAR NOT NULL,
    lead_ids JSONB NOT NULL,
    exclude_suppressed BOOLEAN DEFAULT TRUE,
    exclude_recent_days INTEGER DEFAULT 14,
    one_per_domain BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE campaign_audience IS 'Audience snapshot voor campaigns';
COMMENT ON COLUMN campaign_audience.lead_ids IS 'Array van lead IDs in audience';

-- Table: messages
CREATE TABLE IF NOT EXISTS messages (
    id VARCHAR PRIMARY KEY,
    campaign_id VARCHAR NOT NULL,
    lead_id VARCHAR NOT NULL,
    domain_used VARCHAR(255) NOT NULL,
    scheduled_at TIMESTAMPTZ NOT NULL,
    sent_at TIMESTAMPTZ,
    mail_number INTEGER DEFAULT 1 CHECK (mail_number BETWEEN 1 AND 4),
    alias VARCHAR(50) DEFAULT 'christian',
    from_email VARCHAR(255),
    reply_to_email VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'sent', 'bounced', 'opened', 'failed', 'canceled')),
    last_error TEXT,
    open_at TIMESTAMPTZ,
    parent_message_id VARCHAR,
    is_followup BOOLEAN DEFAULT FALSE,
    retry_count INTEGER DEFAULT 0,
    smtp_message_id VARCHAR(255) UNIQUE,
    x_campaign_message_id VARCHAR(255),
    with_image BOOLEAN DEFAULT FALSE,
    with_report BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (campaign_id, lead_id)
);

COMMENT ON TABLE messages IS 'Individual emails per lead in campaign flow';
COMMENT ON COLUMN messages.mail_number IS '1-4 in campaign flow';
COMMENT ON COLUMN messages.alias IS 'christian or victor';
COMMENT ON COLUMN messages.smtp_message_id IS 'Voor inbox linking';

-- Table: message_events
CREATE TABLE IF NOT EXISTS message_events (
    id VARCHAR PRIMARY KEY,
    message_id VARCHAR NOT NULL,
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN ('sent', 'opened', 'bounced', 'failed')),
    meta JSONB,
    user_agent VARCHAR(512),
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE message_events IS 'Tracking events voor messages';

-- ============================================================================
-- MODULE 3: TEMPLATES (1 table)
-- ============================================================================

-- Table: templates
CREATE TABLE IF NOT EXISTS templates (
    id VARCHAR PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    subject_template TEXT NOT NULL,
    body_template TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    required_vars JSONB,
    assets JSONB
);

COMMENT ON TABLE templates IS 'Email templates met Jinja2 syntax';
COMMENT ON COLUMN templates.required_vars IS 'Array van required variable names';
COMMENT ON COLUMN templates.assets IS 'Array van asset references';

-- ============================================================================
-- MODULE 4: REPORTS (2 tables)
-- ============================================================================

-- Table: reports
CREATE TABLE IF NOT EXISTS reports (
    id VARCHAR PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    type VARCHAR(10) NOT NULL CHECK (type IN ('pdf', 'xlsx', 'png', 'jpg', 'jpeg')),
    size_bytes INTEGER NOT NULL CHECK (size_bytes > 0),
    storage_path TEXT NOT NULL,
    checksum VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    uploaded_by VARCHAR(255),
    meta JSONB
);

COMMENT ON TABLE reports IS 'Uploaded PDF/Excel/Image files';

-- Table: report_links
CREATE TABLE IF NOT EXISTS report_links (
    id VARCHAR PRIMARY KEY,
    report_id VARCHAR NOT NULL,
    lead_id VARCHAR,
    campaign_id VARCHAR,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT check_single_target CHECK (
        (lead_id IS NOT NULL AND campaign_id IS NULL) OR
        (lead_id IS NULL AND campaign_id IS NOT NULL)
    )
);

COMMENT ON TABLE report_links IS 'Many-to-many linking tussen reports en leads/campaigns';
COMMENT ON CONSTRAINT check_single_target ON report_links IS 'Exact één van lead_id of campaign_id moet gezet zijn';

-- ============================================================================
-- MODULE 5: INBOX (3 tables)
-- ============================================================================

-- Table: mail_accounts
CREATE TABLE IF NOT EXISTS mail_accounts (
    id VARCHAR PRIMARY KEY,
    label VARCHAR(255) NOT NULL,
    imap_host VARCHAR(255) NOT NULL,
    imap_port INTEGER DEFAULT 993,
    use_ssl BOOLEAN DEFAULT TRUE,
    username VARCHAR(255) NOT NULL,
    secret_ref VARCHAR(255) NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    last_fetch_at TIMESTAMPTZ,
    last_seen_uid INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE mail_accounts IS 'IMAP account configuratie';
COMMENT ON COLUMN mail_accounts.secret_ref IS 'Reference naar encrypted password, NOOIT plain text';

-- Table: mail_messages
CREATE TABLE IF NOT EXISTS mail_messages (
    id VARCHAR PRIMARY KEY,
    account_id VARCHAR NOT NULL,
    folder VARCHAR(100) DEFAULT 'INBOX',
    uid INTEGER NOT NULL,
    message_id VARCHAR(512),
    in_reply_to VARCHAR(512),
    reference_headers JSONB,
    from_email VARCHAR(255) NOT NULL,
    from_name VARCHAR(255),
    to_email VARCHAR(255),
    subject TEXT NOT NULL,
    snippet TEXT,
    raw_size INTEGER,
    received_at TIMESTAMPTZ NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    linked_campaign_id VARCHAR,
    linked_lead_id VARCHAR,
    linked_message_id VARCHAR,
    weak_link BOOLEAN DEFAULT FALSE,
    encoding_issue BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE mail_messages IS 'Received emails met smart linking';
COMMENT ON COLUMN mail_messages.snippet IS 'Max ~20kB preview';

-- Table: mail_fetch_runs
CREATE TABLE IF NOT EXISTS mail_fetch_runs (
    id VARCHAR PRIMARY KEY,
    account_id VARCHAR NOT NULL,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    new_count INTEGER,
    error TEXT
);

COMMENT ON TABLE mail_fetch_runs IS 'IMAP fetch job tracking';

-- ============================================================================
-- MODULE 6: SETTINGS (1 table)
-- ============================================================================

-- Table: settings
CREATE TABLE IF NOT EXISTS settings (
    id VARCHAR PRIMARY KEY DEFAULT 'singleton',
    timezone VARCHAR(50) DEFAULT 'Europe/Amsterdam',
    sending_window_start VARCHAR(5) DEFAULT '08:00',
    sending_window_end VARCHAR(5) DEFAULT '17:00',
    sending_days JSONB DEFAULT '["Mon", "Tue", "Wed", "Thu", "Fri"]'::jsonb,
    throttle_minutes INTEGER DEFAULT 20,
    domains JSONB DEFAULT '["punthelder-marketing.nl", "punthelder-seo.nl", "punthelder-vindbaarheid.nl", "punthelder-zoekmachine.nl"]'::jsonb,
    domains_config JSONB DEFAULT '[]'::jsonb,
    unsubscribe_text VARCHAR(50) DEFAULT 'Uitschrijven',
    tracking_pixel_enabled BOOLEAN DEFAULT TRUE,
    provider VARCHAR(50) DEFAULT 'SMTP',
    dns_spf VARCHAR(20) DEFAULT 'ok' CHECK (dns_spf IN ('ok', 'nok', 'unchecked')),
    dns_dkim VARCHAR(20) DEFAULT 'ok' CHECK (dns_dkim IN ('ok', 'nok', 'unchecked')),
    dns_dmarc VARCHAR(20) DEFAULT 'unchecked' CHECK (dns_dmarc IN ('ok', 'nok', 'unchecked'))
);

COMMENT ON TABLE settings IS 'Singleton configuratie tabel';

-- ============================================================================
-- FOREIGN KEY CONSTRAINTS
-- ============================================================================

-- Campaigns module
ALTER TABLE campaigns ADD CONSTRAINT fk_campaigns_template 
    FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE RESTRICT;

ALTER TABLE campaign_audience ADD CONSTRAINT fk_audience_campaign 
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE;

ALTER TABLE messages ADD CONSTRAINT fk_messages_campaign 
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE;

ALTER TABLE messages ADD CONSTRAINT fk_messages_lead 
    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE;

ALTER TABLE messages ADD CONSTRAINT fk_messages_parent 
    FOREIGN KEY (parent_message_id) REFERENCES messages(id) ON DELETE SET NULL;

ALTER TABLE message_events ADD CONSTRAINT fk_events_message 
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE;

-- Reports module
ALTER TABLE report_links ADD CONSTRAINT fk_report_links_report 
    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE;

ALTER TABLE report_links ADD CONSTRAINT fk_report_links_lead 
    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE;

ALTER TABLE report_links ADD CONSTRAINT fk_report_links_campaign 
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE;

-- Inbox module
ALTER TABLE mail_messages ADD CONSTRAINT fk_mail_messages_account 
    FOREIGN KEY (account_id) REFERENCES mail_accounts(id) ON DELETE CASCADE;

ALTER TABLE mail_messages ADD CONSTRAINT fk_mail_messages_campaign 
    FOREIGN KEY (linked_campaign_id) REFERENCES campaigns(id) ON DELETE SET NULL;

ALTER TABLE mail_messages ADD CONSTRAINT fk_mail_messages_lead 
    FOREIGN KEY (linked_lead_id) REFERENCES leads(id) ON DELETE SET NULL;

ALTER TABLE mail_messages ADD CONSTRAINT fk_mail_messages_message 
    FOREIGN KEY (linked_message_id) REFERENCES messages(id) ON DELETE SET NULL;

ALTER TABLE mail_fetch_runs ADD CONSTRAINT fk_fetch_runs_account 
    FOREIGN KEY (account_id) REFERENCES mail_accounts(id) ON DELETE CASCADE;

-- ============================================================================
-- INSERT DEFAULT SETTINGS
-- ============================================================================

INSERT INTO settings (id) VALUES ('singleton')
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- SCHEMA DEPLOYMENT COMPLETE
-- ============================================================================
-- Next steps:
-- 1. Run supabase_indexes.sql - Deploy performance indexes
-- 2. Run supabase_views.sql - Deploy denormalized views
-- 3. Run supabase_functions.sql - Deploy database functions
-- 4. Run supabase_triggers.sql - Deploy triggers
-- ============================================================================

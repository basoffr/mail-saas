-- ============================================================================
-- SUPABASE ROW LEVEL SECURITY (RLS) - MAIL DASHBOARD
-- ============================================================================
-- Project: Mail SaaS Platform
-- Status: DISABLED voor MVP (single-tenant)
-- Usage: Enable alleen bij multi-tenant vereiste
-- ============================================================================

-- ============================================================================
-- ⚠️ IMPORTANT NOTES
-- ============================================================================
-- RLS is DISABLED in MVP omdat we single-tenant zijn.
-- Deze file bevat RLS policies voor TOEKOMSTIGE multi-tenant setup.
-- 
-- Voor MVP: Skip deze file, ga direct naar data seeding.
-- Voor Multi-Tenant: Run deze file na supabase_triggers.sql
-- ============================================================================

-- ============================================================================
-- TENANT SETUP (FUTURE)
-- ============================================================================

-- Voor multi-tenant zou je een tenant kolom toevoegen aan alle tabellen:
-- ALTER TABLE leads ADD COLUMN tenant_id UUID REFERENCES tenants(id);
-- ALTER TABLE campaigns ADD COLUMN tenant_id UUID REFERENCES tenants(id);
-- etc.

-- En een tenants tabel:
-- CREATE TABLE tenants (
--     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--     name VARCHAR(255) NOT NULL,
--     subdomain VARCHAR(100) UNIQUE,
--     created_at TIMESTAMPTZ DEFAULT NOW(),
--     active BOOLEAN DEFAULT TRUE
-- );

-- ============================================================================
-- HELPER FUNCTIONS FOR RLS
-- ============================================================================

-- Function: Get current tenant ID from JWT claim
CREATE OR REPLACE FUNCTION get_current_tenant_id()
RETURNS UUID AS $$
BEGIN
    -- Extract tenant_id from JWT token
    RETURN COALESCE(
        current_setting('request.jwt.claims', true)::json->>'tenant_id',
        NULL
    )::UUID;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_current_tenant_id IS 'Extract tenant_id from JWT claims';

-- Function: Check if user is admin
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN COALESCE(
        (current_setting('request.jwt.claims', true)::json->>'role') = 'admin',
        FALSE
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION is_admin IS 'Check if current user has admin role';

-- ============================================================================
-- ENABLE RLS ON ALL TABLES (COMMENTED OUT voor MVP)
-- ============================================================================

-- Enable RLS op alle tabellen (DISABLED voor MVP)
-- ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE assets ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE import_jobs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE campaign_audience ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE message_events ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE templates ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE report_links ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE mail_accounts ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE mail_messages ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE mail_fetch_runs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE settings ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- LEADS MODULE RLS POLICIES
-- ============================================================================

-- Policy: Users can view their own tenant's leads
-- CREATE POLICY leads_tenant_isolation ON leads
--     FOR SELECT
--     USING (tenant_id = get_current_tenant_id() OR is_admin());

-- Policy: Users can insert leads in their own tenant
-- CREATE POLICY leads_tenant_insert ON leads
--     FOR INSERT
--     WITH CHECK (tenant_id = get_current_tenant_id());

-- Policy: Users can update their own tenant's leads
-- CREATE POLICY leads_tenant_update ON leads
--     FOR UPDATE
--     USING (tenant_id = get_current_tenant_id())
--     WITH CHECK (tenant_id = get_current_tenant_id());

-- Policy: Users can delete their own tenant's leads (soft delete)
-- CREATE POLICY leads_tenant_delete ON leads
--     FOR UPDATE
--     USING (tenant_id = get_current_tenant_id())
--     WITH CHECK (tenant_id = get_current_tenant_id());

-- ============================================================================
-- CAMPAIGNS MODULE RLS POLICIES
-- ============================================================================

-- Policy: Users can view their own tenant's campaigns
-- CREATE POLICY campaigns_tenant_isolation ON campaigns
--     FOR SELECT
--     USING (tenant_id = get_current_tenant_id() OR is_admin());

-- Policy: Users can create campaigns in their own tenant
-- CREATE POLICY campaigns_tenant_insert ON campaigns
--     FOR INSERT
--     WITH CHECK (tenant_id = get_current_tenant_id());

-- Policy: Users can update their own tenant's campaigns
-- CREATE POLICY campaigns_tenant_update ON campaigns
--     FOR UPDATE
--     USING (tenant_id = get_current_tenant_id())
--     WITH CHECK (tenant_id = get_current_tenant_id());

-- Policy: Users can delete their own tenant's campaigns
-- CREATE POLICY campaigns_tenant_delete ON campaigns
--     FOR DELETE
--     USING (tenant_id = get_current_tenant_id());

-- ============================================================================
-- MESSAGES RLS POLICIES
-- ============================================================================

-- Policy: Users can view messages for their tenant's campaigns
-- CREATE POLICY messages_tenant_isolation ON messages
--     FOR SELECT
--     USING (
--         EXISTS (
--             SELECT 1 FROM campaigns c 
--             WHERE c.id = messages.campaign_id 
--             AND c.tenant_id = get_current_tenant_id()
--         ) OR is_admin()
--     );

-- ============================================================================
-- TEMPLATES RLS POLICIES
-- ============================================================================

-- Policy: Templates zijn global (alle tenants kunnen zien)
-- CREATE POLICY templates_public_read ON templates
--     FOR SELECT
--     USING (TRUE);

-- Policy: Alleen admins kunnen templates aanmaken/wijzigen
-- CREATE POLICY templates_admin_write ON templates
--     FOR ALL
--     USING (is_admin())
--     WITH CHECK (is_admin());

-- ============================================================================
-- REPORTS RLS POLICIES
-- ============================================================================

-- Policy: Users can view their own tenant's reports
-- CREATE POLICY reports_tenant_isolation ON reports
--     FOR SELECT
--     USING (tenant_id = get_current_tenant_id() OR is_admin());

-- Policy: Users can upload reports to their own tenant
-- CREATE POLICY reports_tenant_insert ON reports
--     FOR INSERT
--     WITH CHECK (tenant_id = get_current_tenant_id());

-- ============================================================================
-- INBOX RLS POLICIES
-- ============================================================================

-- Policy: Users can view their own tenant's mail accounts
-- CREATE POLICY mail_accounts_tenant_isolation ON mail_accounts
--     FOR SELECT
--     USING (tenant_id = get_current_tenant_id() OR is_admin());

-- Policy: Users can view messages for their tenant's accounts
-- CREATE POLICY mail_messages_tenant_isolation ON mail_messages
--     FOR SELECT
--     USING (
--         EXISTS (
--             SELECT 1 FROM mail_accounts ma 
--             WHERE ma.id = mail_messages.account_id 
--             AND ma.tenant_id = get_current_tenant_id()
--         ) OR is_admin()
--     );

-- ============================================================================
-- SETTINGS RLS POLICIES
-- ============================================================================

-- Policy: Users can view their own tenant's settings
-- CREATE POLICY settings_tenant_isolation ON settings
--     FOR SELECT
--     USING (tenant_id = get_current_tenant_id() OR is_admin());

-- Policy: Users can update their own tenant's settings
-- CREATE POLICY settings_tenant_update ON settings
--     FOR UPDATE
--     USING (tenant_id = get_current_tenant_id())
--     WITH CHECK (tenant_id = get_current_tenant_id());

-- ============================================================================
-- ADMIN BYPASS POLICIES
-- ============================================================================

-- Admins kunnen alles zien en wijzigen (voor support/debugging)
-- CREATE POLICY admin_full_access ON leads FOR ALL TO authenticated USING (is_admin());
-- CREATE POLICY admin_full_access ON campaigns FOR ALL TO authenticated USING (is_admin());
-- CREATE POLICY admin_full_access ON messages FOR ALL TO authenticated USING (is_admin());
-- CREATE POLICY admin_full_access ON reports FOR ALL TO authenticated USING (is_admin());
-- CREATE POLICY admin_full_access ON mail_accounts FOR ALL TO authenticated USING (is_admin());

-- ============================================================================
-- ANONYMOUS ACCESS POLICIES (PUBLIC ENDPOINTS)
-- ============================================================================

-- Voor unsubscribe/tracking pixels (anonymous access)
-- CREATE POLICY messages_public_tracking ON messages
--     FOR SELECT
--     USING (TRUE);  -- Allow tracking pixel hits

-- Voor open tracking endpoint
-- CREATE POLICY message_events_public_insert ON message_events
--     FOR INSERT
--     WITH CHECK (event_type IN ('opened'));  -- Allow open tracking

-- ============================================================================
-- SERVICE ROLE BYPASS
-- ============================================================================

-- Service role (backend) heeft volledige toegang (bypass RLS)
-- Dit wordt automatisch geregeld door Supabase als je service_role key gebruikt
-- Geen extra policies nodig

-- ============================================================================
-- TESTING RLS POLICIES
-- ============================================================================

-- Test RLS policies met specifieke tenant:
-- SET request.jwt.claims = '{"tenant_id": "00000000-0000-0000-0000-000000000001", "role": "user"}';
-- SELECT * FROM leads;  -- Zou alleen leads van tenant 1 moeten tonen

-- Test admin role:
-- SET request.jwt.claims = '{"tenant_id": "00000000-0000-0000-0000-000000000001", "role": "admin"}';
-- SELECT * FROM leads;  -- Zou alle leads moeten tonen

-- Reset:
-- RESET request.jwt.claims;

-- ============================================================================
-- PERFORMANCE IMPACT
-- ============================================================================

-- RLS policies hebben performance impact omdat ze extra WHERE clauses toevoegen
-- aan elke query. Voor multi-tenant setup:
-- 
-- 1. Zorg voor indexes op tenant_id kolommen:
--    CREATE INDEX idx_leads_tenant_id ON leads(tenant_id);
--    CREATE INDEX idx_campaigns_tenant_id ON campaigns(tenant_id);
--    etc.
--
-- 2. Monitor query performance na RLS enable
-- 3. Gebruik EXPLAIN ANALYZE om query plans te checken
-- 4. Overweeg materialized views voor cross-tenant analytics

-- ============================================================================
-- MIGRATION PLAN (voor bestaande MVP → Multi-Tenant)
-- ============================================================================

-- Stap 1: Add tenant_id kolommen aan alle tabellen
-- ALTER TABLE leads ADD COLUMN tenant_id UUID;
-- ALTER TABLE campaigns ADD COLUMN tenant_id UUID;
-- -- etc voor alle tabellen

-- Stap 2: Migrate bestaande data naar default tenant
-- UPDATE leads SET tenant_id = '00000000-0000-0000-0000-000000000001';
-- UPDATE campaigns SET tenant_id = '00000000-0000-0000-0000-000000000001';
-- -- etc

-- Stap 3: Add NOT NULL constraints
-- ALTER TABLE leads ALTER COLUMN tenant_id SET NOT NULL;
-- ALTER TABLE campaigns ALTER COLUMN tenant_id SET NOT NULL;
-- -- etc

-- Stap 4: Add foreign keys
-- ALTER TABLE leads ADD CONSTRAINT fk_leads_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id);
-- -- etc

-- Stap 5: Enable RLS (uncomment policies hierboven)

-- Stap 6: Test thoroughly met verschillende tenants

-- ============================================================================
-- RLS CONFIGURATION COMPLETE
-- ============================================================================
-- Status: DISABLED voor MVP (single-tenant)
-- Voor Multi-Tenant: Uncomment policies en add tenant_id kolommen
-- Performance impact: ~10-20% overhead op queries met RLS enabled
-- Security: Zeer hoog (database-level isolation)
-- ============================================================================

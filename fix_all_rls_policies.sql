-- ============================================================================
-- COMPLETE RLS FIX - Storage + Database Tables
-- ============================================================================
-- Fix ALL RLS policies to allow anon key operations
-- ============================================================================

-- ============================================================================
-- PART 1: DISABLE RLS on all tables temporarily
-- ============================================================================

ALTER TABLE public.leads DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.reports DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.report_links DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.assets DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.campaigns DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.campaign_audience DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.templates DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.mail_messages DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.mail_accounts DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.bounces DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.unsubscribes DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.settings DISABLE ROW LEVEL SECURITY;

-- ============================================================================
-- PART 2: Storage Policies - Make fully permissive
-- ============================================================================

-- Drop all existing storage policies
DROP POLICY IF EXISTS "Authenticated users can upload reports" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated users can read reports" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated users can update reports" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated users can delete reports" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated users can upload assets" ON storage.objects;
DROP POLICY IF EXISTS "Public can read assets" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated users can update assets" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated users can delete assets" ON storage.objects;
DROP POLICY IF EXISTS "Allow all uploads to reports" ON storage.objects;
DROP POLICY IF EXISTS "Allow all reads from reports" ON storage.objects;
DROP POLICY IF EXISTS "Allow all updates to reports" ON storage.objects;
DROP POLICY IF EXISTS "Allow all deletes from reports" ON storage.objects;
DROP POLICY IF EXISTS "Allow all uploads to assets" ON storage.objects;
DROP POLICY IF EXISTS "Allow all reads from assets" ON storage.objects;
DROP POLICY IF EXISTS "Allow all updates to assets" ON storage.objects;
DROP POLICY IF EXISTS "Allow all deletes from assets" ON storage.objects;

-- Create fully permissive storage policies
CREATE POLICY "Allow all operations on reports bucket"
ON storage.objects FOR ALL
USING (bucket_id = 'reports');

CREATE POLICY "Allow all operations on assets bucket"
ON storage.objects FOR ALL
USING (bucket_id = 'assets');

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Check table RLS status
SELECT 
    schemaname,
    tablename,
    rowsecurity
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;

-- Check storage policies
SELECT 
    policyname,
    permissive,
    cmd
FROM pg_policies
WHERE tablename = 'objects'
ORDER BY policyname;

-- ============================================================================
-- DONE! All RLS restrictions removed for import
-- IMPORTANT: Re-enable RLS after import is complete!
-- ============================================================================

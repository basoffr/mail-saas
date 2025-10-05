-- ============================================================================
-- SAFE RLS FIX - Only existing tables
-- ============================================================================

-- Disable RLS on existing import tables
ALTER TABLE IF EXISTS public.leads DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.reports DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.report_links DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.assets DISABLE ROW LEVEL SECURITY;

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

-- Verification
SELECT 
    tablename,
    rowsecurity
FROM pg_tables 
WHERE schemaname = 'public'
  AND tablename IN ('leads', 'reports', 'report_links', 'assets')
ORDER BY tablename;

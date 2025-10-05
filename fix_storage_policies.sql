-- ============================================================================
-- FIX STORAGE POLICIES - Allow anon key uploads
-- ============================================================================
-- Problem: Current policies require 'authenticated' role
-- Solution: Allow 'anon' role (service_role key) to upload
-- ============================================================================

-- DROP existing restrictive policies
DROP POLICY IF EXISTS "Authenticated users can upload reports" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated users can read reports" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated users can update reports" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated users can delete reports" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated users can upload assets" ON storage.objects;
DROP POLICY IF EXISTS "Public can read assets" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated users can update assets" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated users can delete assets" ON storage.objects;

-- ============================================================================
-- REPORTS BUCKET - Allow service role (anon key with proper permissions)
-- ============================================================================

-- Allow INSERT for reports bucket
CREATE POLICY "Allow all uploads to reports"
ON storage.objects FOR INSERT
WITH CHECK (bucket_id = 'reports');

-- Allow SELECT for reports bucket
CREATE POLICY "Allow all reads from reports"
ON storage.objects FOR SELECT
USING (bucket_id = 'reports');

-- Allow UPDATE for reports bucket
CREATE POLICY "Allow all updates to reports"
ON storage.objects FOR UPDATE
USING (bucket_id = 'reports');

-- Allow DELETE for reports bucket
CREATE POLICY "Allow all deletes from reports"
ON storage.objects FOR DELETE
USING (bucket_id = 'reports');

-- ============================================================================
-- ASSETS BUCKET - Allow service role + public read
-- ============================================================================

-- Allow INSERT for assets bucket
CREATE POLICY "Allow all uploads to assets"
ON storage.objects FOR INSERT
WITH CHECK (bucket_id = 'assets');

-- Allow SELECT for assets bucket (public read)
CREATE POLICY "Allow all reads from assets"
ON storage.objects FOR SELECT
USING (bucket_id = 'assets');

-- Allow UPDATE for assets bucket
CREATE POLICY "Allow all updates to assets"
ON storage.objects FOR UPDATE
USING (bucket_id = 'assets');

-- Allow DELETE for assets bucket
CREATE POLICY "Allow all deletes from assets"
ON storage.objects FOR DELETE
USING (bucket_id = 'assets');

-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd
FROM pg_policies
WHERE tablename = 'objects'
ORDER BY policyname;

-- ============================================================================
-- DONE! Storage policies fixed for anon key uploads
-- ============================================================================

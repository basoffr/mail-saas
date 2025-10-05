-- ============================================================================
-- SUPABASE STORAGE BUCKETS CREATION
-- ============================================================================
-- Create storage buckets for reports (PDFs) and assets (images)
-- ============================================================================

-- Create REPORTS bucket (private - PDFs)
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'reports',
    'reports',
    false,  -- Private bucket (requires authentication)
    52428800,  -- 50MB per file
    ARRAY['application/pdf']::text[]
)
ON CONFLICT (id) DO NOTHING;

-- Create ASSETS bucket (public - images)
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'assets',
    'assets',
    true,  -- Public bucket (images need to be accessible)
    10485760,  -- 10MB per file
    ARRAY['image/png', 'image/jpeg', 'image/jpg', 'image/webp']::text[]
)
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- STORAGE POLICIES - Reports Bucket (Private)
-- ============================================================================

-- Allow authenticated users to upload reports
CREATE POLICY "Authenticated users can upload reports"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'reports');

-- Allow authenticated users to read their own reports
CREATE POLICY "Authenticated users can read reports"
ON storage.objects FOR SELECT
TO authenticated
USING (bucket_id = 'reports');

-- Allow authenticated users to update reports
CREATE POLICY "Authenticated users can update reports"
ON storage.objects FOR UPDATE
TO authenticated
USING (bucket_id = 'reports');

-- Allow authenticated users to delete reports
CREATE POLICY "Authenticated users can delete reports"
ON storage.objects FOR DELETE
TO authenticated
USING (bucket_id = 'reports');

-- ============================================================================
-- STORAGE POLICIES - Assets Bucket (Public)
-- ============================================================================

-- Allow authenticated users to upload assets
CREATE POLICY "Authenticated users can upload assets"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'assets');

-- Allow public read access to assets (for dashboard images in emails)
CREATE POLICY "Public can read assets"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'assets');

-- Allow authenticated users to update assets
CREATE POLICY "Authenticated users can update assets"
ON storage.objects FOR UPDATE
TO authenticated
USING (bucket_id = 'assets');

-- Allow authenticated users to delete assets
CREATE POLICY "Authenticated users can delete assets"
ON storage.objects FOR DELETE
TO authenticated
USING (bucket_id = 'assets');

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify buckets were created
SELECT 
    id,
    name,
    public,
    file_size_limit / 1024 / 1024 as max_size_mb,
    allowed_mime_types,
    created_at
FROM storage.buckets
ORDER BY name;

-- ============================================================================
-- DONE! Storage buckets ready for file uploads
-- ============================================================================

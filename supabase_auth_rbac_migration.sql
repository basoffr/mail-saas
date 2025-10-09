-- ============================================================================
-- SUPABASE AUTH + RBAC MIGRATION
-- Mail SaaS: Profiles table for role-based access control
-- ============================================================================

-- Drop existing if needed (for clean re-run)
DROP TABLE IF EXISTS profiles CASCADE;

-- Create profiles table
CREATE TABLE IF NOT EXISTS profiles (
  user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('admin', 'viewer')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create index for faster role lookups
CREATE INDEX IF NOT EXISTS idx_profiles_role ON profiles(role);
CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON profiles(user_id);

-- Enable RLS (optional but recommended)
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read their own profile
CREATE POLICY "profiles_self_select" ON profiles
  FOR SELECT
  USING (auth.uid() = user_id);

-- Policy: Only admins can update profiles (via service role key)
-- We'll use service role key for profile management via API

-- ============================================================================
-- SEED DATA (REPLACE UIDs AFTER CREATING USERS IN SUPABASE AUTH)
-- ============================================================================

-- After creating users in Supabase Auth dashboard, run this:
-- 1. Go to Supabase Dashboard → Authentication → Users
-- 2. Create 3 users with email + password
-- 3. Copy their UUIDs and replace below

/*
INSERT INTO profiles (user_id, role) VALUES
  ('<ADMIN_USER_UUID>', 'admin'),      -- Replace with actual UUID from Supabase Auth
  ('<VIEWER1_USER_UUID>', 'viewer'),   -- Replace with actual UUID from Supabase Auth
  ('<VIEWER2_USER_UUID>', 'viewer')    -- Replace with actual UUID from Supabase Auth
ON CONFLICT (user_id) DO UPDATE SET role = EXCLUDED.role, updated_at = NOW();
*/

-- ============================================================================
-- HELPER FUNCTION: Get user role (for backend queries)
-- ============================================================================

CREATE OR REPLACE FUNCTION get_user_role(p_user_id UUID)
RETURNS TEXT AS $$
BEGIN
  RETURN (SELECT role FROM profiles WHERE user_id = p_user_id);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check if profiles table exists
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name = 'profiles';

-- List all profiles (after seeding)
-- SELECT user_id, role, created_at FROM profiles ORDER BY created_at;

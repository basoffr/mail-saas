-- ============================================================================
-- FIX: Add user role to profiles table
-- ============================================================================
-- Run this in Supabase SQL Editor to add roles for your users
--
-- FIRST: Get the user UUIDs from auth.users table (see query below)
-- THEN: Replace <UUID> with actual user IDs and run the INSERT
-- ============================================================================

-- STEP 1: Find user UUIDs
-- Copy these UUIDs for the INSERT below
SELECT 
  id as user_id,
  email,
  created_at
FROM auth.users
ORDER BY created_at DESC;

-- Expected results:
-- You should see:
-- - info@boffringadigital.nl
-- - christian@punthelder.nl  
-- - victor@punthelder.nl


-- ============================================================================
-- STEP 2: Insert roles (replace UUIDs below with real ones from STEP 1)
-- ============================================================================

-- Add admin role for info@boffringadigital.nl
INSERT INTO profiles (user_id, role)
VALUES 
  ('<UUID_FOR_INFO_BOFFRINGA>', 'admin')
ON CONFLICT (user_id) 
DO UPDATE SET role = EXCLUDED.role;

-- Add viewer roles for christian@ and victor@
INSERT INTO profiles (user_id, role)
VALUES 
  ('<UUID_FOR_CHRISTIAN>', 'viewer'),
  ('<UUID_FOR_VICTOR>', 'viewer')
ON CONFLICT (user_id) 
DO UPDATE SET role = EXCLUDED.role;


-- ============================================================================
-- STEP 3: Verify roles were added
-- ============================================================================

SELECT 
  p.user_id,
  u.email,
  p.role,
  p.created_at
FROM profiles p
JOIN auth.users u ON u.id = p.user_id
ORDER BY p.created_at DESC;

-- Expected: 3 rows showing all users with their roles


-- ============================================================================
-- ALTERNATIVE: If you know the emails but not UUIDs
-- ============================================================================
-- Run this to add roles by email (more convenient)

-- Get UUID for info@boffringadigital.nl and insert as admin
DO $$
DECLARE
  v_user_id UUID;
BEGIN
  SELECT id INTO v_user_id 
  FROM auth.users 
  WHERE email = 'info@boffringadigital.nl';
  
  IF v_user_id IS NOT NULL THEN
    INSERT INTO profiles (user_id, role)
    VALUES (v_user_id, 'admin')
    ON CONFLICT (user_id) DO UPDATE SET role = EXCLUDED.role;
    
    RAISE NOTICE 'Added admin role for info@boffringadigital.nl';
  ELSE
    RAISE NOTICE 'User info@boffringadigital.nl not found in auth.users';
  END IF;
END $$;

-- Get UUIDs for christian@ and victor@ and insert as viewers
DO $$
DECLARE
  v_christian_id UUID;
  v_victor_id UUID;
BEGIN
  SELECT id INTO v_christian_id FROM auth.users WHERE email = 'christian@punthelder.nl';
  SELECT id INTO v_victor_id FROM auth.users WHERE email = 'victor@punthelder.nl';
  
  IF v_christian_id IS NOT NULL THEN
    INSERT INTO profiles (user_id, role)
    VALUES (v_christian_id, 'viewer')
    ON CONFLICT (user_id) DO UPDATE SET role = EXCLUDED.role;
    RAISE NOTICE 'Added viewer role for christian@punthelder.nl';
  END IF;
  
  IF v_victor_id IS NOT NULL THEN
    INSERT INTO profiles (user_id, role)
    VALUES (v_victor_id, 'viewer')
    ON CONFLICT (user_id) DO UPDATE SET role = EXCLUDED.role;
    RAISE NOTICE 'Added viewer role for victor@punthelder.nl';
  END IF;
END $$;


-- ============================================================================
-- FINAL VERIFICATION
-- ============================================================================

SELECT 
  u.email,
  p.role,
  CASE 
    WHEN p.role IS NULL THEN '❌ NO ROLE'
    ELSE '✅ HAS ROLE'
  END as status
FROM auth.users u
LEFT JOIN profiles p ON p.user_id = u.id
ORDER BY u.created_at DESC;

-- All users should show '✅ HAS ROLE'

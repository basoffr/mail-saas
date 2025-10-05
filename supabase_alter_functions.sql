-- ============================================================================
-- ALTER FUNCTIONS TO SET SEARCH_PATH
-- ============================================================================
-- Use ALTER instead of DROP/CREATE to set search_path on existing functions
-- ============================================================================

-- Method: Use ALTER FUNCTION to set search_path on existing functions
ALTER FUNCTION public.calculate_campaign_eta(VARCHAR) 
    SET search_path = public, pg_temp;

ALTER FUNCTION public.get_next_send_slot(VARCHAR) 
    SET search_path = public, pg_temp;

ALTER FUNCTION public.link_inbox_message(VARCHAR, VARCHAR) 
    SET search_path = public, pg_temp;

ALTER FUNCTION public.get_campaign_stats(VARCHAR) 
    SET search_path = public, pg_temp;

ALTER FUNCTION public.get_domain_stats(VARCHAR) 
    SET search_path = public, pg_temp;

-- ============================================================================
-- DONE! All 5 function warnings should now be resolved.
-- ============================================================================

-- =============================================================
-- Migration V4: JWT custom claims — embed roles in the token
-- =============================================================
-- Why put roles in the JWT?
--   Your services can authorise requests without hitting the DB
--   on every call.  The token is self-contained: API gateway,
--   edge functions, and microservices all read
--   request.auth.app_metadata.roles[] with zero DB queries.
--
-- How Supabase custom claims work:
--   Supabase Auth supports a "custom access token hook" (Auth
--   Hooks, available in Supabase ≥ 2024-02).  When enabled in
--   the dashboard, Supabase calls this function before signing
--   the JWT and merges whatever you return into the token.
--
--   Dashboard path:
--     Authentication → Hooks → Custom Access Token Hook
--     → set to: public.custom_access_token_hook
--
-- Token path: event.claims.app_metadata (shows up as
--   request.auth.app_metadata in PostgREST / Storage policies).
-- =============================================================

CREATE OR REPLACE FUNCTION public.custom_access_token_hook(event JSONB)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
STABLE       -- tells Postgres the function won't modify the DB
             -- so it can be called in read-only transactions
SET search_path = public
AS $$
DECLARE
    claims      JSONB;
    user_roles  TEXT[];
BEGIN
    -- Collect all roles for this user as a text array
    SELECT ARRAY_AGG(role::TEXT)
    INTO   user_roles
    FROM   public.user_roles
    WHERE  user_id = (event->>'user_id')::UUID;

    -- Start with whatever claims Supabase already built
    claims := event->'claims';

    -- Ensure app_metadata is a JSON object before nested jsonb_set
    IF claims->'app_metadata' IS NULL OR jsonb_typeof(claims->'app_metadata') <> 'object' THEN
        claims := jsonb_set(claims, '{app_metadata}', '{}'::jsonb);
    END IF;

    -- Merge our roles array into app_metadata
    -- COALESCE handles the case where the user somehow has no roles
    claims := jsonb_set(
        claims,
        '{app_metadata, roles}',
        TO_JSONB(COALESCE(user_roles, ARRAY['customer']::TEXT[]))
    );

    -- Return the mutated event — Supabase signs THIS as the JWT
    RETURN jsonb_set(event, '{claims}', claims);
END;
$$;

-- Grant execute to supabase_auth_admin so the hook can fire.
-- You must also enable the hook in the Supabase dashboard.
GRANT EXECUTE
    ON FUNCTION public.custom_access_token_hook
    TO supabase_auth_admin;

-- Prevent anon / authenticated users from calling it directly
REVOKE EXECUTE
    ON FUNCTION public.custom_access_token_hook
    FROM PUBLIC, authenticated, anon;


-- =============================================================
-- Helper: check_role() — use inside RLS policies across tables
-- =============================================================
-- Instead of repeating the EXISTS(...) sub-query everywhere,
-- wrap it in a STABLE function.  Postgres will inline/cache it
-- per query, so performance is the same.
--
-- Usage in any RLS policy:
--   USING ( public.check_role('admin') )
--   USING ( public.check_role('organizer') OR public.check_role('admin') )
-- =============================================================

CREATE OR REPLACE FUNCTION public.check_role(required_role public.app_role)
RETURNS BOOLEAN
LANGUAGE sql
SECURITY DEFINER
STABLE
SET search_path = public
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM   public.user_roles
        WHERE  user_id = auth.uid()
          AND  role    = required_role
    );
$$;

GRANT EXECUTE ON FUNCTION public.check_role TO authenticated;

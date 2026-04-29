-- =============================================================
-- Migration V3: auto-assign 'customer' role on signup
-- =============================================================
-- Problem: when Supabase creates a new user in auth.users, your
-- public.user_roles table knows nothing yet.
--
-- Solution: a TRIGGER on auth.users that fires AFTER INSERT and
-- inserts a 'customer' row automatically.
--
-- Why a DB trigger instead of application code?
--   • Atomic: role is created in the same transaction as the
--     user record.  No race-condition window where the user
--     exists but has no role.
--   • Resilient: works regardless of which client/service
--     created the user (OAuth, magic link, password, admin API).
--   • Auth service boundary: your auth service doesn't need an
--     extra API call after signup — the DB handles it.
-- =============================================================

CREATE OR REPLACE FUNCTION public.handle_new_user_default_role()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER  -- runs with the privileges of the function OWNER,
                  -- not the caller.  Required because the trigger
                  -- fires in the auth schema context.
SET search_path = public  -- prevent search_path hijacking attacks
AS $$
BEGIN
    INSERT INTO public.user_roles (user_id, role)
    VALUES (NEW.id, 'customer')
    ON CONFLICT (user_id, role) DO NOTHING;
    -- ON CONFLICT guard: safe to replay (idempotent).
    -- Useful if you ever replay events from your user service.

    RETURN NEW;
END;
$$;

-- Attach the trigger to auth.users
CREATE TRIGGER trg_new_user_default_role
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user_default_role();


-- =============================================================
-- Migration V3b: helper function to grant a role
-- =============================================================
-- Your backend (service_role key, bypasses RLS) can call this
-- function to elevate a user.  Having the logic in a function
-- means you can add audit logging here later in one place.
-- =============================================================

CREATE OR REPLACE FUNCTION public.grant_role(
    target_user_id UUID,
    target_role     public.app_role
)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.user_roles (user_id, role)
    VALUES (target_user_id, target_role)
    ON CONFLICT (user_id, role) DO NOTHING;
END;
$$;

-- Revoke public execute — only your backend (service_role) or
-- explicit GRANTs should call this.
REVOKE EXECUTE ON FUNCTION public.grant_role FROM PUBLIC;

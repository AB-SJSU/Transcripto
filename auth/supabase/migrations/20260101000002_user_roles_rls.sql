-- =============================================================
-- Migration V2: user_roles table + RLS
-- =============================================================
-- What this table does:
--   Maps auth.users (Supabase-managed) → one or more app roles.
--   A user can hold multiple roles simultaneously (e.g., an
--   organizer is also a customer at base level).
--
-- Why we DON'T put this in auth.users:
--   Supabase owns the auth schema.  You must never alter its
--   tables directly.  public.user_roles is your extension point.
--
-- Why NOT a single role column?
--   A junction table lets you add/remove roles independently,
--   audit when each was granted, and query "all admins" easily.
-- =============================================================

CREATE TABLE public.user_roles (
    id          BIGINT        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    -- References the Supabase-managed auth.users table.
    -- ON DELETE CASCADE: if the auth record is deleted,
    -- all role rows for that user are removed automatically.
    user_id     UUID          NOT NULL
                    REFERENCES auth.users (id) ON DELETE CASCADE,

    role        public.app_role NOT NULL,

    granted_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    -- A user should never hold the same role twice.
    CONSTRAINT uq_user_role UNIQUE (user_id, role)
);

-- Index for the most common lookup: "what roles does user X have?"
CREATE INDEX idx_user_roles_user_id ON public.user_roles (user_id);


-- =============================================================
-- ROW LEVEL SECURITY
-- =============================================================
-- RLS means every query is filtered through policies.
-- Without policies, enabling RLS makes the table completely
-- invisible — even to the authenticated service role unless
-- you bypass with the service_role key.
--
-- Key principle: Supabase's `anon` role = unauthenticated.
--               `authenticated` role = logged-in user (JWT present).
--               `service_role` = your backend / migration runner
--               (bypasses RLS entirely).
-- =============================================================

ALTER TABLE public.user_roles ENABLE ROW LEVEL SECURITY;

-- ─── Policy 1: users can read their OWN roles ────────────────
-- auth.uid() is a Supabase helper that returns the UUID from
-- the caller's JWT.  This is safe — users cannot spoof it.
CREATE POLICY "users: read own roles"
    ON public.user_roles
    FOR SELECT
    TO authenticated
    USING ( user_id = auth.uid() );

-- ─── Policy 2: admins can read ALL roles ─────────────────────
-- We check if the calling user themselves has the admin role.
-- This is a self-referential check on the same table, which
-- Postgres handles fine (it evaluates the sub-query per row).
CREATE POLICY "admins: read all roles"
    ON public.user_roles
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1
            FROM public.user_roles AS my_roles
            WHERE my_roles.user_id = auth.uid()
              AND my_roles.role = 'admin'
        )
    );

-- ─── Policy 3: admins can INSERT / UPDATE / DELETE any role ──
-- Mutations are intentionally admin-only.
-- Normal role grants happen via service_role (your backend),
-- which bypasses RLS entirely, so end-users can never
-- self-escalate.
CREATE POLICY "admins: manage all roles"
    ON public.user_roles
    FOR ALL  -- INSERT, UPDATE, DELETE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1
            FROM public.user_roles AS my_roles
            WHERE my_roles.user_id = auth.uid()
              AND my_roles.role = 'admin'
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1
            FROM public.user_roles AS my_roles
            WHERE my_roles.user_id = auth.uid()
              AND my_roles.role = 'admin'
        )
    );

-- USING  → filter rows already in the table (SELECT / DELETE)
-- WITH CHECK → validate rows being written (INSERT / UPDATE)
-- Both must pass for a mutation to succeed.

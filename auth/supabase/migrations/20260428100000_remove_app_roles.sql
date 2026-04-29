-- Remove app-specific roles: signup trigger, DB role table, JWT custom-claims hook, and enum.
-- Apply only when no other objects depend on public.check_role or public.user_roles.

DROP TRIGGER IF EXISTS trg_new_user_default_role ON auth.users;

DROP FUNCTION IF EXISTS public.handle_new_user_default_role();

DROP FUNCTION IF EXISTS public.grant_role(uuid, public.app_role);

DROP TABLE IF EXISTS public.user_roles CASCADE;

DROP FUNCTION IF EXISTS public.check_role(public.app_role);

DROP FUNCTION IF EXISTS public.custom_access_token_hook(jsonb);

DROP TYPE IF EXISTS public.app_role CASCADE;

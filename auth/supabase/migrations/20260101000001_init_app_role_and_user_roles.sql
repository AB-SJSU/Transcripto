-- App role kinds (matches Java AppRole via DB labels)
CREATE TYPE public.app_role AS ENUM (
  'customer',
  'app_admin',
  'organization'
);

CREATE TABLE public.user_roles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  role public.app_role NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT user_roles_user_id_role_unique UNIQUE (user_id, role)
);

CREATE OR REPLACE FUNCTION public.user_roles_set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

CREATE TRIGGER user_roles_set_updated_at
  BEFORE UPDATE ON public.user_roles
  FOR EACH ROW
  EXECUTE PROCEDURE public.user_roles_set_updated_at();

CREATE INDEX user_roles_user_id_idx ON public.user_roles (user_id);

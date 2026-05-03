ALTER TABLE public.user_roles ENABLE ROW LEVEL SECURITY;

GRANT USAGE ON TYPE public.app_role TO authenticated;
GRANT SELECT ON TABLE public.user_roles TO authenticated;
GRANT ALL ON TABLE public.user_roles TO service_role;

CREATE POLICY "user_roles_select_own"
  ON public.user_roles
  FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

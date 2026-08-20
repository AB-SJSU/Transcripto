-- Dev/local seed: assign app roles to deterministic user IDs.
-- Ensure matching auth.users rows exist (same ids) if you need end-to-end login tests.
INSERT INTO public.user_roles (user_id, role)
VALUES
  ('a1111111-1111-4111-8111-111111111101'::uuid, 'customer'),
  ('a2222222-2222-4222-8222-222222222202'::uuid, 'customer'),
  ('a3333333-3333-4333-8333-333333333303'::uuid, 'organization'),
  ('a4444444-4444-4444-8444-444444444404'::uuid, 'app_admin')
ON CONFLICT (user_id, role) DO NOTHING;

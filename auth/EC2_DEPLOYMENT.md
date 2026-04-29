# EC2 Deployment With Supabase Cloud

This repository deploys the Spring Boot auth service on EC2. Supabase Auth and Postgres run separately in Supabase Cloud.

## 1. Prepare Supabase Cloud

1. Create or open your Supabase Cloud project.
2. Install and log in to the Supabase CLI on your workstation.
3. Link this repository to the cloud project, then push the checked-in migrations:

   ```bash
   supabase login
   supabase link
   supabase db push
   ```

4. In the Supabase Dashboard, enable the custom access token hook if you are using the role migrations:
   `Authentication > Hooks > Custom Access Token Hook > public.custom_access_token_hook`.
5. Collect these values from the dashboard:
   - Project URL: `https://<project-ref>.supabase.co`
   - anon or publishable key
   - service role key, server-side only
   - database password
   - connection string from `Connect`

For EC2, prefer the Supabase Session pooler connection string unless your instance has IPv6 or your Supabase project has the IPv4 add-on. Convert the Supabase Postgres URL into Spring's JDBC format:

```text
postgres://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres
```

becomes:

```text
jdbc:postgresql://aws-0-<region>.pooler.supabase.com:5432/postgres?sslmode=require
```

Then set `DATABASE_USER=postgres.<project-ref>` and `DATABASE_PASSWORD=<password>`.

## 2. Prepare EC2

Open inbound TCP `22` for SSH and `8080` for this service, or put the instance behind a load balancer / reverse proxy and only expose HTTPS publicly.

On Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y git ca-certificates curl
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu
newgrp docker
sudo apt-get install -y docker-compose-plugin
```

Clone the repository:

```bash
git clone <your-repo-url> auth
cd auth
```

Create the runtime environment:

```bash
cp .env.example .env
nano .env
```

Fill every value in `.env`. Never commit `.env`; it contains the Supabase service role key and database password.

## 3. Run The Service

Build and start the container:

```bash
docker compose up -d --build
```

Check health and logs:

```bash
docker compose ps
curl http://localhost:8080/actuator/health
docker compose logs -f auth
```

The public API is available on port `8080`:

- `POST /api/v1/auth/login`
- `GET /api/v1/me` with a Supabase bearer token
- `/internal/**` with `X-Internal-Api-Key: <AUTH_INTERNAL_API_KEY>`

## 4. Update Deployment

Pull changes and rebuild:

```bash
git pull
docker compose up -d --build
docker image prune -f
```

If a change includes new Supabase migrations, run `supabase db push` from your workstation or CI after reviewing the SQL, then redeploy the EC2 service.

## Troubleshooting

- `Set <NAME> in .env`: the compose file requires production values. Add the missing value to `.env`.
- Database connection fails: use the Session pooler on EC2 if direct database connection fails because the direct connection is IPv6 by default. Keep `?sslmode=require` on the JDBC URL.
- JWT validation fails: confirm `SUPABASE_JWT_ISSUER=https://<project-ref>.supabase.co/auth/v1`.
- Login fails with missing key: confirm `SUPABASE_ANON_KEY` is set.
- Admin user creation fails: confirm `SUPABASE_SERVICE_ROLE_KEY` is set and has not been exposed to a browser or committed.

# Transcripto web UI

Static single-page client for uploading audio and polling transcription status. Deploy these files to an **S3 bucket configured for static website hosting** (or any static host).

## Configure the API URL

The SPA reads the API base URL from `window.__API_BASE__` in [`index.html`](index.html):

```html
<script>
  window.__API_BASE__ = "https://your-api-host.example.com";
</script>
```

- Use the origin **only** (no trailing slash): scheme + host, include port if non-default.
- Set this **before** deploying, or inject/replace it in CI when syncing files to S3.

## CORS on the API server

Browsers block cross-origin requests unless the FastAPI server allows your SPA origin.

On the API host, set in `.env`:

```bash
CORS_ALLOW_ORIGINS=https://your-static-site-origin.example.com
```

Use the exact origin where users open the SPA (scheme + host + port). Multiple origins are comma-separated with no spaces after commas unless each origin is trimmed by you.

Leave `CORS_ALLOW_ORIGINS` empty until you know the bucket URL; with no origins configured, CORS middleware is not registered (browser requests from the SPA will fail until you set this).

## Flow

1. `POST /upload` with `user_id` (derived from the email field), `filename`, and `content_type`.
2. `PUT` the file bytes to the presigned `upload_url` with the same `Content-Type`.
3. `POST /upload/confirm/{job_id}` with `user_id` and `s3_key` as query parameters.
4. Poll `GET /status/{job_id}` until status is `SUCCESS` or `FAILED`.

See [`../transcripto-api/docs/API_CONTRACT.md`](../transcripto-api/docs/API_CONTRACT.md) for details.

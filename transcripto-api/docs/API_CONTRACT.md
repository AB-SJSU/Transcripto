# Transcripto API Contract
Version: 1.0.0  
Base URL: https://<ec2-ip-or-alb-dns>

---

## Authentication
Currently open for academic demo. In production, all endpoints would require
a Bearer token from Amazon Cognito.

---

## Endpoints

### POST /upload
Creates a new transcription job and returns a presigned S3 URL for direct audio upload.

**Request body:**
| Field | Type | Required | Description |
|---|---|---|---|
| user_id | string | yes | Identifier for the requesting user |
| filename | string | yes | Original audio filename (e.g. lecture.mp3) |
| content_type | string | yes | MIME type (e.g. audio/mpeg, audio/wav) |

**Example request:**
```
POST /upload
Content-Type: application/json

{
  "user_id": "user-abc-123",
  "filename": "lecture.mp3",
  "content_type": "audio/mpeg"
}
```

**Example response (200 OK):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "upload_url": "https://transcripto-audio-input.s3.amazonaws.com/audio/...?X-Amz-Signature=...",
  "s3_key": "audio/user-abc-123/550e8400.../lecture.mp3",
  "expires_in": 3600
}
```

**After receiving this response:**
The client uploads the audio file directly to `upload_url` using HTTP PUT.
The API server never receives audio bytes — only metadata.

---

### POST /upload/confirm/{job_id}
Notifies the API that the S3 upload is complete, triggering the worker via SQS.
This endpoint is idempotent — safe to call multiple times.

**Path parameter:** `job_id` — the UUID returned by POST /upload

**Query parameters:**
| Param | Type | Required | Description |
|---|---|---|---|
| user_id | string | yes | Must match the user_id from POST /upload |
| s3_key | string | yes | The s3_key returned by POST /upload |

**Example request:**
```
POST /upload/confirm/550e8400-e29b-41d4-a716-446655440000
     ?user_id=user-abc-123
     &s3_key=audio/user-abc-123/550e8400.../lecture.mp3
```

**Example response — first call (200 OK):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "queued": true,
  "sqs_message_id": "abc123def456"
}
```

**Example response — duplicate call (200 OK, not re-queued):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "queued": false,
  "reason": "Job already in status PROCESSING — not re-queued"
}
```

---

### GET /status/{job_id}
Returns the current state of a transcription job.
The frontend polls this endpoint every 5 seconds until status is SUCCESS or FAILED.

**Path parameter:** `job_id` — the UUID returned by POST /upload

**Example response (200 OK):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-abc-123",
  "status": "SUCCESS",
  "created_at": "2026-03-31T10:00:00+00:00",
  "updated_at": "2026-03-31T10:02:14+00:00",
  "input_s3_path": "s3://transcripto-audio-input/audio/user-abc-123/.../lecture.mp3",
  "output_s3_path": "s3://transcripto-transcripts/transcripts/user-abc-123/.../lecture.txt",
  "transcript_url": "https://d1234abcd.cloudfront.net/transcripts/user-abc-123/.../lecture.txt",
  "error_message": null,
  "retry_count": 0
}
```

**Status values:**
| Status | Meaning | output_s3_path | error_message |
|---|---|---|---|
| PENDING | Job created, not yet picked up by worker | null | null |
| PROCESSING | Worker is running Whisper inference | null | null |
| SUCCESS | Transcript ready | populated | null |
| FAILED | Inference failed after retries | null | populated |

**Error response (404):**
```json
{
  "detail": "Job 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

---

### GET /health
Health check — used by the load balancer to verify the API is alive.

**Example response (200 OK):**
```json
{
  "status": "ok"
}
```

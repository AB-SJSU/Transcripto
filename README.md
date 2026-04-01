# Transcripto

Async audio transcription platform built on AWS — CMPE 281 course project.

## Overview

Transcripto is a cloud-native backend that accepts audio file uploads and returns transcriptions asynchronously. The API layer handles job creation and queuing; a separate worker fleet runs Whisper inference.

**Flow:**

1. Client calls `POST /upload` → API creates a job in DynamoDB and returns a presigned S3 URL
2. Client uploads audio directly to S3 (the API server never receives the audio bytes)
3. Client calls `POST /upload/confirm/{job_id}` → API publishes a message to SQS
4. Worker fleet (Sai Chetan) polls SQS, runs Whisper, updates job status in DynamoDB
5. Lambda (Ankush) sends email notification on completion
6. Client polls `GET /status/{job_id}` until status is `SUCCESS` or `FAILED`

## Team

| Role | Owner |
| --- | --- |
| API & Backend Lead | Aakruti Beladiya |
| Infrastructure Lead | Sonali |
| Worker / ML Lead | Sai Chetan |
| Frontend / Notifications | Ankush |

## Project Structure

```text
transcripto-api/
├── app/
│   ├── main.py          # FastAPI entry point
│   ├── config.py        # Env vars and AWS config (pydantic-settings)
│   ├── models.py        # Pydantic request/response schemas
│   ├── routes/
│   │   ├── upload.py    # POST /upload, POST /upload/confirm/{job_id}
│   │   └── status.py    # GET /status/{job_id}
│   └── services/
│       ├── s3.py        # Presigned URL generation
│       ├── dynamodb.py  # Job record CRUD
│       └── sqs.py       # SQS message publishing
├── requirements.txt
├── Dockerfile
└── .env.example
```

## API Endpoints

### `POST /upload`

Start a transcription job. Returns a presigned S3 URL for direct upload.

**Request:**

```json
{
  "user_id": "user-abc-123",
  "filename": "lecture.mp3",
  "content_type": "audio/mpeg"
}
```

**Response:**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "upload_url": "https://s3.amazonaws.com/transcripto-audio-input/audio/...?X-Amz-Signature=...",
  "s3_key": "audio/user-abc-123/550e8400.../lecture.mp3",
  "expires_in": 3600
}
```

### `POST /upload/confirm/{job_id}`

Call after successfully uploading to S3. Triggers the SQS message for the worker.

```http
POST /upload/confirm/550e8400-e29b-41d4-a716-446655440000
     ?user_id=user-abc-123
     &s3_key=audio/user-abc-123/550e8400.../lecture.mp3
```

### `GET /status/{job_id}`

Poll for job status. Frontend polls every 5 seconds until `SUCCESS` or `FAILED`.

**Response:**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-abc-123",
  "status": "PROCESSING",
  "created_at": "2026-03-31T10:00:00+00:00",
  "updated_at": "2026-03-31T10:00:45+00:00",
  "input_s3_path": "s3://transcripto-audio-input/audio/user-abc-123/.../lecture.mp3",
  "output_s3_path": null,
  "error_message": null,
  "retry_count": 0
}
```

**Status values:**

| Status | Meaning |
| --- | --- |
| `PENDING` | Job created, waiting for worker |
| `PROCESSING` | Worker is running Whisper inference |
| `SUCCESS` | Transcript ready, `output_s3_path` is populated |
| `FAILED` | Inference failed after retries, check `error_message` |

### `GET /health`

Returns `{"status": "ok"}`.

## AWS Resources

| Resource | Purpose |
| --- | --- |
| S3 audio bucket | Raw audio uploads (input) |
| S3 transcript bucket | Generated transcripts (output) |
| SQS queue | Job queue between API and worker fleet |
| DynamoDB table | Job records and status tracking |

## Setup

**1. Clone and install dependencies:**

```bash
cd transcripto-api
python -m venv api-venv
source api-venv/bin/activate
pip install -r requirements.txt
```

**2. Configure environment:**

```bash
cp .env.example .env
# Fill in AWS credentials and resource names
```

**3. Run locally:**

```bash
uvicorn app.main:app --reload --port 8000
```

Swagger UI: `http://localhost:8000/docs`  
ReDoc: `http://localhost:8000/redoc`

## Docker

```bash
docker build -t transcripto-api .
docker run -p 8000:8000 --env-file .env transcripto-api
```

## DynamoDB Schema

Table partition key: `jobId` (String)

| Attribute | Type | Notes |
| --- | --- | --- |
| `jobId` | String | Partition key |
| `userId` | String | Uploader identifier |
| `status` | String | PENDING / PROCESSING / SUCCESS / FAILED |
| `createdAt` | String | ISO 8601 UTC timestamp |
| `updatedAt` | String | ISO 8601 UTC timestamp |
| `inputS3Path` | String | Full S3 URI of audio file |
| `outputS3Path` | String | Full S3 URI of transcript (null until SUCCESS) |
| `errorMessage` | String | Populated on FAILED |
| `retryCount` | Number | Incremented by worker on each retry |

## SQS Message Format

Published on `POST /upload/confirm`. Worker (Sai) consumes this shape:

```json
{
  "jobId": "550e8400-e29b-41d4-a716-446655440000",
  "userId": "user-abc-123",
  "s3Key": "audio/user-abc-123/550e8400.../lecture.mp3",
  "bucket": "transcripto-audio-input"
}
```


#  Transcripto ML Worker (Day 1)

This project implements a distributed ML worker for audio transcription using OpenAI Whisper on AWS.

---

##  System Overview

Pipeline:

SQS → EC2 Worker → S3 (audio) → Whisper → S3 (transcript) → DynamoDB

---

##  Day 1 Tasks

- EC2 worker setup (CPU/GPU compatible)
- Whisper model preloaded at startup (not per job)
- SQS polling loop
- Audio download from S3
- Audio validation (16kHz mono using ffmpeg)
- End-to-end transcription
- Upload transcript to S3
- Update job status in DynamoDB

---

##  Tech Stack

- Python 3.12
- OpenAI Whisper
- AWS S3
- AWS SQS
- AWS DynamoDB
- FFmpeg

---

## Setup Instructions

### 1. Connect to EC2

```bash
ssh -i "<your-key.pem>" ubuntu@<your-ec2-ip>
```
### 2. Create Project + Virtual Environment
```bash
mkdir whisper-worker
cd whisper-worker
python3 -m venv venv
source venv/bin/activate
```
### 3. Install Dependencies
```
pip install --upgrade pip
pip install -r requirements.txt
sudo apt install ffmpeg -y
```
### 4. Verify Whisper Installation
```
python verify.py
```
Expected output:

Model loaded successfully!
Device: cpu (or cuda)
### 5. Test Local Pipeline
```
wget https://github.com/openai/whisper/raw/main/tests/jfk.flac -O test.wav
python pipeline_test.py
```
### 6. Upload Test Audio to S3
```
aws s3 cp test.wav s3://transcripto-audio-bucket/audio/test.wav
```
### 7. Send SQS Job
```
{
  "jobId": "test1",
  "key": "audio/test.wav"
}
```
### 8. Run Worker
```
python worker.py
```


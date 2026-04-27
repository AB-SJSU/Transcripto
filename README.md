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


# Transcripto — ML Worker (worker-ml branch)

ML Worker pipeline for async audio transcription using OpenAI Whisper on AWS.

---

## 🚀 Overview

This branch implements the **Worker/ML pipeline** for Transcripto.

The worker continuously polls SQS, processes audio files from S3, runs Whisper transcription, and stores results back to S3 while updating DynamoDB.

---

## 🧠 Architecture

```
SQS → EC2 Worker → S3 (audio) → Whisper → S3 (transcripts)
                         ↓
                     DynamoDB
                         ↓
                 Notification SQS
```

---

## ⚙️ Tech Stack

* Python 3.12
* OpenAI Whisper (base model)
* PyTorch
* AWS:

  * EC2 (worker)
  * SQS (job queue + notification queue)
  * S3 (audio + transcript buckets)
  * DynamoDB (job tracking)

---

## 📁 Project Structure

```
transcripto-worker/
├── worker.py            # Main worker loop (SQS polling + processing)
├── chunking.py          # Audio chunking for long files
├── pipeline_test.py     # End-to-end test script
├── verify.py            # Whisper model verification
├── requirements.txt     # Python dependencies
└── .gitignore
```

---

## 🔁 Worker Flow

1. Poll SQS (long polling)
2. Parse message:

   ```json
   {
     "jobId": "...",
     "userId": "...",
     "s3Key": "...",
     "bucket": "..."
   }
   ```
3. Update DynamoDB → `PROCESSING`
4. Download audio from S3
5. Preprocess:

   * Validate format
   * Normalize to 16kHz mono
6. If long audio → chunk into segments
7. Run Whisper inference
8. Merge transcription
9. Upload transcript to S3:

   ```
   s3://transcripto-transcript-bucket/{userId}/{jobId}.txt
   ```
10. Update DynamoDB → `SUCCESS`
11. Send notification to SQS
12. Delete original SQS message

---

## 🗄 DynamoDB Schema

| Attribute    | Type   | Notes                                   |
| ------------ | ------ | --------------------------------------- |
| jobId        | String | Partition key                           |
| userId       | String | User identifier                         |
| status       | String | PENDING / PROCESSING / SUCCESS / FAILED |
| createdAt    | String | ISO 8601                                |
| updatedAt    | String | ISO 8601                                |
| inputS3Path  | String | Input audio path                        |
| outputS3Path | String | Output transcript path                  |
| errorMessage | String | Error details                           |
| retryCount   | Number | Retry attempts                          |

---

## 📥 Setup (EC2)

### 1. SSH into instance

```bash
ssh -i "cmpe281.pem" ubuntu@<EC2-IP>
```

---

### 2. Create project + venv

```bash
mkdir -p ~/Transcripto/transcripto-worker
cd ~/Transcripto/transcripto-worker

python3 -m venv venv
source venv/bin/activate
```

---

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install torch openai-whisper boto3
sudo apt update
sudo apt install ffmpeg -y
```

---

### 4. Verify installation

```bash
python -c "import torch; print(torch.__version__)"
```

---

## ✅ Verify Whisper

Create `verify.py`:

```python
import whisper

print("Loading model...")
model = whisper.load_model("base")
print("Model loaded successfully!")
print("Device:", model.device)
```

Run:

```bash
python verify.py
```

---

## 🎧 Test Pipeline

```bash
wget https://github.com/openai/whisper/raw/main/tests/jfk.flac -O test.wav
python pipeline_test.py
```

---

## 🔄 Running Worker

```bash
python worker.py
```

Expected output:

```
Loading Whisper model...
Model loaded!
Polling SQS...

Processing job: <jobId>
Transcription...
Job completed
```

---

## 📤 SQS Test Message

```bash
aws sqs send-message \
  --queue-url <JOB_QUEUE_URL> \
  --message-body '{
    "jobId": "test-1",
    "userId": "user1",
    "s3Key": "audio/test/audio.wav",
    "bucket": "transcripto-audio-bucket"
  }'
```

---

## 📊 Batch Testing

```bash
for i in {1..5}; do
  aws sqs send-message \
    --queue-url <JOB_QUEUE_URL> \
    --message-body "{
      \"jobId\": \"batch-$i\",
      \"userId\": \"user1\",
      \"s3Key\": \"audio/test/audio.wav\",
      \"bucket\": \"transcripto-audio-bucket\"
    }"
done
```

---

## 📩 Notification Queue

Worker sends:

```json
{
  "jobId": "...",
  "status": "SUCCESS",
  "transcriptUrl": "s3://..."
}
```

---

## ⚠️ Known Issues / Fixes

* `FP16 not supported on CPU` → expected
* Ensure correct S3 key or you'll get `404 HeadObject`
* DynamoDB item must exist before processing
* Worker runs indefinitely (expected behavior)

---

## 📈 Current Status

* ✅ EC2 worker setup
* ✅ Whisper preloaded (not per job)
* ✅ SQS polling (long polling)
* ✅ S3 input/output integration
* ✅ DynamoDB status updates
* ✅ Notification queue integration
* ✅ End-to-end pipeline working

---

## 🔜 Next Steps

* Batch performance testing
* Word Error Rate (WER) evaluation
* Docker containerization
* ECS deployment
* Auto-scaling workers

---

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


ML Worker Lead — Transcripto

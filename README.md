# Transcripto
# 🎙️ Transcripto ML Worker (Day 1)

This project implements a distributed ML worker for audio transcription using OpenAI Whisper on AWS.

---

## 🚀 System Overview

Pipeline:

SQS → EC2 Worker → S3 (audio) → Whisper → S3 (transcript) → DynamoDB

---

## ✅ Day 1 Features

- EC2 worker setup (CPU/GPU compatible)
- Whisper model preloaded at startup (not per job)
- SQS polling loop
- Audio download from S3
- Audio validation (16kHz mono using ffmpeg)
- End-to-end transcription
- Upload transcript to S3
- Update job status in DynamoDB

---

## 🧠 Tech Stack

- Python 3.12
- OpenAI Whisper
- AWS S3
- AWS SQS
- AWS DynamoDB
- FFmpeg

---

## ⚙️ Setup Instructions

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

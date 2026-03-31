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

# Transcripto Infrastructure Setup Guide (AWS Console + AMI Baking)

## Overview

This document describes the AWS infrastructure we provisioned for the Transcripto project (audio upload → async transcription → transcript delivery → notifications), and how we validated it. It also explains why we used **AMI baking** for the worker fleet and how we configured **Auto Scaling** using **SQS metrics**.

**Region:** `REGION`
**Account:** `ACCOUNT_ID`

---

## Architecture Summary

**Core idea:** Decouple upload from transcription using an asynchronous queue so the system can scale and handle spikes.

**Flow:**

1. Client uploads audio to **S3 audio bucket** (via presigned URL from API).
2. API creates a job record in **DynamoDB** and sends a job message to **SQS job queue**.
3. Worker fleet (EC2 instances) polls SQS, downloads audio from S3, runs Whisper transcription, uploads transcript to **S3 transcript bucket**, updates DynamoDB status, and publishes completion to **SQS notify queue**.
4. Notification service (Lambda/SES) can send user email when complete (integration done by notifications owner).
5. (Optional) Transcripts can be served via **CloudFront** for faster delivery.

---

## Resources Created

### Storage

* **S3 Audio Bucket:** `transcripto-audio-bucket`
* **S3 Transcript Bucket:** `transcripto-transcript-bucket`

### Messaging

* **SQS Job Queue:** `transcripto-job-queue`
* **SQS Dead Letter Queue (DLQ):** `transcripto-job-dlq`
* **SQS Notify Queue:** `transcripto-notify-queue`

### Metadata / State

* **DynamoDB Table:** `TranscriptionJobs` (Partition key: `jobId`)

### Compute

* **EC2 Instance (API):** `transcripto-api`
* **EC2 Instance (Worker Golden Instance):** `transcripto-worker`
* **AMI (Worker Image):** `transcripto-worker-ami-v1` (`ami-0accd42eb83b08f5a`)
* **Launch Template:** `transcripto-worker-lt` (`lt-05842ef26342fbcb7`)
* **Auto Scaling Group:** `transcripto-worker-asg`

### Monitoring / Logging

* **CloudWatch Log Groups:**

  * `/transcripto/api`
  * `/transcripto/worker`
  * `/transcripto/notify`
* **CloudWatch Alarms (examples):**

  * `ALARM-JobQueueDepth-High`
  * `ALARM-OldestMessageAge-High`
  * `ALARM-DLQ-HasMessages`
  * `ALARM-WorkerCPU-High`

### IAM

* **Worker Instance Profile / Role:** `TranscriptoWorkerTaskRole`
* **API Instance Profile / Role:** `TranscriptoApiEC2Role`
* **Notification Role:** `TranscriptoNotifyLambdaRole`

---

## Step-by-Step: AWS Console Setup

## 1) Create S3 Buckets (Audio + Transcripts)

### 1.1 Create `transcripto-audio-bucket`

1. AWS Console → **S3** → **Create bucket**
2. Bucket name: `transcripto-audio-bucket`
3. Region: `REGION`
4. **Block Public Access**: keep **ON** (all boxes checked)
5. **Default encryption**: enable **SSE-S3 (AES-256)**
6. Create bucket

### 1.2 Create `transcripto-transcript-bucket`

Repeat steps above with bucket name: `transcripto-transcript-bucket`

### 1.3 Confirm encryption + public access block

S3 → bucket → **Properties**

* Default encryption = Enabled (AES256)
  S3 → bucket → **Permissions**
* Block public access = Enabled (all true)

### 1.4 Lifecycle rules (cost control)

We configured lifecycle policies to prevent storage growth.

**Audio bucket lifecycle (expire after 30 days):**

1. S3 → `transcripto-audio-bucket` → **Management**
2. **Lifecycle rules** → **Create lifecycle rule**
3. Name: `expire-audio-after-30-days`
4. Apply to all objects
5. Action: **Expire current versions** after **30 days**
6. Save

**Transcript bucket lifecycle (transition + expire):**

1. S3 → `transcripto-transcript-bucket` → **Management**
2. Create lifecycle rule: `expire-transcripts-after-30-days` (name kept)
3. Transition to **STANDARD_IA** after **30 days**
4. Expire after **60 days**
5. Save

---

## 2) Create DynamoDB Table for Job Tracking

1. AWS Console → **DynamoDB** → **Tables** → **Create table**
2. Table name: `TranscriptionJobs`
3. Partition key: `jobId` (String)
4. Capacity: **On-demand**
5. Create table

**Why DynamoDB?**

* Low operational overhead (no DB server maintenance)
* Low-latency reads/writes for job status tracking
* Fits simple job state machine: PENDING → PROCESSING → SUCCESS/FAILED

---

## 3) Create SQS Queues (Job Queue + DLQ + Notify Queue)

### 3.1 Create the DLQ first

1. AWS Console → **SQS** → **Create queue**
2. Type: **Standard**
3. Name: `transcripto-job-dlq`
4. Create

### 3.2 Create job queue with redrive policy

1. SQS → **Create queue**
2. Type: **Standard**
3. Name: `transcripto-job-queue`
4. **Visibility timeout**: set ~ **600 seconds (10 minutes)** (recommended for longer jobs)
5. Enable DLQ (dead-letter queue):

   * choose `transcripto-job-dlq`
   * set **maxReceiveCount = 3**
6. Create

### 3.3 Create notify queue

1. SQS → Create queue
2. Name: `transcripto-notify-queue`
3. Create

**Why SQS + DLQ?**

* SQS buffers spikes and decouples components (upload vs processing)
* DLQ captures repeated failures (corrupt audio, unsupported formats)
* Enables autoscaling based on queue metrics

---

## 4) Create IAM Roles (Least Privilege)

### 4.1 Worker Role: `TranscriptoWorkerTaskRole`

**Purpose:** allow worker to read jobs, fetch audio, write transcripts, update job status, send notify message.

Permissions typically include:

* SQS: Receive/Delete/ChangeVisibility on job queue, SendMessage on notify queue
* S3: GetObject on audio bucket; PutObject on transcript bucket
* DynamoDB: GetItem/UpdateItem (and optional DescribeTable)
* CloudWatch Logs (optional)

Attach role as **EC2 instance profile**.

### 4.2 API Role: `TranscriptoApiEC2Role`

**Purpose:** allow API to create DynamoDB job record, generate presigned URLs, send job message to SQS.

Permissions typically include:

* DynamoDB PutItem/GetItem/UpdateItem
* SQS SendMessage to job queue
* S3 PutObject permissions needed for presigned URL generation

### 4.3 Notification Role: `TranscriptoNotifyLambdaRole`

**Purpose:** Lambda reads notify queue and sends email using SES/SNS.

---

## 5) Create EC2 Instances (API + Worker)

### 5.1 API instance: `transcripto-api`

1. EC2 → **Launch instance**
2. Name: `transcripto-api`
3. Instance type: `t3.micro` (free-tier friendly)
4. IAM instance profile: `TranscriptoApiEC2Role`
5. Security group:

   * SSH 22 from My IP
   * API port (e.g., 8000) from My IP (or ALB later)
6. Launch

### 5.2 Worker “Golden Instance”: `transcripto-worker`

This is a one-time instance used to install dependencies and validate the worker pipeline before baking an AMI.

1. EC2 → Launch instance
2. Name: `transcripto-worker`
3. Instance type: `t3.small`
4. IAM instance profile: `TranscriptoWorkerTaskRole`
5. Security group:

   * SSH 22 from My IP
6. Launch

---

## Why we chose AMI Baking (instead of user data or Git clone)

We chose **AMI baking** because we needed a reliable, demo-ready autoscaling worker fleet without complex bootstrapping.

### Benefits

* **Fast and deterministic boot:** new autoscaled instances start ready to work.
* **No Git authentication issues:** no need to clone private repos at boot.
* **No dependency on long user-data installs:** avoids failures from pip/ffmpeg/whisper downloads during autoscaling.
* **Stable demo behavior:** ensures every ASG instance runs the same worker version.

### Tradeoff

* When worker code changes, we create a new AMI version (v2, v3, etc.) and update the Launch Template.

---

## 6) AMI Baking: How we did it (step-by-step)

### 6.1 Prepare Python environment (venv)

On `transcripto-worker` EC2:

1. SSH into instance
2. Create venv inside worker directory:

   * install `ffmpeg`, python venv tools
   * create `venv`
3. Install dependencies into venv (Whisper, boto3, etc.)
4. Validate whisper import and pipeline test

### 6.2 Configure environment variables

Create an env file for the worker (example):

* `/etc/transcripto.env`
  Includes:
* `AWS_REGION`
* `JOB_QUEUE_URL`
* `NOTIFY_QUEUE_URL`
* `AUDIO_BUCKET`
* `TRANSCRIPT_BUCKET`
* `DDB_TABLE`

### 6.3 Configure systemd to auto-start worker on boot

Create:

* `/etc/systemd/system/transcripto-worker.service`
* Service runs `worker.py` using the venv Python and loads `/etc/transcripto.env`

Enable it:

* `systemctl enable transcripto-worker`
* Confirm it runs after reboot

### 6.4 Validate end-to-end (one job)

We tested:

* S3 audio download + ffmpeg normalization
* Whisper transcription
* transcript upload to transcript bucket
* DynamoDB status update to SUCCESS
* return to polling “No messages…”

### 6.5 Create AMI

1. EC2 → Instances → select `transcripto-worker`
2. Actions → **Image and templates → Create image**
3. Name: `transcripto-worker-ami-v1`
4. Create
5. Wait until AMI becomes **available**
6. AMI ID recorded: `ami-0accd42eb83b08f5a`

---

## 7) Launch Template + Auto Scaling Group for Workers

### 7.1 Launch Template: `transcripto-worker-lt`

1. EC2 → **Launch Templates** → Create
2. AMI: `transcripto-worker-ami-v1`
3. Instance type: `t3.small`
4. Security group: worker SG (SSH from My IP)
5. IAM instance profile: `TranscriptoWorkerTaskRole`
6. Tags:

   * Name = `transcripto-worker-asg` (propagate at launch)
   * Project = `Transcripto`
7. Create

### 7.2 Auto Scaling Group: `transcripto-worker-asg`

1. EC2 → Auto Scaling Groups → Create
2. Name: `transcripto-worker-asg`
3. Choose Launch Template: `transcripto-worker-lt`
4. VPC/Subnets: select 2+ subnets
5. Min/Desired/Max:

   * Min = 1
   * Desired = 1
   * Max = 3
6. Create

**Verification:** New ASG instance should show worker service running automatically:

* SSH → `sudo systemctl status transcripto-worker`

---

## 8) CloudWatch Logs, Metrics, Alarms, Dashboard

### 8.1 Log Groups

CloudWatch → Logs → Create log groups:

* `/transcripto/api`
* `/transcripto/worker`
* `/transcripto/notify`

### 8.2 Alarms

We created alarms for:

* **Queue depth high:** `ApproximateNumberOfMessagesVisible`
* **Oldest message age high:** `ApproximateAgeOfOldestMessage`
* **DLQ messages visible > 0**
* **Worker CPU high**

### 8.3 Autoscaling driven by SQS metrics (demo guidance)

Autoscaling triggers require backlog to build.
If workers consume too fast, backlog may never exceed thresholds. For demo, we temporarily set ASG capacity to 0, enqueue jobs, then restore ASG min/desired to allow scale-out.

---

## 9) Terraform (Infrastructure as Code)

After manual setup, we created Terraform configuration and **imported** existing resources into Terraform state. This ensures:

* configuration is documented and reproducible
* Terraform plan shows **No changes**, indicating config matches deployed infra

---

## Final Verification Checklist

* ✅ Buckets private + AES256 encryption + lifecycle policies
* ✅ SQS job queue + DLQ (maxReceiveCount=3) + notify queue
* ✅ DynamoDB job table
* ✅ Worker can complete end-to-end test
* ✅ Worker AMI created and used by Launch Template
* ✅ ASG launches instances that auto-run worker
* ✅ CloudWatch alarms and logs present
* ✅ Terraform import complete and `terraform plan` shows no changes

---
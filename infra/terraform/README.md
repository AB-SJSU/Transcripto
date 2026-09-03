# Transcripto Infrastructure (Terraform)

This folder contains Terraform configuration for the **Transcripto** AWS infrastructure for the CMPE 281 project.

✅ **Status:** The AWS resources were initially created manually and then **imported into Terraform state** by Sonali.
Running `terraform plan` in this folder should show **No changes** (infra matches the configuration).

---

## What Terraform Manages (Region: us-east-1)

### Storage

* **S3 Audio Bucket:** `transcripto-audio-bucket`

  * Default encryption: **SSE-S3 (AES256)**
  * Bucket key enabled: **true**
  * Public access blocked: **true (all options)**
  * Lifecycle: **expire objects after 30 days**
* **S3 Transcript Bucket:** `transcripto-transcript-bucket`

  * Default encryption: **SSE-S3 (AES256)**
  * Bucket key enabled: **true**
  * Public access blocked: **true (all options)**
  * Lifecycle:

    * Transition to **STANDARD_IA after 30 days**
    * Expire after **60 days**

### Metadata Store

* **DynamoDB Table:** `TranscriptionJobs`

  * Partition key: `jobId` (String)
  * Billing: **PAY_PER_REQUEST**

### Queues

* **SQS Job Queue:** `transcripto-job-queue`
* **SQS Dead Letter Queue:** `transcripto-job-dlq`
* **SQS Notify Queue:** `transcripto-notify-queue`

### Compute / Scaling

* **Worker AMI:** `transcripto-worker-ami-v1`

  * AMI ID: `ami-0accd42eb83b08f5a`
* **Launch Template:** `transcripto-worker-lt`
* **Auto Scaling Group:** `transcripto-worker-asg`

### IAM (Roles / Instance Profiles)

* `TranscriptoWorkerTaskRole` (EC2 instance profile)
* `TranscriptoApiEC2Role` (EC2 instance profile)
* `TranscriptoNotifyLambdaRole` (Lambda execution role)

### Observability

* **CloudWatch Log Groups**

  * `/transcripto/api`
  * `/transcripto/worker`
  * `/transcripto/notify`
* **CloudWatch Alarms** (examples)

  * Job queue depth high
  * Oldest message age high
  * DLQ has messages
  * Worker CPU high

---

## Who Should Run Terraform?

### Day-to-day development / demo work

Most team members **do not need to run Terraform**, because the AWS environment is already created and running.

Instead:

* Use the existing AWS resources.
* Get resource values via `terraform output` (bucket names, queue URLs, table name, etc.).

### When to run Terraform

Run Terraform only if:

* An infra change is needed (queues, alarms, policies, ASG settings, etc.)
* The environment breaks and you need a controlled rebuild
* The instructor expects Infrastructure-as-Code execution

⚠️ **Important:** Terraform state is currently local (on Sonali’s machine).
If another teammate runs Terraform without the same state, Terraform may try to create duplicates or fail with “already exists”.

If we want shared execution by multiple teammates, we should set up a **remote backend** (S3 state bucket + DynamoDB lock table).

---

## Prerequisites

### Install Terraform

Check:

* `terraform -version`

### Configure AWS CLI (correct account + region)

Check:

* `aws sts get-caller-identity`
* `aws configure get region`

Expected:

* Account: `164995165456`
* Region: `us-east-1`

---

## How to Run Terraform

From this folder (`Transcripto/infra/terraform`):

### 1) Initialize

* `terraform init`

### 2) Preview changes

* `terraform plan`

If everything is correct, you should see:

> No changes. Your infrastructure matches the configuration.

### 3) Apply changes (only if you intentionally changed infra)

* `terraform apply`

### 4) Print outputs for the team

* `terraform output`

Share outputs (queue URLs, bucket names, table name) with the team for wiring frontend/backend/worker/notifications.

---

## Do NOT Commit Terraform State

Terraform state files contain environment details and must not be committed.

This folder should have a `.gitignore` that excludes:

* `.terraform/`
* `*.tfstate`
* `*.tfstate.*`
* `*.tfvars`
* `.terraform.lock.hcl`

✅ Commit Terraform `.tf` files and `README.md`
❌ Do not commit `terraform.tfstate`

---

## Common Troubleshooting

### Terraform wants to create everything again

Most common causes:

* Wrong AWS account or region
* Missing Terraform state

Check:

* `aws sts get-caller-identity`
* `aws configure get region`

### AWS CLI permission errors

You may be logged in as an IAM user without required permissions.
Ask the infra owner (Sonali) to grant appropriate read permissions or to run Terraform.

### I ran Terraform on my machine and it shows "to add"

Do not run `apply`. Coordinate with Sonali. Without shared state, you may create duplicates.

---

## Reference: Key Resource Names

* Audio bucket: `transcripto-audio-bucket`
* Transcript bucket: `transcripto-transcript-bucket`
* DynamoDB table: `TranscriptionJobs`
* SQS job queue URL: `https://sqs.us-east-1.amazonaws.com/164995165456/transcripto-job-queue`
* SQS DLQ URL: `https://sqs.us-east-1.amazonaws.com/164995165456/transcripto-job-dlq`
* SQS notify queue URL: `https://sqs.us-east-1.amazonaws.com/164995165456/transcripto-notify-queue`
* Worker AMI ID: `ami-0accd42eb83b08f5a`
* Launch template: `transcripto-worker-lt`
* ASG: `transcripto-worker-asg`
* Log groups: `/transcripto/api`, `/transcripto/worker`, `/transcripto/notify`

---

## Owner / Maintainer

Infra owner: **Sonali**

---

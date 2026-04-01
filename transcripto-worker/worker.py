import boto3
import whisper
import json
import subprocess
import os
from datetime import datetime, timezone

# CONFIG
QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/164995165456/transcripto-job-queue"
NOTIFY_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/164995165456/transcripto-notify-queue"

DEFAULT_INPUT_BUCKET = "transcripto-audio-bucket"
OUTPUT_BUCKET = "transcripto-transcript-bucket"

TABLE_NAME = "TranscriptionJobs"

MAX_RETRIES = 3
MAX_DURATION = 300  # seconds for chunking

# AWS clients
sqs = boto3.client("sqs", region_name="us-east-1")
s3 = boto3.client("s3", region_name="us-east-1")
dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
table = dynamodb.Table(TABLE_NAME)

# Load Whisper model ONCE
print("Loading Whisper model...")
model = whisper.load_model("base")
print("Model loaded!")

# ---------- UTILS ----------
def now():
    return datetime.now(timezone.utc).isoformat()

def update_status(job_id, status, output=None, error=None):
    expr = "SET #s = :s, updatedAt = :u"
    vals = {
        ":s": status,
        ":u": now()
    }

    if output:
        expr += ", outputS3Path = :o"
        vals[":o"] = output

    if error:
        expr += ", errorMessage = :e"
        vals[":e"] = error

    table.update_item(
        Key={"jobId": job_id},
        UpdateExpression=expr,
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues=vals
    )

def increment_retry(job_id, current_retry):
    table.update_item(
        Key={"jobId": job_id},
        UpdateExpression="SET retryCount = :r, updatedAt = :u",
        ExpressionAttributeValues={
            ":r": current_retry + 1,
            ":u": now()
        }
    )

def send_notification(job_id, status, transcript_url=None):
    message = {
        "jobId": job_id,
        "status": status,
        "transcriptUrl": transcript_url
    }

    sqs.send_message(
        QueueUrl=NOTIFY_QUEUE_URL,
        MessageBody=json.dumps(message)
    )

    print("Notification sent:", message)

# ---------- AUDIO ----------
def validate_audio(input_path):
    output_path = input_path + ".wav"

    subprocess.run([
        "ffmpeg", "-y",
        "-i", input_path,
        "-ar", "16000",
        "-ac", "1",
        output_path
    ])

    return output_path

def get_duration(file_path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration", "-of",
         "default=noprint_wrappers=1:nokey=1", file_path],
        stdout=subprocess.PIPE
    )
    return float(result.stdout.decode().strip())

def split_audio(file_path):
    duration = get_duration(file_path)

    if duration <= MAX_DURATION:
        return [file_path]

    print(f"Long audio detected ({duration}s), splitting...")

    for f in os.listdir("/tmp"):
        if f.startswith("chunk_"):
            try:
                os.remove(f"/tmp/{f}")
            except:
                pass

    subprocess.run([
        "ffmpeg",
        "-i", file_path,
        "-f", "segment",
        "-segment_time", str(MAX_DURATION),
        "-c", "copy",
        "/tmp/chunk_%03d.wav"
    ])

    return sorted([
        f"/tmp/{f}" for f in os.listdir("/tmp")
        if f.startswith("chunk_")
    ])

# ---------- MAIN JOB ----------
def process_job(msg):
    body = json.loads(msg["Body"])

    if "jobId" not in body:
        print("Invalid message:", body)
        return

    job_id = body["jobId"]
    s3_key = body.get("s3Key")
    bucket = body.get("bucket", DEFAULT_INPUT_BUCKET)
    user_id = body.get("userId", "unknown-user")

    print(f"\nProcessing job: {job_id}")

    try:
        # Fetch from DB
        response = table.get_item(Key={"jobId": job_id})

        if "Item" not in response:
            print("Job not found, skipping")
            return

        item = response["Item"]

        # Prevent duplicate processing
        if item["status"] == "SUCCESS":
            print("Skipping completed job")
            return

        retry_count = item.get("retryCount", 0)

        # Update status
        update_status(job_id, "PROCESSING")

        # Download audio
        local_input = f"/tmp/{job_id}"
        s3.download_file(bucket, s3_key, local_input)

        # Normalize
        clean_audio = validate_audio(local_input)

        # Chunk if needed
        chunks = split_audio(clean_audio)

        full_text = ""

        for chunk in chunks:
            print(f"Processing chunk: {chunk}")
            result = model.transcribe(chunk)
            full_text += result["text"] + " "

        text = full_text.strip()

        print("Transcription:", text[:100], "...")

        # Save locally
        output_file = f"/tmp/{job_id}.txt"
        with open(output_file, "w") as f:
            f.write(text)

        # Upload transcript (API-compatible path)
        output_key = f"{user_id}/{job_id}.txt"
        s3.upload_file(output_file, OUTPUT_BUCKET, output_key)

        output_s3 = f"s3://{OUTPUT_BUCKET}/{output_key}"

        # Update DB
        update_status(job_id, "SUCCESS", output=output_s3)

        # Notify
        send_notification(job_id, "SUCCESS", output_s3)

        print(f"Job {job_id} completed")

    except Exception as e:
        print("Error:", e)

        try:
            if retry_count >= MAX_RETRIES:
                update_status(job_id, "FAILED", error=str(e))
            else:
                increment_retry(job_id, retry_count)
        except:
            pass

        send_notification(job_id, "FAILED", None)

# ---------- LOOP ----------
def poll_sqs():
    print("Polling SQS...")

    while True:
        response = sqs.receive_message(
            QueueUrl=QUEUE_URL,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=10
        )

        if "Messages" not in response:
            print("No messages...")
            continue

        for msg in response["Messages"]:
            process_job(msg)

            sqs.delete_message(
                QueueUrl=QUEUE_URL,
                ReceiptHandle=msg["ReceiptHandle"]
            )

# ---------- START ----------
if __name__ == "__main__":
    poll_sqs()

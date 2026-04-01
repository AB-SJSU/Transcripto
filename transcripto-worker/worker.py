import os
import boto3
import whisper
import json
import subprocess
from datetime import datetime, timezone
from dotenv import load_dotenv

# ---------- LOAD ENV ----------
load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

JOB_QUEUE_URL = os.getenv("JOB_QUEUE_URL")
NOTIFY_QUEUE_URL = os.getenv("NOTIFY_QUEUE_URL")

AUDIO_BUCKET = os.getenv("AUDIO_BUCKET")
TRANSCRIPT_BUCKET = os.getenv("TRANSCRIPT_BUCKET")

TABLE_NAME = os.getenv("DYNAMODB_TABLE")

# ---------- AWS CLIENTS ----------
sqs = boto3.client("sqs", region_name=AWS_REGION)
s3 = boto3.client("s3", region_name=AWS_REGION)
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)

table = dynamodb.Table(TABLE_NAME)

# ---------- LOAD MODEL ----------
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

# ---------- MAIN JOB ----------
def process_job(msg):
    body = json.loads(msg["Body"])

    job_id = body["jobId"]
    user_id = body["userId"]
    key = body["s3Key"]

    print(f"\nProcessing job: {job_id}")

    try:
        update_status(job_id, "PROCESSING")

        local_input = f"/tmp/{job_id}"
        s3.download_file(AUDIO_BUCKET, key, local_input)

        clean_audio = validate_audio(local_input)

        result = model.transcribe(clean_audio)
        text = result["text"]

        print("Transcription:", text[:100], "...")

        output_file = f"/tmp/{job_id}.txt"
        with open(output_file, "w") as f:
            f.write(text)

        output_key = f"{user_id}/{job_id}.txt"
        s3.upload_file(output_file, TRANSCRIPT_BUCKET, output_key)

        output_s3 = f"s3://{TRANSCRIPT_BUCKET}/{output_key}"

        update_status(job_id, "SUCCESS", output=output_s3)
        send_notification(job_id, "SUCCESS", output_s3)

        print(f"Job {job_id} completed")

    except Exception as e:
        print("Error:", e)
        update_status(job_id, "FAILED", error=str(e))
        send_notification(job_id, "FAILED")

# ---------- SQS LOOP ----------
def poll_sqs():
    print("Polling SQS...")

    while True:
        response = sqs.receive_message(
            QueueUrl=JOB_QUEUE_URL,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=10
        )

        if "Messages" not in response:
            print("No messages...")
            continue

        for msg in response["Messages"]:
            process_job(msg)

            sqs.delete_message(
                QueueUrl=JOB_QUEUE_URL,
                ReceiptHandle=msg["ReceiptHandle"]
            )

# ---------- START ----------
if __name__ == "__main__":
    poll_sqs()

import boto3
import json
import os
import time
import subprocess
import whisper
from datetime import datetime
from botocore.exceptions import ClientError

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
JOB_QUEUE_URL = os.getenv("JOB_QUEUE_URL")
NOTIFY_QUEUE_URL = os.getenv("NOTIFY_QUEUE_URL")
AUDIO_BUCKET = os.getenv("AUDIO_BUCKET")
TRANSCRIPT_BUCKET = os.getenv("TRANSCRIPT_BUCKET")
DDB_TABLE = os.getenv("DDB_TABLE")

sqs = boto3.client("sqs", region_name=AWS_REGION)
s3 = boto3.client("s3", region_name=AWS_REGION)
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(DDB_TABLE)

model = whisper.load_model("base")

def update_status(job_id, status, output=None, error=None):
    expr = "SET #s = :s, updatedAt = :u"
    names = {"#s": "status"}
    values = {":s": status, ":u": datetime.utcnow().isoformat()}

    if output:
        expr += ", outputS3Path = :o"
        values[":o"] = output
    if error:
        expr += ", errorMessage = :e"
        values[":e"] = error

    table.update_item(
        Key={"jobId": job_id},
        UpdateExpression=expr,
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values
    )

def send_notification(job_id, status, transcript_url=None):
    body = {"jobId": job_id, "status": status}
    if transcript_url:
        body["transcriptUrl"] = transcript_url

    if NOTIFY_QUEUE_URL:
        sqs.send_message(
            QueueUrl=NOTIFY_QUEUE_URL,
            MessageBody=json.dumps(body)
        )

def validate_audio(input_path, output_path):
    subprocess.run([
        "ffmpeg", "-y",
        "-i", input_path,
        "-ar", "16000",
        "-ac", "1",
        output_path
    ])

def process_job(msg):
    """
    Returns:
      True  -> job processed successfully, safe to delete SQS message
      False -> job failed, DO NOT delete message so SQS can retry -> DLQ
    """
    try:
        body = json.loads(msg["Body"])
        job_id = body["jobId"]
        user_id = body["userId"]
        s3_key = body["s3Key"]
        bucket = body.get("bucket", AUDIO_BUCKET)

        print(f"Processing job: {job_id}")

        update_status(job_id, "PROCESSING")

        local_in = f"/tmp/{job_id}"
        local_wav = f"/tmp/{job_id}.wav"
        s3.download_file(bucket, s3_key, local_in)

        validate_audio(local_in, local_wav)

        result = model.transcribe(local_wav)
        text = result.get("text", "")
        print("Transcription: ", text[:80], "...")

        output_file = f"/tmp/{job_id}.txt"
        with open(output_file, "w") as f:
            f.write(text)

        output_key = f"{user_id}/{job_id}.txt"
        s3.upload_file(output_file, TRANSCRIPT_BUCKET, output_key)

        output_s3 = f"s3://{TRANSCRIPT_BUCKET}/{output_key}"

        update_status(job_id, "SUCCESS", output=output_s3)
        send_notification(job_id, "SUCCESS", output_s3)

        print(f"Job {job_id} completed")
        return True

    except Exception as e:
        print("Error:", e)
        # Best-effort updates; even if these fail, still return False so message retries
        try:
            job_id = job_id if "job_id" in locals() else None
            if job_id:
                update_status(job_id, "FAILED", error=str(e))
                send_notification(job_id, "FAILED")
        except Exception as inner:
            print("Error while updating FAILED status/notification:", inner)

        return False

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
            ok = process_job(msg)

            # ✅ DLQ fix: delete ONLY on success.
            if ok:
                sqs.delete_message(
                    QueueUrl=JOB_QUEUE_URL,
                    ReceiptHandle=msg["ReceiptHandle"]
                )
            else:
                # Do not delete → message becomes visible again after visibility timeout
                # and will be retried until maxReceiveCount, then moved to DLQ.
                print("Job failed; leaving message in queue for retry/DLQ.")

if __name__ == "__main__":
    poll_sqs()
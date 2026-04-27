from fastapi import APIRouter, HTTPException
from app.models import UploadRequest, UploadResponse
from app.services.s3 import generate_presigned_upload_url
from app.services.dynamodb import create_job, get_job
from app.services.sqs import publish_job_message
from app.config import settings
import uuid

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def create_upload_job(request: UploadRequest):
    """
    Step 1: Client calls this to start a transcription job.
    Returns a presigned S3 URL — client uploads the audio file directly to S3.
    Step 2: After upload completes, client calls POST /upload/confirm/{job_id}
    """
    job_id = str(uuid.uuid4())
    s3_key = f"audio/{request.user_id}/{job_id}/{request.filename}"

    try:
        upload_url = generate_presigned_upload_url(s3_key, request.content_type)
        create_job(job_id, request.user_id, s3_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")

    return UploadResponse(
        job_id=job_id,
        upload_url=upload_url,
        s3_key=s3_key,
        expires_in=settings.presigned_url_expiry_seconds,
    )


@router.post("/upload/confirm/{job_id}")
async def confirm_upload(job_id: str, user_id: str, s3_key: str):
    """
    Step 2: Client calls this AFTER successfully uploading to S3.
    This triggers the SQS message so the worker picks up the job.
    Idempotent — safe to call multiple times. Only publishes to SQS if job is PENDING or FAILED.
    """
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    current_status = job.get("status")

    if current_status in ("PROCESSING", "SUCCESS"):
        return {
            "job_id": job_id,
            "queued": False,
            "reason": f"Job already in status {current_status} — not re-queued",
        }

    # PENDING or FAILED — publish to SQS
    try:
        message_id = publish_job_message(job_id, user_id, s3_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue job: {str(e)}")

    return {
        "job_id": job_id,
        "queued": True,
        "sqs_message_id": message_id,
        "previous_status": current_status,
    }

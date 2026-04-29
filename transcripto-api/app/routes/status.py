from fastapi import APIRouter, HTTPException
from app.models import StatusResponse, TranscriptResponse
from app.services.dynamodb import get_job
from app.services.s3 import generate_presigned_download_url
from app.config import settings

router = APIRouter()


@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_job_status(job_id: str):
    """
    Poll this endpoint to check transcription job status.
    Frontend polls every 5 seconds until status is SUCCESS or FAILED.
    """
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return StatusResponse(
        job_id=job["jobId"],
        user_id=job["userId"],
        status=job["status"],
        created_at=job["createdAt"],
        updated_at=job["updatedAt"],
        input_s3_path=job.get("inputS3Path"),
        output_s3_path=job.get("outputS3Path"),
        transcript_url=job.get("transcriptUrl"),
        error_message=job.get("errorMessage"),
        retry_count=int(job.get("retryCount", 0)),
    )


@router.get("/transcript/{job_id}", response_model=TranscriptResponse)
async def get_transcript(job_id: str, user_id: str):
    """
    Returns a presigned S3 download URL for a completed transcript.
    Requires user_id to match the job owner — prevents users from accessing each other's transcripts.
    URL expires after presigned_url_expiry_seconds (default 1 hour).
    """
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job["userId"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    if job["status"] != "SUCCESS":
        raise HTTPException(
            status_code=409,
            detail=f"Transcript not ready — job status is {job['status']}"
        )

    output_s3_path = job.get("outputS3Path")
    if not output_s3_path:
        raise HTTPException(status_code=409, detail="Transcript path not set")

    # outputS3Path is stored as s3://bucket/key — extract just the key
    s3_key = output_s3_path.replace(f"s3://{settings.s3_transcript_bucket}/", "")
    download_url = generate_presigned_download_url(s3_key)

    return TranscriptResponse(
        job_id=job_id,
        user_id=user_id,
        transcript_url=download_url,
        expires_in=settings.presigned_url_expiry_seconds,
    )

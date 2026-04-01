from fastapi import APIRouter, HTTPException
from app.models import StatusResponse
from app.services.dynamodb import get_job

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

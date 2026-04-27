import boto3
import json
from app.config import settings
from app.utils.retry import with_retries


def _get_client(service: str):
    kwargs = {"region_name": settings.aws_region}
    if settings.aws_access_key_id:
        kwargs["aws_access_key_id"] = settings.aws_access_key_id
        kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
    return boto3.client(service, **kwargs)


sqs_client = _get_client("sqs")


@with_retries(max_attempts=3, base_delay=1.0)
def publish_job_message(job_id: str, user_id: str, s3_key: str) -> str:
    """
    Publish a transcription job message to SQS.
    The worker fleet polls this queue and picks up the job.
    Returns the SQS MessageId for logging.
    """
    message = {
        "jobId": job_id,
        "userId": user_id,
        "s3Key": s3_key,
        "bucket": settings.s3_audio_bucket,
    }
    response = sqs_client.send_message(
        QueueUrl=settings.sqs_queue_url,
        MessageBody=json.dumps(message),
    )
    return response["MessageId"]

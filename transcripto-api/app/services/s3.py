import boto3
from app.config import settings
from app.utils.retry import with_retries


def _get_client(service: str):
    kwargs = {"region_name": settings.aws_region}
    if settings.aws_access_key_id:
        kwargs["aws_access_key_id"] = settings.aws_access_key_id
        kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
    return boto3.client(service, **kwargs)


s3_client = _get_client("s3")


@with_retries(max_attempts=3, base_delay=0.5)
def generate_presigned_upload_url(s3_key: str, content_type: str) -> str:
    """
    Generate a presigned PUT URL so the client uploads directly to S3.
    The API server never receives the audio bytes — only the metadata.
    """
    url = s3_client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": settings.s3_audio_bucket,
            "Key": s3_key,
            "ContentType": content_type,
        },
        ExpiresIn=settings.presigned_url_expiry_seconds,
    )
    return url


@with_retries(max_attempts=3, base_delay=0.5)
def generate_presigned_download_url(s3_key: str) -> str:
    url = s3_client.generate_presigned_url(
        ClientMethod="get_object",
        Params={
            "Bucket": settings.s3_transcript_bucket,
            "Key": s3_key,
        },
        ExpiresIn=settings.presigned_url_expiry_seconds,
    )
    return url

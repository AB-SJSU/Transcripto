import boto3
from app.config import settings

s3_client = boto3.client(
    "s3",
    region_name=settings.aws_region,
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
)


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

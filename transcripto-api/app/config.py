from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    aws_region: str = "us-east-1"

    # Optional — boto3 falls back to EC2 instance profile if not set
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None

    s3_audio_bucket: str
    s3_transcript_bucket: str
    sqs_queue_url: str
    dynamodb_table_name: str

    presigned_url_expiry_seconds: int = 3600

    class Config:
        env_file = ".env"


settings = Settings()

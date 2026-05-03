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

    # Comma-separated list; empty means no browser origins allowed (add your S3 website URL later).
    cors_allow_origins: str = ""

    class Config:
        env_file = ".env"

    @property
    def cors_origins_list(self) -> list[str]:
        raw = self.cors_allow_origins.strip()
        if not raw:
            return []
        return [o.strip() for o in raw.split(",") if o.strip()]


settings = Settings()

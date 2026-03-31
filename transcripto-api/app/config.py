from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    aws_region: str
    aws_access_key_id: str
    aws_secret_access_key: str

    s3_audio_bucket: str
    s3_transcript_bucket: str
    sqs_queue_url: str
    dynamodb_table_name: str

    presigned_url_expiry_seconds: int = 3600

    class Config:
        env_file = ".env"


settings = Settings()

import boto3
from datetime import datetime, timezone
from app.config import settings

dynamodb = boto3.resource(
    "dynamodb",
    region_name=settings.aws_region,
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
)
table = dynamodb.Table(settings.dynamodb_table_name)


def create_job(job_id: str, user_id: str, s3_key: str) -> dict:
    """Write a new PENDING job record to DynamoDB."""
    now = datetime.now(timezone.utc).isoformat()
    item = {
        "jobId": job_id,
        "userId": user_id,
        "status": "PENDING",
        "createdAt": now,
        "updatedAt": now,
        "inputS3Path": f"s3://{settings.s3_audio_bucket}/{s3_key}",
        "outputS3Path": None,
        "errorMessage": None,
        "retryCount": 0,
    }
    table.put_item(Item=item)
    return item


def get_job(job_id: str) -> dict | None:
    """Fetch a job record by jobId. Returns None if not found."""
    response = table.get_item(Key={"jobId": job_id})
    return response.get("Item")

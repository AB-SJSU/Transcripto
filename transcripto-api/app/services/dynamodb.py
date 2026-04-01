import boto3
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError
from app.config import settings
from app.utils.retry import with_retries

dynamodb = boto3.resource(
    "dynamodb",
    region_name=settings.aws_region,
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
)
table = dynamodb.Table(settings.dynamodb_table_name)


@with_retries(max_attempts=3, base_delay=0.5)
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


@with_retries(max_attempts=3, base_delay=0.5)
def get_job(job_id: str) -> dict | None:
    """Fetch a job record by jobId. Returns None if not found."""
    response = table.get_item(Key={"jobId": job_id})
    return response.get("Item")


@with_retries(max_attempts=3, base_delay=0.5)
def update_job_status(
    job_id: str,
    status: str,
    output_s3_path: str = None,
    error_message: str = None,
    increment_retry: bool = False,
) -> bool:
    """
    Update job status. Returns True on success, False if job not found.
    Uses a conditional write to prevent race conditions.
    """
    now = datetime.now(timezone.utc).isoformat()
    update_expr = "SET #s = :status, updatedAt = :now"
    expr_names = {"#s": "status"}
    expr_values = {":status": status, ":now": now}

    if output_s3_path:
        update_expr += ", outputS3Path = :out"
        expr_values[":out"] = output_s3_path

    if error_message:
        update_expr += ", errorMessage = :err"
        expr_values[":err"] = error_message

    if increment_retry:
        update_expr += " ADD retryCount :inc"
        expr_values[":inc"] = 1

    try:
        table.update_item(
            Key={"jobId": job_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
            ConditionExpression=Attr("jobId").exists(),
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise

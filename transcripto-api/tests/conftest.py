import os
import pytest
import boto3
from moto import mock_aws
from fastapi.testclient import TestClient

# Point boto3 at moto's fake AWS — must be set before app imports
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"

from app.main import app
from app.config import settings


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def all_mocks():
    """Single mock_aws context covering DynamoDB, SQS, and S3 together."""
    with mock_aws():
        # DynamoDB
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.create_table(
            TableName=settings.dynamodb_table_name,
            KeySchema=[{"AttributeName": "jobId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "jobId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        # SQS
        sqs = boto3.client("sqs", region_name="us-east-1")
        queue = sqs.create_queue(QueueName="transcripto-test-queue")
        os.environ["SQS_QUEUE_URL"] = queue["QueueUrl"]
        settings.sqs_queue_url = queue["QueueUrl"]  # patch so sqs.py uses moto queue URL

        # S3
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket=settings.s3_audio_bucket)

        # Patch service-level boto3 clients/resources to use moto
        import app.services.dynamodb as ddb_module
        import app.services.sqs as sqs_module
        import app.services.s3 as s3_module

        ddb_module.table = table
        sqs_module.sqs_client = sqs
        s3_module.s3_client = s3

        yield table, sqs, s3


@pytest.fixture
def mock_dynamodb(all_mocks):
    table, _, _ = all_mocks
    return table

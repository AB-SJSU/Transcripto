from tests.conftest import *


def test_create_upload_job_returns_presigned_url(client, all_mocks):
    response = client.post("/upload", json={
        "user_id": "test-user-1",
        "filename": "audio.mp3",
        "content_type": "audio/mpeg",
    })
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert "upload_url" in data
    assert data["upload_url"].startswith("https://")
    assert "expires_in" in data


def test_create_upload_job_writes_pending_to_dynamodb(client, all_mocks):
    mock_dynamodb, _, _ = all_mocks
    response = client.post("/upload", json={
        "user_id": "test-user-1",
        "filename": "audio.mp3",
        "content_type": "audio/mpeg",
    })
    job_id = response.json()["job_id"]

    item = mock_dynamodb.get_item(Key={"jobId": job_id})["Item"]
    assert item["status"] == "PENDING"
    assert item["userId"] == "test-user-1"
    assert item["retryCount"] == 0
    assert item["inputS3Path"].startswith("s3://")


def test_confirm_upload_publishes_to_sqs(client, all_mocks):
    upload_resp = client.post("/upload", json={
        "user_id": "test-user-1",
        "filename": "audio.mp3",
        "content_type": "audio/mpeg",
    })
    job_id = upload_resp.json()["job_id"]
    s3_key = upload_resp.json()["s3_key"]

    confirm_resp = client.post(
        f"/upload/confirm/{job_id}",
        params={"user_id": "test-user-1", "s3_key": s3_key},
    )
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["queued"] is True
    assert "sqs_message_id" in confirm_resp.json()


def test_confirm_upload_returns_404_for_unknown_job(client, all_mocks):
    confirm_resp = client.post(
        "/upload/confirm/nonexistent-job-id",
        params={"user_id": "test-user-1", "s3_key": "audio/test/file.mp3"},
    )
    assert confirm_resp.status_code == 404


def test_confirm_upload_idempotent_when_processing(client, all_mocks):
    """Calling confirm when job is PROCESSING must not publish a second SQS message."""
    mock_dynamodb, _, _ = all_mocks
    upload_resp = client.post("/upload", json={
        "user_id": "test-user-1",
        "filename": "audio.mp3",
        "content_type": "audio/mpeg",
    })
    job_id = upload_resp.json()["job_id"]
    s3_key = upload_resp.json()["s3_key"]

    # Simulate worker picking up the job
    mock_dynamodb.update_item(
        Key={"jobId": job_id},
        UpdateExpression="SET #s = :s",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": "PROCESSING"},
    )

    confirm_resp = client.post(
        f"/upload/confirm/{job_id}",
        params={"user_id": "test-user-1", "s3_key": s3_key},
    )
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["queued"] is False


def test_confirm_upload_idempotent_when_success(client, all_mocks):
    """Calling confirm on a SUCCESS job must not re-queue."""
    mock_dynamodb, _, _ = all_mocks
    upload_resp = client.post("/upload", json={
        "user_id": "test-user-1",
        "filename": "audio.mp3",
        "content_type": "audio/mpeg",
    })
    job_id = upload_resp.json()["job_id"]
    s3_key = upload_resp.json()["s3_key"]

    mock_dynamodb.update_item(
        Key={"jobId": job_id},
        UpdateExpression="SET #s = :s",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": "SUCCESS"},
    )

    confirm_resp = client.post(
        f"/upload/confirm/{job_id}",
        params={"user_id": "test-user-1", "s3_key": s3_key},
    )
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["queued"] is False

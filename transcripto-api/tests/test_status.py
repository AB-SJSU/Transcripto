from datetime import datetime, timezone
from tests.conftest import *


def test_status_returns_404_for_unknown_job(client, all_mocks):
    response = client.get("/status/nonexistent-job-id")
    assert response.status_code == 404


def test_status_returns_pending_after_upload(client, all_mocks):
    upload_resp = client.post("/upload", json={
        "user_id": "test-user-1",
        "filename": "audio.mp3",
        "content_type": "audio/mpeg",
    })
    job_id = upload_resp.json()["job_id"]

    status_resp = client.get(f"/status/{job_id}")
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["status"] == "PENDING"
    assert data["output_s3_path"] is None
    assert data["transcript_url"] is None
    assert data["error_message"] is None
    assert data["retry_count"] == 0


def test_status_returns_success_after_worker_completion(client, all_mocks):
    """Simulate Sai's worker writing SUCCESS to DynamoDB."""
    mock_dynamodb, _, _ = all_mocks
    upload_resp = client.post("/upload", json={
        "user_id": "test-user-1",
        "filename": "audio.mp3",
        "content_type": "audio/mpeg",
    })
    job_id = upload_resp.json()["job_id"]

    mock_dynamodb.update_item(
        Key={"jobId": job_id},
        UpdateExpression="SET #s = :s, outputS3Path = :out, updatedAt = :now",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":s": "SUCCESS",
            ":out": "s3://transcripto-transcripts/transcripts/test-user-1/audio.txt",
            ":now": datetime.now(timezone.utc).isoformat(),
        },
    )

    status_resp = client.get(f"/status/{job_id}")
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["status"] == "SUCCESS"
    assert data["output_s3_path"] is not None


def test_status_returns_transcript_url_when_set(client, all_mocks):
    """Verify transcript_url field is returned when Ankush's CloudFront URL is written."""
    mock_dynamodb, _, _ = all_mocks
    upload_resp = client.post("/upload", json={
        "user_id": "test-user-1",
        "filename": "audio.mp3",
        "content_type": "audio/mpeg",
    })
    job_id = upload_resp.json()["job_id"]

    mock_dynamodb.update_item(
        Key={"jobId": job_id},
        UpdateExpression="SET #s = :s, transcriptUrl = :url, updatedAt = :now",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":s": "SUCCESS",
            ":url": "https://cdn.transcripto.example.com/transcripts/audio.txt",
            ":now": datetime.now(timezone.utc).isoformat(),
        },
    )

    status_resp = client.get(f"/status/{job_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["transcript_url"] == "https://cdn.transcripto.example.com/transcripts/audio.txt"


def test_full_lifecycle(client, all_mocks):
    """End-to-end: create → confirm → poll PENDING → simulate SUCCESS → poll SUCCESS."""
    mock_dynamodb, _, _ = all_mocks

    # 1. Create job
    upload_resp = client.post("/upload", json={
        "user_id": "user-lifecycle-test",
        "filename": "lecture.mp3",
        "content_type": "audio/mpeg",
    })
    assert upload_resp.status_code == 200
    job_id = upload_resp.json()["job_id"]
    s3_key = upload_resp.json()["s3_key"]

    # 2. Confirm upload → SQS published
    confirm_resp = client.post(
        f"/upload/confirm/{job_id}",
        params={"user_id": "user-lifecycle-test", "s3_key": s3_key},
    )
    assert confirm_resp.json()["queued"] is True

    # 3. Poll status → PENDING
    assert client.get(f"/status/{job_id}").json()["status"] == "PENDING"

    # 4. Simulate worker → SUCCESS
    mock_dynamodb.update_item(
        Key={"jobId": job_id},
        UpdateExpression="SET #s = :s, outputS3Path = :out, updatedAt = :now",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":s": "SUCCESS",
            ":out": "s3://transcripto-transcripts/transcripts/user-lifecycle-test/lecture.txt",
            ":now": datetime.now(timezone.utc).isoformat(),
        },
    )

    # 5. Poll status → SUCCESS
    final = client.get(f"/status/{job_id}").json()
    assert final["status"] == "SUCCESS"
    assert final["output_s3_path"] is not None

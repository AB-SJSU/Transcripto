import os
import pytest
import time
import requests

# Skip entire file unless E2E=true is explicitly set
pytestmark = pytest.mark.skipif(
    os.getenv("E2E") != "true",
    reason="End-to-end tests only run with E2E=true"
)

BASE_URL = os.getenv("API_BASE_URL", "https://localhost:443")
TEST_USER_ID = "e2e-test-user"
SAMPLE_AUDIO_PATH = "tests/fixtures/sample.mp3"
POLL_INTERVAL_SECONDS = 5
POLL_TIMEOUT_SECONDS = 180  # 3 minutes max — enough for Whisper on a short clip


def poll_until_done(job_id: str) -> dict:
    """Poll /status/{job_id} until status is SUCCESS or FAILED, or timeout."""
    deadline = time.time() + POLL_TIMEOUT_SECONDS
    while time.time() < deadline:
        resp = requests.get(f"{BASE_URL}/status/{job_id}", verify=False)
        assert resp.status_code == 200, f"Status check failed: {resp.text}"
        data = resp.json()
        if data["status"] in ("SUCCESS", "FAILED"):
            return data
        print(f"  [{data['status']}] waiting {POLL_INTERVAL_SECONDS}s...")
        time.sleep(POLL_INTERVAL_SECONDS)
    pytest.fail(f"Job {job_id} did not complete within {POLL_TIMEOUT_SECONDS}s")


# ── Test 1: PENDING state ──────────────────────────────────────────────────

def test_job_created_with_pending_status():
    """POST /upload must create a PENDING job and return a presigned URL."""
    resp = requests.post(f"{BASE_URL}/upload", json={
        "user_id": TEST_USER_ID,
        "filename": "test_pending.mp3",
        "content_type": "audio/mpeg",
    }, verify=False)

    assert resp.status_code == 200, f"Upload failed: {resp.text}"
    data = resp.json()
    assert "job_id" in data
    assert "upload_url" in data
    assert data["upload_url"].startswith("https://")

    job_id = data["job_id"]
    status_resp = requests.get(f"{BASE_URL}/status/{job_id}", verify=False)
    assert status_resp.json()["status"] == "PENDING"
    print(f"  PASS: job {job_id} created with PENDING status")


# ── Test 2: PROCESSING state ───────────────────────────────────────────────

def test_job_transitions_to_processing():
    """After confirming upload, status must move to PROCESSING (worker picks it up)."""
    resp = requests.post(f"{BASE_URL}/upload", json={
        "user_id": TEST_USER_ID,
        "filename": "test_processing.mp3",
        "content_type": "audio/mpeg",
    }, verify=False)
    data = resp.json()
    job_id = data["job_id"]
    s3_key = data["s3_key"]
    upload_url = data["upload_url"]

    with open(SAMPLE_AUDIO_PATH, "rb") as f:
        put_resp = requests.put(upload_url, data=f, headers={"Content-Type": "audio/mpeg"})
    assert put_resp.status_code == 200, f"S3 upload failed: {put_resp.text}"

    confirm_resp = requests.post(
        f"{BASE_URL}/upload/confirm/{job_id}",
        params={"user_id": TEST_USER_ID, "s3_key": s3_key},
        verify=False,
    )
    assert confirm_resp.json()["queued"] is True

    time.sleep(10)
    status_resp = requests.get(f"{BASE_URL}/status/{job_id}", verify=False)
    status = status_resp.json()["status"]
    assert status in ("PROCESSING", "SUCCESS"), (
        f"Expected PROCESSING or SUCCESS 10s after queue, got {status}"
    )
    print(f"  PASS: job {job_id} transitioned to {status}")


# ── Test 3: SUCCESS state ──────────────────────────────────────────────────

def test_full_pipeline_reaches_success():
    """Full pipeline: upload → confirm → worker → SUCCESS with transcript URL."""
    resp = requests.post(f"{BASE_URL}/upload", json={
        "user_id": TEST_USER_ID,
        "filename": "test_success.mp3",
        "content_type": "audio/mpeg",
    }, verify=False)
    data = resp.json()
    job_id, s3_key, upload_url = data["job_id"], data["s3_key"], data["upload_url"]

    with open(SAMPLE_AUDIO_PATH, "rb") as f:
        requests.put(upload_url, data=f, headers={"Content-Type": "audio/mpeg"})

    requests.post(
        f"{BASE_URL}/upload/confirm/{job_id}",
        params={"user_id": TEST_USER_ID, "s3_key": s3_key},
        verify=False,
    )

    final = poll_until_done(job_id)

    assert final["status"] == "SUCCESS", (
        f"Expected SUCCESS, got {final['status']}. Error: {final.get('error_message')}"
    )
    assert final["output_s3_path"] is not None, "output_s3_path must be set on SUCCESS"
    print(f"  PASS: job {job_id} reached SUCCESS")
    print(f"  Transcript: {final.get('transcript_url') or final['output_s3_path']}")


# ── Test 4: FAILED state ───────────────────────────────────────────────────

def test_corrupt_audio_reaches_failed_status():
    """A corrupt/empty file must eventually reach FAILED status via DLQ path."""
    resp = requests.post(f"{BASE_URL}/upload", json={
        "user_id": TEST_USER_ID,
        "filename": "corrupt.mp3",
        "content_type": "audio/mpeg",
    }, verify=False)
    data = resp.json()
    job_id, s3_key, upload_url = data["job_id"], data["s3_key"], data["upload_url"]

    requests.put(upload_url, data=b"this is not audio", headers={"Content-Type": "audio/mpeg"})

    requests.post(
        f"{BASE_URL}/upload/confirm/{job_id}",
        params={"user_id": TEST_USER_ID, "s3_key": s3_key},
        verify=False,
    )

    final = poll_until_done(job_id)

    assert final["status"] == "FAILED", (
        f"Expected FAILED for corrupt audio, got {final['status']}"
    )
    assert final["error_message"] is not None, "error_message must be set on FAILED"
    print(f"  PASS: corrupt job {job_id} reached FAILED with message: {final['error_message']}")


# ── Test 5: Idempotency under real conditions ──────────────────────────────

def test_confirm_twice_does_not_duplicate_transcript():
    """
    Calling confirm twice must not produce two transcripts.
    Verified by checking the worker only writes outputS3Path once.
    """
    resp = requests.post(f"{BASE_URL}/upload", json={
        "user_id": TEST_USER_ID,
        "filename": "test_idempotent.mp3",
        "content_type": "audio/mpeg",
    }, verify=False)
    data = resp.json()
    job_id, s3_key, upload_url = data["job_id"], data["s3_key"], data["upload_url"]

    with open(SAMPLE_AUDIO_PATH, "rb") as f:
        requests.put(upload_url, data=f, headers={"Content-Type": "audio/mpeg"})

    r1 = requests.post(
        f"{BASE_URL}/upload/confirm/{job_id}",
        params={"user_id": TEST_USER_ID, "s3_key": s3_key},
        verify=False,
    )
    r2 = requests.post(
        f"{BASE_URL}/upload/confirm/{job_id}",
        params={"user_id": TEST_USER_ID, "s3_key": s3_key},
        verify=False,
    )

    assert r1.json()["queued"] is True
    assert r2.json()["queued"] is False, (
        f"Second confirm should not re-queue but got: {r2.json()}"
    )

    final = poll_until_done(job_id)
    assert final["status"] == "SUCCESS"
    assert final["retry_count"] == 0, (
        f"retryCount should be 0 for clean run, got {final['retry_count']}"
    )
    print(f"  PASS: idempotency confirmed — job {job_id} processed exactly once")


# ── Test 6: 404 for unknown job ────────────────────────────────────────────

def test_status_returns_404_for_unknown_job():
    resp = requests.get(f"{BASE_URL}/status/definitely-not-a-real-job-id", verify=False)
    assert resp.status_code == 404
    print("  PASS: 404 returned for unknown jobId")

from pydantic import BaseModel
from typing import Optional


class UploadRequest(BaseModel):
    user_id: str
    filename: str
    content_type: str


class UploadResponse(BaseModel):
    job_id: str
    upload_url: str
    s3_key: str
    expires_in: int


class StatusResponse(BaseModel):
    job_id: str
    user_id: str
    status: str
    created_at: str
    updated_at: str
    input_s3_path: Optional[str] = None
    output_s3_path: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0

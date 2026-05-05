import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthRequest(BaseModel):
    email: str
    password: str


def _auth_headers() -> dict:
    return {"X-Internal-Api-Key": settings.auth_internal_api_key}


def _proxy(method: str, path: str, body: dict) -> dict:
    url = f"{settings.auth_service_url}{path}"
    try:
        resp = httpx.request(method, url, json=body, headers=_auth_headers(), timeout=10)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Auth service unavailable: {e}")


@router.post("/login")
def login(body: AuthRequest):
    return _proxy("POST", "/internal/auth/login", {"email": body.email, "password": body.password})


@router.post("/signup")
def signup(body: AuthRequest):
    return _proxy("POST", "/internal/auth/signup", {"email": body.email, "password": body.password})

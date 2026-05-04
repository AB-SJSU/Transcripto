import httpx
from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.config import settings

router = APIRouter(tags=["auth"])

_AUTH_TIMEOUT = 30.0


@router.post("/login")
async def proxy_login(request: Request) -> Response:
    return await _forward_to_auth(request, "/api/v1/auth/login")


@router.post("/signup")
async def proxy_signup(request: Request) -> Response:
    return await _forward_to_auth(request, "/api/v1/auth/signup")


async def _forward_to_auth(request: Request, auth_path: str) -> Response:
    base = settings.auth_service_base_url.rstrip("/")
    url = f"{base}{auth_path}"
    body = await request.body()
    content_type = request.headers.get("content-type") or "application/json"
    async with httpx.AsyncClient(timeout=_AUTH_TIMEOUT) as client:
        upstream = await client.post(url, content=body, headers={"Content-Type": content_type})
    media_type = upstream.headers.get("content-type") or "application/json"
    return Response(content=upstream.content, status_code=upstream.status_code, media_type=media_type)

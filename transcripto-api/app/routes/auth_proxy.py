import logging

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from app.config import settings

router = APIRouter(tags=["auth"])
logger = logging.getLogger(__name__)

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
    try:
        async with httpx.AsyncClient(timeout=_AUTH_TIMEOUT) as client:
            upstream = await client.post(url, content=body, headers={"Content-Type": content_type})
    except httpx.RequestError as exc:
        logger.warning("Auth proxy could not reach %s: %s", url, exc)
        return JSONResponse(
            status_code=502,
            content={
                "detail": (
                    "Authentication service is unreachable from this API. "
                    "Set AUTH_SERVICE_BASE_URL on the API host to the Spring auth-api base URL "
                    "(no trailing path), ensure auth-api is running, and that security groups/firewall "
                    "allow the API to connect to that host and port."
                )
            },
        )
    media_type = upstream.headers.get("content-type") or "application/json"
    return Response(content=upstream.content, status_code=upstream.status_code, media_type=media_type)

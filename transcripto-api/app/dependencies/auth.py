import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.config import settings

security = HTTPBearer()

_jwks_cache: dict | None = None


def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        resp = httpx.get(settings.supabase_jwks_url, timeout=10)
        resp.raise_for_status()
        _jwks_cache = resp.json()
    return _jwks_cache


def _find_rsa_key(token: str, jwks: dict) -> dict | None:
    header = jwt.get_unverified_header(token)
    for key in jwks.get("keys", []):
        if key.get("kid") == header.get("kid"):
            return key
    return None


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    try:
        jwks = _get_jwks()
        rsa_key = _find_rsa_key(token, jwks)
        if not rsa_key:
            raise HTTPException(status_code=401, detail="Invalid token key")
        payload = jwt.decode(token, rsa_key, algorithms=["RS256"], options={"verify_aud": False})
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

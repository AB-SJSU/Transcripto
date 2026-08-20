import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, "auth_service_base_url", "http://auth.test")
    return TestClient(app)


def test_login_proxies_to_auth_url_status_and_body(client):
    mock_resp = MagicMock()
    mock_resp.content = json.dumps(
        {"accessToken": "tok", "tokenType": "bearer", "expiresIn": 3600}
    ).encode()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "application/json"}

    inner = MagicMock()
    inner.post = AsyncMock(return_value=mock_resp)
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=inner)
    cm.__aexit__ = AsyncMock(return_value=False)

    payload = {"email": "u@example.com", "password": "secret"}
    with patch("app.routes.auth_proxy.httpx.AsyncClient", return_value=cm):
        r = client.post("/login", json=payload)

    assert r.status_code == 200
    assert r.json()["accessToken"] == "tok"
    inner.post.assert_called_once()
    args, kwargs = inner.post.call_args
    assert args[0] == "http://auth.test/api/v1/auth/login"
    assert json.loads(kwargs["content"]) == payload
    assert kwargs["headers"]["Content-Type"] == "application/json"


def test_signup_proxies_201_and_body(client):
    mock_resp = MagicMock()
    mock_resp.content = json.dumps({"id": "uuid-1", "email": "new@example.com"}).encode()
    mock_resp.status_code = 201
    mock_resp.headers = {"content-type": "application/json"}

    inner = MagicMock()
    inner.post = AsyncMock(return_value=mock_resp)
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=inner)
    cm.__aexit__ = AsyncMock(return_value=False)

    payload = {"email": "new@example.com", "password": "pw"}
    with patch("app.routes.auth_proxy.httpx.AsyncClient", return_value=cm):
        r = client.post("/signup", json=payload)

    assert r.status_code == 201
    assert r.json() == {"id": "uuid-1", "email": "new@example.com"}
    args, kwargs = inner.post.call_args
    assert args[0] == "http://auth.test/api/v1/auth/signup"


def test_login_passes_through_upstream_error(client):
    mock_resp = MagicMock()
    mock_resp.content = json.dumps(
        {"title": "Authentication error", "detail": "Invalid email or password"}
    ).encode()
    mock_resp.status_code = 401
    mock_resp.headers = {"content-type": "application/problem+json"}

    inner = MagicMock()
    inner.post = AsyncMock(return_value=mock_resp)
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=inner)
    cm.__aexit__ = AsyncMock(return_value=False)

    with patch("app.routes.auth_proxy.httpx.AsyncClient", return_value=cm):
        r = client.post("/login", json={"email": "u@x.com", "password": "wrong"})

    assert r.status_code == 401
    body = r.json()
    assert body["detail"] == "Invalid email or password"
